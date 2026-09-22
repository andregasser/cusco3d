from pathlib import Path
from PIL import Image, ImageDraw
from make_cusco_terrain import CITY_LAT, CITY_LON, sample_mosaic, read_mosaic
import math, json

N = 360
SIZE = 150.0
tiles = read_mosaic(Path('data'))
half_lat = 20 / 2 / 111.32
half_lon = 20 / 2 / (111.32 * math.cos(math.radians(CITY_LAT)))
south, north = CITY_LAT - half_lat, CITY_LAT + half_lat
west, east = CITY_LON - half_lon, CITY_LON + half_lon
h = [[sample_mosaic(tiles, south + (north-south)*j/(N-1), west + (east-west)*i/(N-1)) for i in range(N)] for j in range(N)]
lo, hi = min(map(min, h)), max(map(max, h))
im = Image.new('RGB', (1000, 820), (13, 22, 31))
d = ImageDraw.Draw(im)

def z(lat, lon):
    return (sample_mosaic(tiles, lat, lon)-lo)*0.018 + 4

def color(v, shade):
    t = (v-lo)/(hi-lo)
    return (int(105 + 105*t*shade), int(48 + 83*t*shade), int(25 + 35*t*shade))

def proj(i, j, z):
    x = 120 + i*3.75 - j*1.85
    y = 135 + i*0.88 + j*0.73 - z*1.7
    return (int(x), int(y))

def xy(lat, lon):
    return ((lon-west)/(east-west)*(N-1), (lat-south)/(north-south)*(N-1))

# Visible front face of the real 4 mm print base.
d.polygon([proj(0,N-1,0), proj(N-1,N-1,0), proj(N-1,N-1,4), proj(0,N-1,4)], fill=(62, 30, 20))
d.polygon([proj(N-1,0,0), proj(N-1,N-1,0), proj(N-1,N-1,4), proj(N-1,0,4)], fill=(47, 25, 19))

for j in range(N-2, -1, -1):
    for i in range(N-1):
        z00 = (h[j][i]-lo)*0.018 + 4
        z10 = (h[j][i+1]-lo)*0.018 + 4
        z01 = (h[j+1][i]-lo)*0.018 + 4
        z11 = (h[j+1][i+1]-lo)*0.018 + 4
        shade = max(0.55, min(1.15, 0.78 + ((h[j][i+1]-h[j][i]) - (h[j+1][i]-h[j][i]))/500))
        poly = [proj(i,j,z00), proj(i+1,j,z10), proj(i+1,j+1,z11), proj(i,j+1,z01)]
        d.polygon(poly, fill=color((h[j][i]+h[j][i+1]+h[j+1][i]+h[j+1][i+1])/4, shade))

green=json.load(open('data/cusco_green.json'))['elements']
for e in green:
    geo=e.get('geometry',[])
    if e['type']=='way' and len(geo)>=3 and all(south <= p['lat'] <= north and west <= p['lon'] <= east for p in geo):
        pts=[proj(*xy(p['lat'],p['lon']),z(p['lat'],p['lon'])+.15) for p in geo]
        d.polygon(pts, fill=(58,105,54), outline=(89,135,70))

osm=json.load(open('data/cusco_osm.json'))['elements']
for e in osm:
    tags=e.get('tags',{}); geo=e.get('geometry',[])
    if e['type']!='way' or len(geo)<2: continue
    if not all(south <= p['lat'] <= north and west <= p['lon'] <= east for p in geo): continue
    pts=[proj(*xy(p['lat'],p['lon']), z(p['lat'],p['lon']) if 'z' in globals() else 10) for p in geo]
    if 'highway' in tags and tags['highway'] in {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service'}:
        d.line(pts, fill=(54, 55, 52), width=2, joint='curve')
    elif 'building' in tags and len(pts)>=3:
        d.polygon(pts, fill=(151, 72, 43), outline=(204, 126, 76))

for e in green:
    if e['type']=='node' and e.get('tags',{}).get('natural')=='tree':
        x,y=xy(e['lat'],e['lon']); px,py=proj(x,y,z(e['lat'],e['lon'])+2.0)
        d.polygon([(px,py-5),(px-3,py+2),(px+3,py+2)], fill=(57,112,49), outline=(104,151,77))

# The label is drawn on the same front plane as the printable raised letters.
font={'C':["1111","1000","1000","1000","1000","1000","1111"],
      'U':["1001","1001","1001","1001","1001","1001","0110"],
      'S':["1111","1000","1000","1110","0001","0001","1110"],
      'O':["0110","1001","1001","1001","1001","1001","0110"]}
cell=.5; gap=.8; word='CUSCO'; width=sum(len(font[ch][0])*cell for ch in word)+gap*(len(word)-1)
xcur=(SIZE-width)/2
for ch in word:
    for row,line in enumerate(font[ch]):
        for col,on in enumerate(line):
            if on:
                x0=(xcur+col*cell)/SIZE*(N-1); x1=(xcur+(col+1)*cell)/SIZE*(N-1)
                z0=.35+(6-row)*cell; z1=z0+cell
                jf=(N-1)+.65/SIZE*(N-1)
                d.polygon([proj(x0,jf,z0),proj(x1,jf,z0),proj(x1,jf,z1),proj(x0,jf,z1)], fill=(206,126,70))
    xcur += len(font[ch][0])*cell+gap
im.save('output/cusco_terrain_preview.png')
