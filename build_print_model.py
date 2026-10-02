#!/usr/bin/env python3
"""Rebuild the Cusco relief as four mutually exclusive watertight solids.

Run with .venv-model/bin/python. Old prototypes are deliberately left intact.
"""
from pathlib import Path
import gzip, json, math, zipfile, hashlib, os, sys
from xml.sax.saxutils import escape
import numpy as np
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
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
# Preserve the original terrain triangles, but resolve map features twice as finely.
SAMPLING_APRON = 16.
TERRAIN_NX, TERRAIN_NY = 734, 788
NX, NY = 2*TERRAIN_NX, 2*TERRAIN_NY
DX, DY = SIZE/NX, (SIZE+SAMPLING_APRON)/NY
LAT, LON = -13.53195, -71.96746
SOUTH = LAT-10/111.32
WEST = LON-10/(111.32*math.cos(math.radians(LAT)))
DLAT = 20/111.32
DLON = 20/(111.32*math.cos(math.radians(LAT)))
LABEL = 'Cusco'
NAMES = ['01_Terrain_Sockel', '02_Strassen_Schrift', '03_Gebaeude', '04_Vegetation']
COLORS = ['#B8A17C', '#64696C', '#AC5438', '#637D46']
BUILDING_RISE, ROAD_RISE, AIRPORT_RISE = .48, .24, .40
INLAY_DEPTH = .64  # Four 0.16 mm layers below terrain, plus the visible relief.
LABEL_RISE, LABEL_DEPTH = .64, .48
LABEL_WIDTH, LABEL_HEIGHT = 28.8, 7.5
ROAD_WIDTHS = {'motorway':.8,'trunk':.8,'primary':.7,'secondary':.6,'tertiary':.5,
               'residential':.4,'living_street':.4,'unclassified':.4,
               'motorway_link':.4,'trunk_link':.4,'primary_link':.4,
               'secondary_link':.4,'tertiary_link':.4}
MAJOR_ROADS={'motorway','trunk','primary','secondary','tertiary',
             'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
MESH_TOLERANCE = 0.  # Remove only coplanar detail, preserving colour interfaces.
report = {'label': LABEL, 'size_xy_mm': [SIZE, SIZE], 'terrain_km':20,
          'base_mm': BASE, 'inlay_depth_mm': INLAY_DEPTH,
          'layer_height_check_mm': .16, 'colors': dict(zip(NAMES,COLORS))}

def refine_terrain(a):
    """Subdivide the original b-c diagonal triangles without changing their shape."""
    fine=np.empty((2*a.shape[0]-1,2*a.shape[1]-1))
    fine[::2,::2]=a
    fine[::2,1::2]=(a[:,:-1]+a[:,1:])/2
    fine[1::2,::2]=(a[:-1]+a[1:])/2
    fine[1::2,1::2]=(a[:-1,1:]+a[1:,:-1])/2
    return fine

def terrain():
    x,y = np.meshgrid(np.linspace(0,SIZE,TERRAIN_NX+1),np.linspace(-SAMPLING_APRON,SIZE,TERRAIN_NY+1))
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
      'gaussian_sigma_ground_m':float(1.25*SIZE/TERRAIN_NX*AREA/SIZE),'vertical_exaggeration':1.6,
      'max_adjacent_elevation_change_m':float(max(abs(np.diff(elevation,axis=0)).max(),abs(np.diff(elevation,axis=1)).max()))}
    np.savez_compressed(OUT/'terrain_samples.npz',height=z,elevation=elevation)
    report['terrain_refinement']={'factor':2,'original_triangle_surface_preserved':True,
      'feature_cell_mm':[DX,DY],'mesh_simplification_tolerance_mm':MESH_TOLERANCE}
    return refine_terrain(x),refine_terrain(y),refine_terrain(z)

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
      'green_classes':[10,20,30,90,95,100],'unclassified_interior_cells':0,
      'vegetation_rise_mm':0,'note':'Land-cover classes, not seasonal or satellite RGB colours.'}
    mask=np.isin(classes,[10,20,30,90,95,100])
    # Cropland keeps the earth colour; a majority filter suppresses sub-nozzle
    # fragments without inventing forest or deriving colours from elevation.
    window=(max(1,round(.95/DY)),max(1,round(.95/DX)))
    mask=ndi.uniform_filter(mask.astype(float),size=window,mode='nearest')>=.5
    report['landcover']['generalization']={'majority_window_cells':list(window),
      'cropland_material':'earth','window_mm':[window[1]*DX,window[0]*DY]}
    return mask

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

