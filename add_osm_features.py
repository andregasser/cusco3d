"""Add printable OSM roads, buildings and tree cones to the Cusco relief."""
import json, math, struct
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
from make_cusco_terrain import CITY_LAT, CITY_LON, sample_mosaic, read_mosaic

N = 240; SIZE = 150.0; AREA_KM = 20.0; SCALE_Z = 0.018; BASE = 4.0
half_lat = AREA_KM/2/111.32
half_lon = AREA_KM/2/(111.32*math.cos(math.radians(CITY_LAT)))
south,north = CITY_LAT-half_lat,CITY_LAT+half_lat; west,east = CITY_LON-half_lon,CITY_LON+half_lon
tiles=read_mosaic(Path('data'))
sample=[sample_mosaic(tiles,south+(north-south)*j/(N-1),west+(east-west)*i/(N-1)) for j in range(N) for i in range(N)]
low=min(sample)

def xy(lat,lon): return ((lon-west)/(east-west)*SIZE, (lat-south)/(north-south)*SIZE)
def z(lat,lon): return BASE+(sample_mosaic(tiles,lat,lon)-low)*SCALE_Z
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(poly): return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))/2)
def add_box(tris, poly, top_extra):
    if len(poly)<3: return
    bot=[(x,y,z(lat,lon)) for lat,lon,x,y in poly]
    top=[(x,y,zz+top_extra) for (x,y,zz) in bot]
    for i in range(1,len(poly)-1): tris.append((top[0],top[i],top[i+1]))
    for i in range(len(poly)):
        k=(i+1)%len(poly); tris += [(bot[i],bot[k],top[k]),(bot[i],top[k],top[i])]

def cube(tris, x0,x1,y0,y1,z0,z1):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    tris += [(v[0],v[2],v[1]),(v[0],v[3],v[2]),(v[4],v[5],v[6]),(v[4],v[6],v[7]),
            (v[0],v[1],v[5]),(v[0],v[5],v[4]),(v[1],v[2],v[6]),(v[1],v[6],v[5]),
            (v[2],v[3],v[7]),(v[2],v[7],v[6]),(v[3],v[0],v[4]),(v[3],v[4],v[7])]

