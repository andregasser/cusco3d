#!/usr/bin/env python3
"""Rebuild the Cusco relief as four mutually exclusive watertight solids.

Run with .venv-model/bin/python. Old prototypes are deliberately left intact.
"""
from pathlib import Path
import gzip, json, math, zipfile, hashlib
from xml.sax.saxutils import escape
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
import trimesh
import manifold3d as md
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon
from shapely.affinity import scale, translate

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output/print_v2'
OUT.mkdir(parents=True, exist_ok=True)
SIZE, APRON, AREA, BASE = 200., 16., 20000., 4.
NX, NY = 734, 788
DX, DY = SIZE/NX, (SIZE+APRON)/NY
LAT, LON = -13.53195, -71.96746
SOUTH = LAT-10/111.32
WEST = LON-10/(111.32*math.cos(math.radians(LAT)))
DLAT = 20/111.32
DLON = 20/(111.32*math.cos(math.radians(LAT)))
LABEL = 'Cusco'
NAMES = ['01_Terrain_Sockel', '02_Strassen_Schrift', '03_Gebaeude', '04_Vegetation']
COLORS = ['#B8A17C', '#757575', '#B66548', '#637D46']
report = {'label': LABEL, 'size_xy_mm': [SIZE, SIZE+APRON], 'terrain_km':20,
          'base_mm': BASE, 'layer_height_check_mm': .16, 'colors': dict(zip(NAMES,COLORS))}

def terrain():
    x,y = np.meshgrid(np.linspace(0,SIZE,NX+1),np.linspace(0,SIZE+APRON,NY+1))
    lat=SOUTH+np.clip((y-APRON)/SIZE,0,1)*DLAT
    lon=WEST+x/SIZE*DLON
    elevation=np.zeros_like(x)
    tiles={}
    for lon0 in (-73,-72):
        p=ROOT/f'data/S14W{abs(lon0):03}.hgt.gz'
        a=np.frombuffer(gzip.decompress(p.read_bytes()),dtype='>i2').reshape(3601,3601).astype(float)
        tiles[lon0]=a
        chosen=np.floor(lon)==lon0
        # Refuse missing heights instead of propagating voids into the mesh.
        xx=(lon[chosen]-lon0)*3600
        yy=(-13-lat[chosen])*3600
        patch=a[max(0,int(yy.min())-2):min(3601,int(yy.max())+3),max(0,int(xx.min())-2):min(3601,int(xx.max())+3)]
        assert np.all(patch > -1000), 'Missing/invalid DEM samples in crop'
        elevation[chosen]=ndi.map_coordinates(a,[yy,xx],order=1,mode='nearest')
    row0,row1=sorted([int((-13-(SOUTH+DLAT))*3600),int((-13-SOUTH)*3600)])
    seam=np.abs(tiles[-73][row0:row1+1,-1]-tiles[-72][row0:row1+1,0])
    assert seam.max()<=2, f'DEM seam mismatch: {seam.max()} m'
    raw=elevation.copy()
    elevation=ndi.gaussian_filter(elevation,sigma=1.25,mode='nearest')
    # Scale at 1:100,000 horizontally, 1.6x vertical exaggeration.
    z=BASE+(elevation-elevation.min())*(SIZE/AREA)*1.6
    # Flat integral front label strip; gradual smoothstep transition to terrain.
    blend=np.clip((y-12)/4,0,1)
    blend=blend*blend*(3-2*blend)
    z=BASE+(z-BASE)*blend
    report['dem']={'tiles':['S14W073','S14W072'],'voids_in_crop':0,
      'tile_seam_max_difference_m':float(seam.max()),'elevation_min_max_m':[float(raw.min()),float(raw.max())],
      'gaussian_sigma_ground_m':float(1.25*DX*AREA/SIZE),'vertical_exaggeration':1.6,
      'max_adjacent_elevation_change_m':float(max(abs(np.diff(elevation,axis=0)).max(),abs(np.diff(elevation,axis=1)).max()))}
    np.savez_compressed(OUT/'terrain_samples.npz',height=z,elevation=elevation)
    return x,y,z

def xy(p):
    return ((p['lon']-WEST)/DLON*SIZE/DX, (APRON+(p['lat']-SOUTH)/DLAT*SIZE)/DY)