def group_buildings(raw,roads):
    """Join nearby mapped houses and rescue small remnants within road barriers."""
    grouped=ndi.binary_closing(ndi.binary_dilation(raw,iterations=1),
                               structure=np.ones((2,2))) & ~roads
    minimum_cells=math.ceil(.16/(DX*DY))
    labels,n=ndi.label(grouped)
    sizes=np.bincount(labels.ravel())
    tiny=(sizes[labels]<minimum_cells)&grouped
    # Only grow near actual mapped footprints, and never through a road cell.
    allowed=ndi.binary_dilation(raw,iterations=4)&~roads
    rescued=ndi.binary_dilation(tiny,iterations=2,mask=allowed)
    grouped|=rescued
    labels,n=ndi.label(grouped)
    sizes=np.bincount(labels.ravel()); keep=sizes>=minimum_cells; keep[0]=False
    removed=grouped&~keep[labels]
    report['building_grouping']={'minimum_component_area_mm2':.16,
      'small_remnant_cells_before_rescue':int(tiny.sum()),
      'cells_added_to_rescue_remnants':int((rescued&~tiny).sum()),
      'unprintable_cells_removed':int(removed.sum()),
      'max_growth_from_mapped_footprints_mm':4*DX,
      'road_cells_overwritten':0}
    return grouped&~removed

def prioritize_buildings(raw,roads,major,minor_core=None):
    """Reclaim minor-road shoulders while keeping a narrow mapped street network."""
    protected=ndi.binary_dilation(raw,iterations=1)
    core=np.zeros_like(roads) if minor_core is None else minor_core
    return (roads & (~protected | major)) | core

def raster_layers():
    roads=Image.new('1',(NX,NY)); buildings=Image.new('1',(NX,NY)); green=Image.new('1',(NX,NY))
    airport=Image.new('1',(NX,NY)); da=ImageDraw.Draw(airport)
    dr,db,dg=map(ImageDraw.Draw,(roads,buildings,green))
    main_roads=Image.new('1',(NX,NY)); dm=ImageDraw.Draw(main_roads)
    minor_roads=Image.new('1',(NX,NY)); dminor=ImageDraw.Draw(minor_roads)
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
            if tags['highway'] in MAJOR_ROADS:
                dm.line(pts,fill=1,width=max(2,round(widths[tags['highway']]/DX)),joint='curve')
            else:
                dminor.line(pts,fill=1,width=2,joint='curve')
            counts['roads']+=1
            counts['road_links']+=int(tags['highway'].endswith('_link'))
    osm_buildings=np.array(buildings,dtype=bool)
    supplement_path=ROOT/'data/cusco_buildings_ms.geojson.gz'
    supplement=json.loads(gzip.decompress(supplement_path.read_bytes()))
    for feature in supplement['features']:
        geom=feature['geometry']
        polygons=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        for polygon in polygons:
            # Union each footprint separately so a courtyard cannot erase an
            # existing OSM building or a neighbouring supplemental footprint.
            rings=[[xy({'lon':lon,'lat':lat}) for lon,lat in ring] for ring in polygon]
            if len(rings)==1:
                db.polygon(rings[0],fill=1)
            else:
                mask=Image.new('1',(NX,NY)); draw=ImageDraw.Draw(mask)
                draw.polygon(rings[0],fill=1)
                for ring in rings[1:]:draw.polygon(ring,fill=0)
                buildings.paste(1,mask=mask)
    report['supplemental_buildings']=json.loads((ROOT/'data/cusco_buildings_ms.json').read_text())
    assert report['supplemental_buildings']['crop_sha256']==hashlib.sha256(supplement_path.read_bytes()).hexdigest()
    assert report['supplemental_buildings']['osm_sha256']==hashlib.sha256((ROOT/'data/cusco_osm.json').read_bytes()).hexdigest()
    buildings=Image.fromarray(np.array(buildings,dtype=bool))
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
    r=np.array(roads,dtype=bool); g=np.array(green,dtype=bool)
    raw_buildings=b.copy()
    air=np.array(airport,dtype=bool)
    major=np.array(main_roads,dtype=bool)
    original_roads=r.copy()
    r=prioritize_buildings(b,r,major,np.array(minor_roads,dtype=bool))
    b=group_buildings(b,r|air)
    satellite_green=landcover()
    mat=np.zeros((NY,NX),np.uint8)
    mat[g|satellite_green]=3; mat[b]=2; mat[r|air]=1
    mat[:math.ceil(SAMPLING_APRON/DY)]=0
    mat[[0,-1],:]=0; mat[:,[0,-1]]=0
    # Remove isolated pixel specks that would be below nozzle width.
    for k in (3,):
        lab,n=ndi.label(mat==k)
        sizes=np.bincount(lab.ravel()); keep=sizes>=16; keep[0]=False
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
    protected=major|air
    protected[:math.ceil(SAMPLING_APRON/DY)]=False
    protected[[0,-1],:]=False; protected[:,[0,-1]]=False
    assert np.all(mat[protected]==1), 'Main road or airport was overwritten'
    report['road_topology'].update({'major_roads_and_airport_preserved':True,
      'minor_road_cells_yielded_to_buildings':int((original_roads&~r&~air).sum()),
      'minor_road_core_width_mm':2*DX,
      'note':'Minor-road shoulders yield to buildings; a two-cell mapped core remains. All main-road and airport cells remain protected.'})
    report['osm']=counts
    report['airport_source_timestamp']=airport_data['osm3s']['timestamp_osm_base']
    report['feature_relief_mm']={'building_roof_offset':BUILDING_RISE,
      'road_offset':ROAD_RISE,'airport_offset':AIRPORT_RISE,
      'note':'Buildings have horizontal roofs and vertical walls; only road relief is blended.'}
    interior=np.arange(NY)[:,None]*DY>=SAMPLING_APRON
    report['building_density']={'source_raster_area_mm2':float((raw_buildings&interior).sum()*DX*DY),
      'supplemental_new_raster_area_mm2':float((raw_buildings&~osm_buildings&interior).sum()*DX*DY),
      'source_raster_area_overwritten_by_roads_percent':float(100*(raw_buildings&(r|air)&interior).sum()/(raw_buildings&interior).sum()),
      'final_building_area_mm2':float(((mat==2)&interior).sum()*DX*DY),
      'final_building_components':int(ndi.label((mat==2)&interior)[1]),
      'road_width_mm_by_class':{k:round(v/DX)*DX for k,v in ROAD_WIDTHS.items()}}
    report['airport_cells']=int((air & (mat==1)).sum())
    report['material_cells']=[int((mat==i).sum()) for i in range(4)]
    return mat,air