osm=json.load(open('data/cusco_osm.json'))['elements']; green=json.load(open('data/cusco_green.json'))['elements']
roads=[]; buildings=[]; trees=[]
for e in osm:
    tags=e.get('tags',{}); geo=e.get('geometry',[])
    if e['type']=='way' and 'highway' in tags and len(geo)>1:
        kind=tags['highway']
        if kind in {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service'}:
            line=[(p['lat'],p['lon']) for p in geo]
            if all(south <= lat <= north and west <= lon <= east for lat,lon in line): roads.append((kind,line))
    elif e['type']=='way' and 'building' in tags and len(geo)>=3:
        pl=[(p['lat'],p['lon'],*xy(p['lat'],p['lon'])) for p in geo]; pl=pl[:-1] if pl[0][:2]==pl[-1][:2] else pl
        if len(pl)>=3 and all(south <= p[0] <= north and west <= p[1] <= east for p in pl) and area([(p[2],p[3]) for p in pl])>=0.02: buildings.append((tags,pl))
for e in green:
    if e['type']=='node' and e.get('tags',{}).get('natural')=='tree': trees.append((e['lat'],e['lon']))

def read_base_stl(path):
    result=[]
    with open(path,'rb') as f:
        f.read(80); count=struct.unpack('<I',f.read(4))[0]
        for _ in range(count):
            f.read(12)
            result.append((struct.unpack('<3f',f.read(12)),struct.unpack('<3f',f.read(12)),struct.unpack('<3f',f.read(12))))
            f.read(2)
    return result

terrain_tris=read_base_stl('output/cusco_terrain_150mm.stl')
# Explicit flat print base; this also makes the intended slicer bed orientation unambiguous.
cube(terrain_tris, 0, SIZE, 0, SIZE, 0, BASE)
road_tris=[]; building_tris=[]; vegetation_tris=[]
# roads as raised ribbons
for kind,line in roads:
    width={'motorway':1.0,'trunk':.9,'primary':.8,'secondary':.7,'tertiary':.6}.get(kind,.45)
    for a,b in zip(line,line[1:]):
        ax,ay=xy(*a); bx,by=xy(*b); dx,dy=bx-ax,by-ay; ll=math.hypot(dx,dy)
        if ll<0.02: continue
        px,py=-dy/ll*width/2,dx/ll*width/2
        q=[(a[0],a[1],ax+px,ay+py),(a[0],a[1],ax-px,ay-py),(b[0],b[1],bx-px,by-py),(b[0],b[1],bx+px,by+py)]
        add_box(road_tris,q,0.45)
# selected building footprints, with levels translated to printable height
for tags,pl in buildings:
    levels=tags.get('building:levels','1')
    try: height=min(4.0,max(0.8,float(levels)*0.35))
    except ValueError: height=1.1
    add_box(building_tris,pl,height)
# mapped trees as compact eight-sided cones, minimum dimensions for FDM
for lat,lon in trees:
    x,y=xy(lat,lon); r=.42; zb=z(lat,lon)+.25; apex=(x,y,zb+2.3)
    ring=[(x+r*math.cos(2*math.pi*i/8),y+r*math.sin(2*math.pi*i/8),zb) for i in range(8)]
    for i in range(8): vegetation_tris.append((ring[i],ring[(i+1)%8],apex))
    for i in range(1,7): vegetation_tris.append((ring[0],ring[i+1],ring[i]))
# Flat label plaque near the north-east edge, with a clean sans-serif typeface.
px0,px1,py0,py1=SIZE-50,SIZE-2,SIZE-14,SIZE-2
font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=ImageFont.truetype(font_path,100)
mask=Image.new('1',(500,150)); md=ImageDraw.Draw(mask); md.text((4,-8),'CUSCO',font=font,fill=1,stroke_width=1)
box=mask.getbbox(); mask=mask.crop(box); target_w=43.0; target_h=8.0
for row in range(mask.height):
    col=0
    while col<mask.width:
        while col<mask.width and not mask.getpixel((col,row)): col+=1
        start=col
        while col<mask.width and mask.getpixel((col,row)): col+=1
        if col>start:
            x0=px0+3+(start/mask.width)*target_w; x1=px0+3+(col/mask.width)*target_w
            y0=py0+2+(row/mask.height)*target_h; y1=py0+2+((row+1)/mask.height)*target_h
            cx,cy=(x0+x1)/2,(y0+y1)/2
            local_lat=south+(north-south)*cy/SIZE; local_lon=west+(east-west)*cx/SIZE
            local_z=z(local_lat,local_lon)+.05
            cube(building_tris,x0,x1,y0,y1,local_z,local_z+.6)

def write_stl(out, triangles, title):
  with Path(out).open('wb') as f:
    f.write(title.encode().ljust(80,b' ')[:80]); f.write(struct.pack('<I',len(triangles)))
    for a,b,c in triangles:
        ux,uy,uz=b[0]-a[0],b[1]-a[1],b[2]-a[2]; vx,vy,vz=c[0]-a[0],c[1]-a[1],c[2]-a[2]
        nx,ny,nz=uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx; ll=math.sqrt(nx*nx+ny*ny+nz*nz) or 1
        f.write(struct.pack('<3f',nx/ll,ny/ll,nz/ll)); f.write(struct.pack('<9f',*(a+b+c))); f.write(b'\0\0')

write_stl('output/cusco_ams_01_terrain_brown.stl', terrain_tris, 'Cusco AMS terrain and base brown')
write_stl('output/cusco_ams_02_roads_asphalt_gray.stl', road_tris, 'Cusco AMS roads asphalt gray')
write_stl('output/cusco_ams_03_buildings_label_terracotta.stl', building_tris, 'Cusco AMS buildings and label terracotta')
write_stl('output/cusco_ams_04_vegetation_green.stl', vegetation_tris, 'Cusco AMS vegetation green')
write_stl('output/cusco_terrain_with_features.stl', terrain_tris+road_tris+building_tris+vegetation_tris, 'Cusco terrain with OSM roads buildings vegetation')
print(f'roads={len(roads)}, buildings={len(buildings)}, trees={len(trees)}')