def raster_layers():
    roads=Image.new('1',(NX,NY)); buildings=Image.new('1',(NX,NY)); green=Image.new('1',(NX,NY))
    dr,db,dg=map(ImageDraw.Draw,(roads,buildings,green))
    counts={'roads':0,'building_footprints':0,'green_areas':0,'mapped_trees':0}
    osm=json.loads((ROOT/'data/cusco_osm.json').read_text())['elements']
    # Keep main network legible. Minor service alleys are intentionally omitted.
    widths={'motorway':.95,'trunk':.95,'primary':.85,'secondary':.8,'tertiary':.7,
            'residential':.6,'living_street':.6,'unclassified':.6}
    for e in osm:
        tags=e.get('tags',{}); g=e.get('geometry',[])
        if len(g)<2: continue
        pts=[xy(p) for p in g]
        if 'building' in tags and len(pts)>=4 and g[0]==g[-1]:
            db.polygon(pts,fill=1)
            counts['building_footprints']+=1
        elif tags.get('highway') in widths:
            dr.line(pts,fill=1,width=max(2,round(widths[tags['highway']]/DX)),joint='curve')
            counts['roads']+=1
    for e in json.loads((ROOT/'data/cusco_green.json').read_text())['elements']:
        g=e.get('geometry',[])
        if len(g)>=4 and g[0]==g[-1]:
            dg.polygon([xy(p) for p in g],fill=1); counts['green_areas']+=1
        elif e['type']=='node' and e.get('tags',{}).get('natural')=='tree':
            xx,yy=xy(e); r=.55/DX
            if 0<=xx<NX and APRON/DY<=yy<NY:
                dg.ellipse((xx-r,yy-r,xx+r,yy+r),fill=1); counts['mapped_trees']+=1
    b=np.array(buildings,dtype=bool)
    # A single-cell dilation gives tiny mapped houses a printable footprint.
    b=ndi.binary_dilation(b,iterations=1)
    b=ndi.binary_closing(b,structure=np.ones((2,2)))
    r=np.array(roads,dtype=bool); g=np.array(green,dtype=bool)
    mat=np.zeros((NY,NX),np.uint8)
    mat[g]=3; mat[b]=2; mat[r]=1
    mat[:math.ceil(APRON/DY)]=0
    mat[[0,-1],:]=0; mat[:,[0,-1]]=0
    # Remove isolated pixel specks that would be below nozzle width.
    for k in (1,2,3):
        lab,n=ndi.label(mat==k)
        sizes=np.bincount(lab.ravel()); keep=sizes>=4; keep[0]=False
        mat[(mat==k)&~keep[lab]]=0
    # Eliminate edge/vertex-only diagonal contacts in every material.
    for iteration in range(100):
        a,b,c,d=mat[:-1,:-1],mat[:-1,1:],mat[1:,:-1],mat[1:,1:]
        bad=((a==d)&(a!=b)&(a!=c))|((b==c)&(b!=a)&(b!=d))
        if not bad.any(): break
        jj,ii=np.where(bad)
        for dj,di in [(0,0),(0,1),(1,0),(1,1)]: mat[jj+dj,ii+di]=0
    else: raise ValueError('Could not remove diagonal material contacts')
    report['osm']=counts
    report['material_cells']=[int((mat==i).sum()) for i in range(4)]
    return mat

def surface_heights(z,mat):
    center=(z[:-1,:-1]+z[1:,:-1]+z[:-1,1:]+z[1:,1:])/4
    lab,n=ndi.label(mat==2)
    peaks=ndi.maximum(center,lab,np.arange(n+1)); peaks[0]=0
    roofs=peaks[lab]+.95
    # Flat connected city-block roofs; heights schematic where no measured data exists.
    target=np.where(mat==2,roofs,center+np.where(mat==1,.18,np.where(mat==3,.35,0)))
    extra=target-center
    ev=np.zeros_like(z); cnt=np.zeros_like(z)
    for dj,di in [(0,0),(1,0),(0,1),(1,1)]:
        ev[dj:dj+NY,di:di+NX]+=extra
        cnt[dj:dj+NY,di:di+NX]+=1
    upper=z+ev/cnt
    lower=z-.8
    return upper,lower