def surface_heights(z,mat,airport):
    center=(z[:-1,:-1]+z[1:,:-1]+z[:-1,1:]+z[1:,1:])/4
    street_rise=np.where(airport,AIRPORT_RISE,ROAD_RISE)
    # Vegetation is a surface colour, without raising entire mountainsides.
    target=center+np.where(mat==1,street_rise,0)
    extra=target-center
    ev=np.zeros_like(z); cnt=np.zeros_like(z)
    for dj,di in [(0,0),(1,0),(0,1),(1,1)]:
        ev[dj:dj+NY,di:di+NX]+=extra
        cnt[dj:dj+NY,di:di+NX]+=1
    upper=z+ev/cnt
    lower=z-INLAY_DEPTH
    return upper,lower

def building_roof_heights(ground,mat):
    """Flat caps above each road-separated block, including boundary vertices."""
    labels,n=ndi.label(mat==2)
    corner_max=np.maximum.reduce([ground[:-1,:-1],ground[1:,:-1],
                                  ground[:-1,1:],ground[1:,1:]])
    areas=np.bincount(labels.ravel())*DX*DY
    rises=np.where(areas<1.,.48,np.where(areas<4.,.64,.80))
    peaks=ndi.maximum(corner_max,labels,np.arange(n+1))+rises
    peaks[0]=0
    caps=peaks[labels]
    roofs=ground.copy()
    for dj,di in [(0,0),(1,0),(0,1),(1,1)]:
        target=roofs[dj:dj+mat.shape[0],di:di+mat.shape[1]]
        np.maximum(target,caps,out=target)
    errors=np.maximum.reduce([abs(roofs[:-1,:-1]-caps),abs(roofs[1:,:-1]-caps),
                              abs(roofs[:-1,1:]-caps),abs(roofs[1:,1:]-caps)])
    assert not n or errors[mat==2].max()<1e-9, 'Non-flat building roof or diagonal building contact'
    report['building_roofs']={'components':int(n),'flat_roof_max_error_mm':float(errors[mat==2].max()) if n else 0.,
      'wall_orientation':'vertical','minimum_rise_above_block_mm':BUILDING_RISE,
      'schematic_height_tiers_mm':[.48,.64,.80],
      'tier_rule':'group footprint area <1, <4, >=4 mm2; not measured building heights',
      'tier_counts':{str(h):int((rises[1:]==h).sum()) for h in (.48,.64,.80)}}
    return roofs

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

