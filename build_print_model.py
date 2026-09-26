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
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output/print_v2'
OUT.mkdir(parents=True, exist_ok=True)
SIZE, AREA, BASE = 200., 20000., 4.
# Keep the previous sampling grid and crop its front margin only after building
# the feature heights. This preserves city blocks and roof heights exactly.
SAMPLING_APRON = 16.
NX, NY = 734, 788
DX, DY = SIZE/NX, (SIZE+SAMPLING_APRON)/NY
LAT, LON = -13.53195, -71.96746
SOUTH = LAT-10/111.32
WEST = LON-10/(111.32*math.cos(math.radians(LAT)))
DLAT = 20/111.32
DLON = 20/(111.32*math.cos(math.radians(LAT)))
LABEL = 'Cusco'
NAMES = ['01_Terrain_Sockel', '02_Strassen_Schrift', '03_Gebaeude', '04_Vegetation']
COLORS = ['#B8A17C', '#64696C', '#AC5438', '#637D46']
BUILDING_RISE, ROAD_RISE, AIRPORT_RISE = 1.20, .32, .40
INLAY_DEPTH = .64  # Four 0.16 mm layers below terrain, plus the visible relief.
LABEL_RISE, LABEL_DEPTH = .64, .48
LABEL_WIDTH, LABEL_HEIGHT = 28.8, 7.5
ROAD_WIDTHS = {'motorway':.95,'trunk':.95,'primary':.85,'secondary':.8,'tertiary':.7,
               'residential':.6,'living_street':.6,'unclassified':.6,
               'motorway_link':.6,'trunk_link':.6,'primary_link':.6,
               'secondary_link':.6,'tertiary_link':.6}
report = {'label': LABEL, 'size_xy_mm': [SIZE, SIZE], 'terrain_km':20,
          'base_mm': BASE, 'inlay_depth_mm': INLAY_DEPTH,
          'layer_height_check_mm': .16, 'colors': dict(zip(NAMES,COLORS))}

def terrain():
    x,y = np.meshgrid(np.linspace(0,SIZE,NX+1),np.linspace(-SAMPLING_APRON,SIZE,NY+1))
    lat=SOUTH+np.clip(y/SIZE,0,1)*DLAT
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
    report['dem']={'tiles':['S14W073','S14W072'],'voids_in_crop':0,
      'tile_seam_max_difference_m':float(seam.max()),'elevation_min_max_m':[float(raw.min()),float(raw.max())],
      'gaussian_sigma_ground_m':float(1.25*DX*AREA/SIZE),'vertical_exaggeration':1.6,
      'max_adjacent_elevation_change_m':float(max(abs(np.diff(elevation,axis=0)).max(),abs(np.diff(elevation,axis=1)).max()))}
    np.savez_compressed(OUT/'terrain_samples.npz',height=z,elevation=elevation)
    return x,y,z

def xy(p):
    return ((p['lon']-WEST)/DLON*SIZE/DX, (SAMPLING_APRON+(p['lat']-SOUTH)/DLAT*SIZE)/DY)

def landcover():
    """Aggregate categorical WorldCover data to the terrain cells, north up first."""
    source=ROOT/'data/cusco_worldcover_2021.tif'
    classes=np.zeros((NY,NX),dtype=np.uint8)
    transform=from_bounds(WEST,SOUTH-SAMPLING_APRON/SIZE*DLAT,WEST+DLON,SOUTH+DLAT,NX,NY)
    with rasterio.open(source) as src:
        reproject(rasterio.band(src,1),classes,src_transform=src.transform,src_crs=src.crs,
                  dst_transform=transform,dst_crs='EPSG:4326',resampling=Resampling.mode,
                  src_nodata=0,dst_nodata=0)
    classes=np.flipud(classes).copy()  # Mesh y increases northwards.
    interior=classes[math.ceil(SAMPLING_APRON/DY):]
    assert np.all(interior>0), 'Missing land-cover data inside model'
    values,counts=np.unique(interior,return_counts=True)
    report['landcover']={'dataset':'ESA WorldCover 2021 v200','source_resolution_m':10,
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'resampling':'mode, then north-up rows reversed into south-to-north mesh',
      'class_cells':{str(k):int(v) for k,v in zip(values,counts)},
      'green_classes':[10,20,30,40,90,95,100],'unclassified_interior_cells':0,
      'vegetation_rise_mm':0,'note':'Land-cover classes, not seasonal or satellite RGB colours.'}
    return np.isin(classes,[10,20,30,40,90,95,100])