def solid_for_material(k,x,y,upper,lower,mat):
    """Exact complementary meshes; no overlapping bodies or open bottoms."""
    nv=x.size; ids=np.arange(nv).reshape(x.shape)
    vertices=np.vstack([np.c_[x.ravel(),y.ravel(),upper.ravel()],np.c_[x.ravel(),y.ravel(),lower.ravel()]])
    cells=mat==k
    a,b,c,d=ids[:-1,:-1],ids[:-1,1:],ids[1:,:-1],ids[1:,1:]
    faces=[]
    def caps(mask,offset,reverse=False):
        aa,bb,cc,dd=(v[mask]+offset for v in (a,b,c,d))
        f=np.concatenate([np.c_[aa,bb,cc],np.c_[bb,dd,cc]])
        faces.append(f[:,::-1] if reverse else f)
    caps(cells,0)
    if k==0: caps(~cells,nv)
    else: caps(cells,nv,True)
    # CCW boundary edges around each active cell, including internal holes.
    pad=np.pad(cells,1)
    edges=[]
    for neighbor,start,end in [(pad[:-2,1:-1],a,b),(pad[1:-1,2:],b,d),
                               (pad[2:,1:-1],d,c),(pad[1:-1,:-2],c,a)]:
        boundary=cells & ~neighbor
        edges.append(np.c_[start[boundary],end[boundary]])
    edges=np.concatenate(edges)
    aa,bb=edges.T
    faces.extend([np.c_[aa,aa+nv,bb+nv],np.c_[aa,bb+nv,bb]])
    if k==0:
        # Continuous sides down to a planar bottom; each rim edge is split at lower.
        rim=np.concatenate([ids[0,:],ids[1:,-1],ids[-1,-2::-1],ids[-2:0:-1,0]])
        bottom_start=len(vertices)
        vertices=np.vstack([vertices,np.c_[x.ravel()[rim],y.ravel()[rim],np.zeros(len(rim))],[[SIZE/2,(SIZE+APRON)/2,0]]])
        aa=rim+nv; bb=np.roll(aa,-1)
        ba=np.arange(len(rim))+bottom_start; bbot=np.roll(ba,-1)
        faces.extend([np.c_[aa,ba,bbot],np.c_[aa,bbot,bb],np.c_[np.full(len(rim),len(vertices)-1),bbot,ba]])
    mesh=trimesh.Trimesh(vertices,np.concatenate(faces),process=True)
    mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_winding_consistent, f'{k}: open or inconsistent mesh'
    solid=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
    assert solid.status()==md.Error.NoError, (k,solid.status())
    return solid

def text_solid():
    path=TextPath((0,0),LABEL,size=12,prop=FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    shape=Polygon()
    # XOR contours preserves the counters inside c, s, etc. across glyphs.
    for contour in path.to_polygons():
        poly=Polygon(contour)
        if poly.is_valid and poly.area>0: shape=shape.symmetric_difference(poly)
    xmin,ymin,xmax,ymax=shape.bounds
    factor=7.5/(ymax-ymin)
    shape=scale(shape,factor,factor,origin=(0,0))
    xmin,ymin,xmax,ymax=shape.bounds
    shape=translate(shape,SIZE/2-(xmin+xmax)/2,2.25-ymin)
    solids=[]
    for p in shape.geoms if hasattr(shape,'geoms') else [shape]:
        mesh=trimesh.creation.extrude_polygon(p,.96,engine='earcut')
        mesh.apply_translation((0,0,3.52))
        solids.append(md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32))))
    label=md.Manifold.batch_boolean(solids,md.OpType.Add)
    report['lettering']={'text':LABEL,'font':'DejaVu Sans','orientation':'horizontal XY',
      'raised_mm':.48,'embedded_mm':.48,'glyph_height_mm':7.5,'bounds':list(label.bounding_box())}
    return label

def as_mesh(solid):
    m=solid.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:,:3],np.asarray(m.tri_verts),process=False)