def glyph_shape(text,width,height):
    path=TextPath((0,0),text,size=12,prop=FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    shape=Polygon()
    for contour in path.to_polygons():
        poly=Polygon(contour)
        if poly.is_valid and poly.area>0: shape=shape.symmetric_difference(poly)
    xmin,ymin,xmax,ymax=shape.bounds
    shape=translate(shape,-xmin,-ymin)
    return scale(shape,width/(xmax-xmin),height/(ymax-ymin),origin=(0,0))

def extruded_shape(shape,depth):
    solids=[]
    for p in shape.geoms if hasattr(shape,'geoms') else [shape]:
        mesh=trimesh.creation.extrude_polygon(p,depth,engine='earcut')
        solids.append(md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32))))
    return md.Manifold.batch_boolean(solids,md.OpType.Add)

def information_surface(x,y,upper,lower,mat):
    """A small top-facing card in the nearest feature-free corner area."""
    width,height=38.,18.
    protected=np.isin(mat,[1,2])
    integral=np.pad(protected.cumsum(0).cumsum(1),((1,0),(1,0)))
    candidates=[]
    grid_y=y[:,0]
    for left in range(3,int(SIZE-width-2),2):
        for bottom in range(3,int(SIZE-height-2),2):
            i0=max(0,int((left-.6)/DX));i1=min(mat.shape[1],math.ceil((left+width+.6)/DX))
            j0=max(0,np.searchsorted(grid_y,bottom-.6)-1)
            j1=min(mat.shape[0],np.searchsorted(grid_y,bottom+height+.6)+1)
            count=integral[j1,i1]-integral[j0,i1]-integral[j1,i0]+integral[j0,i0]
            if count==0:
                corner_distance=min(left,SIZE-width-left)**2+min(bottom,SIZE-height-bottom)**2
                candidates.append((corner_distance,left,bottom,i0,i1,j0,j1))
    assert candidates, 'No feature-free information-card location'
    _,left,bottom,i0,i1,j0,j1=min(candidates)
    # Brown landing, planar through every glyph; smooth only its outer 0.4-mm rim.
    mat[j0:j1,i0:i1]=0
    distance=np.maximum.reduce([left-x,x-left-width,bottom-y,y-bottom-height,np.zeros_like(x)])
    core=distance==0
    weight=np.clip(1-distance/.4,0,1);weight=weight*weight*(3-2*weight)
    level=round(float(np.median(upper[core]))/.16)*.16
    upper[:]=upper*(1-weight)+level*weight
    lower[:]=lower*(1-weight)+(level-INLAY_DEPTH)*weight
    report['lettering_surface']={'flat_core_xy_mm':[left,bottom,left+width,bottom+height],
      'plane_z_mm':level,'transition_mm':.4,'mapped_features_covered':0,
      'location_rule':'nearest corner with no mapped roads or buildings, including transition margin',
      'planarity_error_mm':float(np.ptp(upper[core]))}
    report['pins']={'count':0,'landmark_rings':0}
    return left,bottom,level