def repair_material_contacts(mat):
    """Resolve diagonal-only contacts by filling one cell; never erase roads.

    Material priority only increases, so repairs cannot oscillate. At each
    ambiguous 2x2 block choose a single replacement that resolves that block.
    Roads take precedence over buildings, vegetation and background.
    """
    rank=np.array([0,3,2,1])
    def ambiguous(a):
        p,q,r,s=a.ravel()
        return (p==s and p!=q and p!=r) or (q==r and q!=p and q!=s)
    for iteration in range(100):
        a,b,c,d=mat[:-1,:-1],mat[:-1,1:],mat[1:,:-1],mat[1:,1:]
        bad=((a==d)&(a!=b)&(a!=c))|((b==c)&(b!=a)&(b!=d))
        if not bad.any(): return iteration
        for j,i in zip(*np.where(bad)):
            block=mat[j:j+2,i:i+2]
            if not ambiguous(block): continue
            winner=block.ravel()[np.argmax(rank[block.ravel()])]
            candidates=[]
            for dj,di in [(0,0),(0,1),(1,0),(1,1)]:
                if block[dj,di]==winner: continue
                trial=block.copy(); trial[dj,di]=winner
                if ambiguous(trial): continue
                jj,ii=j+dj,i+di
                if jj in (0,mat.shape[0]-1) or ii in (0,mat.shape[1]-1): continue
                support=np.count_nonzero(mat[max(0,jj-1):jj+2,max(0,ii-1):ii+2]==winner)
                candidates.append((int(rank[block[dj,di]]),-support,dj,di))
            assert candidates, 'Cannot resolve material contact without altering model rim'
            _,_,dj,di=min(candidates)
            block[dj,di]=winner
    raise ValueError('Could not resolve diagonal material contacts')

def raster_layers():
    roads=Image.new('1',(NX,NY)); buildings=Image.new('1',(NX,NY)); green=Image.new('1',(NX,NY))
    airport=Image.new('1',(NX,NY)); da=ImageDraw.Draw(airport)
    dr,db,dg=map(ImageDraw.Draw,(roads,buildings,green))
    counts={'roads':0,'building_footprints':0,'green_areas':0,'mapped_trees':0}
    osm=json.loads((ROOT/'data/cusco_osm.json').read_text())['elements']
    # Keep main network legible. Minor service alleys are intentionally omitted.
    widths=ROAD_WIDTHS
    counts['road_links']=0
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
            counts['road_links']+=int(tags['highway'].endswith('_link'))
    # Separate OSM query: the original highway/building selection omitted airfields.
    airport_data=json.loads((ROOT/'data/cusco_airport.json').read_text())
    counts['airport']={'runway':0,'taxiway':0,'apron':0}
    for e in airport_data['elements']:
        tags=e.get('tags',{}); g=e.get('geometry',[])
        kind=tags.get('aeroway')
        if len(g)<2 or kind not in counts['airport']: continue
        pts=[xy(p) for p in g]
        if kind=='apron':
            if len(g)<4 or g[0]!=g[-1]: continue
            da.polygon(pts,fill=1)
        else:
            # Modest minimum widths for a 0.4 mm nozzle; preserve mapped alignment.
            width=1.1 if kind=='runway' else .55
            da.line(pts,fill=1,width=max(2,round(width/DX)),joint='curve')
        counts['airport'][kind]+=1
    assert counts['airport']['runway']>0, 'Missing mapped airport runway'
    for e in json.loads((ROOT/'data/cusco_green.json').read_text())['elements']:
        g=e.get('geometry',[])
        if len(g)>=4 and g[0]==g[-1]:
            dg.polygon([xy(p) for p in g],fill=1); counts['green_areas']+=1
        elif e['type']=='node' and e.get('tags',{}).get('natural')=='tree':
            xx,yy=xy(e); r=.55/DX
            if 0<=xx<NX and SAMPLING_APRON/DY<=yy<NY:
                dg.ellipse((xx-r,yy-r,xx+r,yy+r),fill=1); counts['mapped_trees']+=1
    b=np.array(buildings,dtype=bool)
    # A single-cell dilation gives tiny mapped houses a printable footprint.
    b=ndi.binary_dilation(b,iterations=1)
    b=ndi.binary_closing(b,structure=np.ones((2,2)))
    r=np.array(roads,dtype=bool); g=np.array(green,dtype=bool)
    satellite_green=landcover()
    # Keep the existing horizontal sand-coloured lettering landing. Only the
    # new land-cover tint is excluded here; mapped OSM features stay protected.
    xmin,ymin,xmax,ymax=label_shape().bounds
    label_rows=slice(math.floor((ymin-1.5+SAMPLING_APRON)/DY),math.ceil((ymax+1.5+SAMPLING_APRON)/DY))
    label_cols=slice(math.floor((xmin-1.5)/DX),math.ceil((xmax+1.5)/DX))
    report['landcover']['label_patch_green_cells_excluded']=int(satellite_green[label_rows,label_cols].sum())
    satellite_green[label_rows,label_cols]=False
    mat=np.zeros((NY,NX),np.uint8)
    air=np.array(airport,dtype=bool)
    mat[g|satellite_green]=3; mat[b]=2; mat[r|air]=1
    mat[:math.ceil(SAMPLING_APRON/DY)]=0
    mat[[0,-1],:]=0; mat[:,[0,-1]]=0
    # Remove isolated pixel specks that would be below nozzle width.
    for k in (2,3):
        lab,n=ndi.label(mat==k)
        sizes=np.bincount(lab.ravel()); keep=sizes>=4; keep[0]=False
        mat[(mat==k)&~keep[lab]]=0
    before=mat.copy()
    iterations=repair_material_contacts(mat)
    assert np.all(mat[before==1]==1), 'Contact repair removed a road or airport cell'
    # Every connected road raster remains in a single final road component.
    old,n=ndi.label(before==1); new,_=ndi.label(mat==1)
    lo=ndi.minimum(new,old,np.arange(1,n+1)); hi=ndi.maximum(new,old,np.arange(1,n+1))
    assert np.all(lo==hi) and np.all(lo>0), 'Contact repair split a road'
    report['road_topology']={'source_road_airport_cells':int((before==1).sum()),
      'source_cells_removed':0,'components_before':int(n),'components_after':int(ndi.label(mat==1)[1]),
      'existing_components_preserved':True,'repair_iterations':iterations,
      'cells_reassigned':int((before!=mat).sum()),'road_cells_added':int(((before!=1)&(mat==1)).sum())}
    report['osm']=counts
    report['airport_source_timestamp']=airport_data['osm3s']['timestamp_osm_base']
    report['feature_relief_mm']={'building_roof_offset':BUILDING_RISE,
      'road_offset':ROAD_RISE,'airport_offset':AIRPORT_RISE,
      'note':'Cell targets blended at shared mesh vertices; roof offset above block maximum.'}
    report['airport_cells']=int((air & (mat==1)).sum())
    report['material_cells']=[int((mat==i).sum()) for i in range(4)]
    return mat,air