def write_3mf(meshes):
    xml=['<?xml version="1.0" encoding="UTF-8"?>',
      '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
      '<metadata name="Title">Cusco - 4 colour terrain</metadata>',
      '<metadata name="BambuStudio:3mfVersion">1</metadata>', '<resources>', '<basematerials id="10">']
    for name,col in zip(NAMES,COLORS): xml.append(f'<base name="{name}" displaycolor="{col}FF"/>')
    xml.append('</basematerials>')
    for i,mesh in enumerate(meshes,1):
        xml.append(f'<object id="{i}" type="model" name="{NAMES[i-1]}" pid="10" pindex="{i-1}"><mesh><vertices>')
        xml.extend('<vertex x="%.7g" y="%.7g" z="%.7g"/>'%tuple(v) for v in mesh.vertices)
        xml.append('</vertices><triangles>')
        xml.extend('<triangle v1="%d" v2="%d" v3="%d"/>'%tuple(f) for f in mesh.faces)
        xml.append('</triangles></mesh></object>')
    xml.append('<object id="5" type="model" name="Cusco"><components>')
    xml.extend(f'<component objectid="{i}"/>' for i in range(1,5))
    xml.append('</components></object></resources><build><item objectid="5" transform="1 0 0 0 1 0 0 0 1 19 28 0"/></build></model>')
    config=['<?xml version="1.0" encoding="UTF-8"?><config><object id="5"><metadata key="name" value="Cusco"/><metadata key="extruder" value="1"/>']
    for i in range(1,5):
        config.append(f'<part id="{i}" subtype="normal_part"><metadata key="name" value="{NAMES[i-1]}"/><metadata key="extruder" value="{i}"/></part>')
    config.append('</object><plate><metadata key="plater_id" value="1"/><model_instance><metadata key="object_id" value="5"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="1"/></model_instance></plate></config>')
    with zipfile.ZipFile(OUT/'Cusco_AMS_4_Farben.3mf','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',''.join(xml))
        z.writestr('Metadata/model_settings.config',''.join(config))

def main():
    print('Sampling and checking two DEM tiles...',flush=True)
    x,y,z=terrain()
    print('Rasterizing mapped city blocks, roads and green areas...',flush=True)
    mat=raster_layers(); upper,lower=surface_heights(z,mat)
    solids=[]
    for i in range(4):
        print('Building watertight solid',NAMES[i],flush=True)
        solids.append(solid_for_material(i,x,y,upper,lower,mat))
    print('Inlaying horizontal lettering...',flush=True)
    label=text_solid()
    solids[0]=solids[0]-label
    solids[1]=solids[1]+label
    report['parts']=[]; meshes=[]
    for i,solid in enumerate(solids):
        assert solid.status()==md.Error.NoError
        mesh=as_mesh(solid)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        mesh.export(OUT/f'{NAMES[i]}.stl')
        meshes.append(mesh)
        report['parts'].append({'name':NAMES[i],'watertight':bool(mesh.is_watertight),
          'winding_consistent':bool(mesh.is_winding_consistent),'volume_mm3':float(mesh.volume),'triangles':len(mesh.faces)})
    print('Checking intersections and joined solid...',flush=True)
    overlaps=[]
    for i in range(4):
        for j in range(i+1,4):
            v=abs((solids[i]^solids[j]).volume())
            assert v<.02,(i,j,v)
            overlaps.append({'parts':[i+1,j+1],'intersection_mm3':v})
    whole=md.Manifold.batch_boolean(solids,md.OpType.Add)
    all_components=whole.decompose()
    components=[c for c in all_components if abs(c.volume())>1e-6]
    report['boolean_zero_volume_fragments_removed']=len(all_components)-len(components)
    report['connected_components']=len(components)
    assert len(components)==1, f'{len(components)} detached pieces'
    whole=components[0]
    full=as_mesh(whole)
    full.export(OUT/'Cusco_einfarbig.stl')
    report['overall_bounds_mm']=full.bounds.tolist()
    report['dimensions_mm']=full.extents.tolist()
    report['pairwise_intersections']=overlaps
    print('Checking every 0.16 mm horizontal section...',flush=True)
    levels=np.arange(.08,full.bounds[1,2],.16)
    areas=[whole.slice(float(h)).area() for h in levels]
    assert all(a>0 for a in areas)
    report['cross_section_checks']={'count':len(areas),'all_nonempty':True,'min_area_mm2':min(areas)}
    print('Exporting assembled 3MF...',flush=True)
    write_3mf(meshes)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'dimensions':report['dimensions_mm'],'components':len(components),'label':LABEL},indent=2),flush=True)

if __name__=='__main__': main()