def information_shape(left,bottom):
    elements=[]
    lines=[('Cusco',2,12.1,23,3.8),('Scale 1:100 000',2,8.7,27,2.1),
           ('3200–4430 m',2,5.3,27,2.3),('above sea level',2,2.2,24,1.9)]
    for text,xx,yy,width,height in lines:
        elements.append(translate(glyph_shape(text,width,height),left+xx,bottom+yy))
    # Arrow direction is +Y: geographic north in the terrain projection.
    arrow=Polygon([(32.2,7),(32.2,11),(30.8,10.2),(32.6,13.2),
                   (34.4,10.2),(33,11),(33,7)])
    elements.append(translate(arrow,left,bottom))
    elements.append(translate(glyph_shape('N',2.5,2.3),left+31.35,bottom+14.1))
    # 1 km at 1:100,000, integrated with the card rather than the sidewall.
    from shapely.geometry import box
    elements.extend([box(left+27,bottom+1,left+37,bottom+1.48),
                     box(left+27,bottom+.7,left+27.48,bottom+1.8),
                     box(left+36.52,bottom+.7,left+37,bottom+1.8)])
    elements.append(translate(glyph_shape('1 km',8,1.6),left+28,bottom+2.2))
    shape=elements[0]
    for element in elements[1:]:shape=shape.union(element)
    report['scale']={'horizontal_denominator':100000,'bar_length_mm':10,'bar_distance_km':1,'bar_label':'1 km',
      'vertical_exaggeration':1.6,'card_text':[line[0] for line in lines],
      'elevation_range_rounded_m':[3200,4430],'elevation_reference':'above sea level',
      'north_direction':'positive model Y'}
    return shape

def information_solid(left,bottom,level):
    shape=information_shape(left,bottom)
    solid=extruded_shape(shape,LABEL_DEPTH+LABEL_RISE).translate((0,0,level-LABEL_DEPTH))
    report['lettering']={'text':'Cusco','orientation':'horizontal XY on internal terrain card',
      'raised_mm':LABEL_RISE,'embedded_mm':LABEL_DEPTH,'glyph_height_mm':3.8,'glyph_width_mm':23,
      'mapped_features_covered':0,'bounds':list(solid.bounding_box())}
    return solid

def as_mesh(solid):
    m=solid.to_mesh()
    return trimesh.Trimesh(np.asarray(m.vert_properties)[:,:3],np.asarray(m.tri_verts),process=False)

def joined_body(mesh):
    """Check face connectivity in one sparse pass, discarding zero-volume debris."""
    adjacency=mesh.face_adjacency
    graph=coo_matrix((np.ones(len(adjacency),dtype=bool),adjacency.T),
                     shape=(len(mesh.faces),len(mesh.faces)))
    count,labels=connected_components(graph,directed=False)
    triangles=mesh.triangles-mesh.bounds.mean(axis=0)
    signed=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2]))/6
    volumes=np.bincount(labels,weights=signed,minlength=count)
    # Float32 STL interfaces can leave closed numerical sheets. The largest
    # allowed residual is many orders below a printable 0.16-mm layer feature.
    tolerance=1e-5
    keep=np.abs(volumes)>tolerance
    report['boolean_zero_volume_fragments_removed']=int((~keep).sum())
    report['boolean_numerical_residuals']={'per_component_tolerance_mm3':tolerance,
      'max_removed_volume_mm3':float(np.max(np.abs(volumes[~keep]),initial=0)),
      'total_removed_absolute_volume_mm3':float(np.abs(volumes[~keep]).sum())}
    assert np.abs(volumes[~keep]).sum()<.01, 'Excessive boolean residual volume'
    report['connected_components']=int(keep.sum())
    assert keep.sum()==1, f'{keep.sum()} detached pieces'
    mesh.update_faces(keep[labels]); mesh.remove_unreferenced_vertices()
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
    return mesh