def surface_heights(z,mat,airport):
    center=(z[:-1,:-1]+z[1:,:-1]+z[:-1,1:]+z[1:,1:])/4
    lab,n=ndi.label(mat==2)
    peaks=ndi.maximum(center,lab,np.arange(n+1)); peaks[0]=0
    roofs=peaks[lab]+BUILDING_RISE
    # Flat connected city-block roofs; heights schematic where no measured data exists.
    street_rise=np.where(airport,AIRPORT_RISE,ROAD_RISE)
    # Vegetation is a surface colour, without raising entire mountainsides.
    target=np.where(mat==2,roofs,center+np.where(mat==1,street_rise,0))
    extra=target-center
    ev=np.zeros_like(z); cnt=np.zeros_like(z)
    for dj,di in [(0,0),(1,0),(0,1),(1,1)]:
        ev[dj:dj+NY,di:di+NX]+=extra
        cnt[dj:dj+NY,di:di+NX]+=1
    upper=z+ev/cnt
    lower=z-INLAY_DEPTH
    return upper,lower

def crop_front_margin(x,y,upper,lower,mat):
    """Keep all original interior vertices; interpolate only the new south edge."""
    j=np.searchsorted(y[:,0],0)-1
    t=-y[j,0]/(y[j+1,0]-y[j,0])
    def crop(a):
        result=a[j:].copy()
        result[0]=(1-t)*a[j]+t*a[j+1]
        return result
    cropped_mat=mat[j:].copy()
    assert not cropped_mat[0].any(), 'Crop would expose a coloured sidewall'
    report['cropped_front_margin_mm']=SAMPLING_APRON
    report['interior_sampling_preserved']=True
    report['material_cells']=[int((cropped_mat==i).sum()) for i in range(4)]
    return crop(x),crop(y),crop(upper),crop(lower),cropped_mat

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
        vertices=np.vstack([vertices,np.c_[x.ravel()[rim],y.ravel()[rim],np.zeros(len(rim))],[[SIZE/2,SIZE/2,0]]])
        aa=rim+nv; bb=np.roll(aa,-1)
        ba=np.arange(len(rim))+bottom_start; bbot=np.roll(ba,-1)
        faces.extend([np.c_[aa,ba,bbot],np.c_[aa,bbot,bb],np.c_[np.full(len(rim),len(vertices)-1),bbot,ba]])
    mesh=trimesh.Trimesh(vertices,np.concatenate(faces),process=True)
    mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_winding_consistent, f'{k}: open or inconsistent mesh'
    solid=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
    assert solid.status()==md.Error.NoError, (k,solid.status())
    return solid