def write_3mf(meshes):
    xml=['<?xml version="1.0" encoding="UTF-8"?>',
      '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
      '<metadata name="Title">Cusco - 4 colour terrain</metadata>',
      '<metadata name="BambuStudio:3mfVersion">1</metadata>', '<resources>', '<basematerials id="10">']
    for name,col in zip(NAMES,COLORS): xml.append(f'<base name="{name}" displaycolor="{col}FF"/>')
    xml.append('</basematerials>')
    for i,mesh in enumerate(meshes,1):
        xml.append(f'<object id="{i}" type="model" name="{NAMES[i-1]}" pid="10" pindex="{i-1}"><mesh><vertices>')
        # Nine significant digits round-trip the exported STL's float32 values.
        xml.extend('<vertex x="%.9g" y="%.9g" z="%.9g"/>'%tuple(v) for v in mesh.vertices)
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
    left,bottom,label_level=information_surface(x,y,upper,lower,mat)
    roofs=building_roof_heights(upper,mat)
    solids=[]
    for i in range(4):
        print('Building watertight solid',NAMES[i],flush=True)
        solids.append(solid_for_material(i,x,y,roofs if i==2 else upper,lower,mat))
    print('Adding top-facing information card with integrated north arrow...',flush=True)
    label=information_solid(left,bottom,label_level)
    solids[0]=solids[0]-label
    solids[1]=solids[1]+label
    print('Simplifying coplanar mesh detail...',flush=True)
    # Shared terrain/inlay surfaces must stay identical across materials. A
    # zero-tolerance simplification removes only coplanar edges at interfaces.
    solids=[solid.simplify(MESH_TOLERANCE) for solid in solids]
    report['parts']=[]; meshes=[]
    for i,solid in enumerate(solids):
        assert solid.status()==md.Error.NoError
        mesh=as_mesh(solid)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        mesh.export(OUT/f'{NAMES[i]}.stl')
        meshes.append(mesh)
        report['parts'].append({'name':NAMES[i],'watertight':bool(mesh.is_watertight),
          'winding_consistent':bool(mesh.is_winding_consistent),'volume_mm3':float(mesh.volume),'triangles':len(mesh.faces)})
    # Boolean construction retains large native allocation pools. Start the
    # validation phase fresh so the finer map fits in workstation memory.
    stage={'report':report,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'stl_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest()
                    for name in (f'{n}.stl' for n in NAMES)}}
    (OUT/'geometry_stage.json').write_text(json.dumps(stage,indent=2))
    print('Restarting with exported meshes for bounded-memory validation...',flush=True)
    os.execv(sys.executable,[sys.executable,str(Path(__file__).resolve()),'--validate-exports'])

def validate_exports():
    stage=json.loads((OUT/'geometry_stage.json').read_text())
    assert stage['generator_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'Generator changed since mesh export'
    report.clear(); report.update(stage['report'])
    solids=[]; meshes=[]
    for name in NAMES:
        path=OUT/f'{name}.stl'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==stage['stl_sha256'][path.name], 'Stale or modified mesh'
        mesh=trimesh.load_mesh(path,process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
        meshes.append(mesh)
        solids.append(md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),
                                         np.asarray(mesh.faces,dtype=np.uint32))))
        assert solids[-1].status()==md.Error.NoError
    print('Exporting assembled 3MF from checked mesh files...',flush=True)
    write_3mf(meshes)
    del meshes,mesh
    print('Checking intersections and joined solid...',flush=True)
    overlaps=[]
    for i in range(4):
        for j in range(i+1,4):
            print('Checking material pair',i+1,j+1,flush=True)
            v=abs((solids[i]^solids[j]).volume())
            assert v<.02,(i,j,v)
            overlaps.append({'parts':[i+1,j+1],'intersection_mm3':v})
    print('Joining all four materials...',flush=True)
    whole=md.Manifold.batch_boolean(solids,md.OpType.Add)
    full=as_mesh(whole)
    print('Checking joined mesh connectivity...',flush=True)
    full=joined_body(full)
    whole=md.Manifold(md.Mesh(np.asarray(full.vertices,dtype=np.float32),
                             np.asarray(full.faces,dtype=np.uint32)))
    assert whole.status()==md.Error.NoError
    # Only the single-colour union is simplified with a nonzero tolerance.
    # Remove sub-micron coincident edges before STL loses indexed topology.
    whole=whole.simplify(.001)
    full=as_mesh(whole)
    report['monochrome_simplification_tolerance_mm']=.001
    full.export(OUT/'Cusco_einfarbig.stl')
    roundtrip=trimesh.load_mesh(OUT/'Cusco_einfarbig.stl',process=True)
    assert roundtrip.is_watertight and roundtrip.is_winding_consistent
    report['monochrome_stl_roundtrip_watertight']=True
    del roundtrip
    report['overall_bounds_mm']=full.bounds.tolist()
    report['dimensions_mm']=full.extents.tolist()
    report['pairwise_intersections']=overlaps
    print('Checking every 0.16 mm horizontal section...',flush=True)
    levels=np.arange(.08,full.bounds[1,2],.16)
    areas=[whole.slice(float(h)).area() for h in levels]
    assert all(a>0 for a in areas)
    report['cross_section_checks']={'count':len(areas),'all_nonempty':True,'min_area_mm2':min(areas)}
    del whole,full,solids
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'dimensions':report['dimensions_mm'],'components':report['connected_components'],'label':LABEL},indent=2),flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['--validate-exports']:
        validate_exports()
    elif len(sys.argv)==1:
        main()
    else:
        raise SystemExit('Usage: build_print_model.py [--validate-exports]')