def label_shape():
    path=TextPath((0,0),LABEL,size=12,prop=FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    shape=Polygon()
    # XOR contours preserves the counters inside c, s, etc. across glyphs.
    for contour in path.to_polygons():
        poly=Polygon(contour)
        if poly.is_valid and poly.area>0: shape=shape.symmetric_difference(poly)
    xmin,ymin,xmax,ymax=shape.bounds
    # Stronger strokes inside the existing lettering footprint and flat landing.
    shape=scale(shape,LABEL_WIDTH/(xmax-xmin),LABEL_HEIGHT/(ymax-ymin),origin=(0,0))
    xmin,ymin,xmax,ymax=shape.bounds
    # A feature-free patch on the southwest hillside, inside the original crop.
    shape=translate(shape,45-(xmin+xmax)/2,18-ymin)
    return shape

def flatten_label_surface(shape,x,y,upper,lower,mat):
    """Make a small horizontal landing entirely inside the existing model."""
    xmin,ymin,xmax,ymax=shape.bounds
    assert 0<xmin-1<xmax+1<SIZE and 0<ymin-1<ymax+1<SIZE
    grid_y=y[:,0]
    first_row=max(0,np.searchsorted(grid_y,ymin-1,side='right')-1)
    last_row=np.searchsorted(grid_y,ymax+1,side='left')
    footprint=mat[first_row:last_row,
                  math.floor((xmin-1)/DX):math.ceil((xmax+1)/DX)]
    assert footprint.size and not footprint.any(), 'Lettering would cover mapped features'
    # The flat core includes a margin wider than one grid cell, so every
    # triangle under a glyph is horizontal. Blend only the surrounding rim.
    padding,transition=.55,.40
    distance=np.maximum.reduce([xmin-padding-x,x-(xmax+padding),
                                ymin-padding-y,y-(ymax+padding),np.zeros_like(x)])
    core=distance==0
    weight=np.clip(1-distance/transition,0,1)
    weight=weight*weight*(3-2*weight)
    level=round(float(np.median(upper[core]))/.16)*.16
    upper[:]=upper*(1-weight)+level*weight
    lower[:]=lower*(1-weight)+(level-INLAY_DEPTH)*weight
    assert np.ptp(upper[core])<1e-10, 'Lettering landing is not flat'
    report['lettering_surface']={'plane_z_mm':level,'flat_core_xy_mm':
      [xmin-padding,ymin-padding,xmax+padding,ymax+padding],
      'transition_mm':transition,'planarity_error_mm':float(np.ptp(upper[core])),
      'inside_model':True,'mapped_features_covered':0}
    return level

def text_solid(shape,level):
    solids=[]
    for p in shape.geoms if hasattr(shape,'geoms') else [shape]:
        mesh=trimesh.creation.extrude_polygon(p,LABEL_DEPTH+LABEL_RISE,engine='earcut')
        mesh.apply_translation((0,0,level-LABEL_DEPTH))
        solids.append(md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32))))
    label=md.Manifold.batch_boolean(solids,md.OpType.Add)
    assert label.status()==md.Error.NoError and label.volume()>0
    assert label.bounding_box()[2]>BASE, 'Letter inlay unexpectedly reaches the base'
    assert abs(label.volume()-shape.area*(LABEL_DEPTH+LABEL_RISE))<.02, 'Nonuniform letter extrusion'
    glyphs=[c for c in label.decompose() if abs(c.volume())>1e-6]
    assert len(glyphs)==len(LABEL), 'A glyph is missing or fragmented'
    report['lettering']={'text':LABEL,'font':'DejaVu Sans Bold','orientation':'horizontal XY on internal flat terrain patch',
      'raised_mm':LABEL_RISE,'embedded_mm':LABEL_DEPTH,'glyph_height_mm':LABEL_HEIGHT,
      'glyph_width_mm':LABEL_WIDTH,
      'mapped_features_covered':0,'separate_apron_mm':0,'glyph_components':len(glyphs),
      'volume_mm3':label.volume(),'expected_volume_mm3':shape.area*(LABEL_DEPTH+LABEL_RISE),
      'bounds':list(label.bounding_box())}
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
    mat,airport=raster_layers(); upper,lower=surface_heights(z,mat,airport)
    x,y,upper,lower,mat=crop_front_margin(x,y,upper,lower,mat)
    shape=label_shape()
    label_level=flatten_label_surface(shape,x,y,upper,lower,mat)
    solids=[]
    for i in range(4):
        print('Building watertight solid',NAMES[i],flush=True)
        solids.append(solid_for_material(i,x,y,upper,lower,mat))
    print('Adding horizontal lettering on the internal flat surface...',flush=True)
    label=text_solid(shape,label_level)
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
