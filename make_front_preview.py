from pathlib import Path
from PIL import Image, ImageDraw
from make_cusco_terrain import CITY_LAT, sample_mosaic, read_mosaic
import math

W,H=1200,700; SIZE=150.0; BASE=4.0; S=5.8
tiles=read_mosaic(Path('data')); n=300
half_lat=10/111.32; half_lon=10/(111.32*math.cos(math.radians(CITY_LAT)))
north=CITY_LAT+half_lat; west=-71.96746-half_lon; east=-71.96746+half_lon
def z(x):
    lon=west+(east-west)*x/(n-1)
    return BASE+(sample_mosaic(tiles,north,lon)-2551)*.018
def P(x,zz): return (int(150+x*S),int(585-zz*S))
im=Image.new('RGB',(W,H),(13,22,31)); d=ImageDraw.Draw(im)
d.rectangle((150,585-BASE*S,150+SIZE*S,585),fill=(83,43,28),outline=(155,91,49))
pts=[P(0,BASE)]+[P(SIZE*x/(n-1),z(x)) for x in range(n)]+[P(SIZE,BASE)]
d.polygon(pts,fill=(159,78,34),outline=(213,125,65))
font={'C':["1111","1000","1000","1000","1000","1000","1111"], 'U':["1001","1001","1001","1001","1001","1001","0110"], 'S':["1111","1000","1000","1110","0001","0001","1110"], 'O':["0110","1001","1001","1001","1001","1001","0110"]}
cell=.5; gap=.8; word='CUSCO'; width=sum(len(font[ch][0])*cell for ch in word)+gap*4; xcur=(SIZE-width)/2
for ch in word:
    for row,line in enumerate(font[ch]):
        for col,on in enumerate(line):
            if on:
                x0=xcur+col*cell; x1=x0+cell; z0=.35+(6-row)*cell; z1=z0+cell
                d.rectangle((P(x0,z0)[0],P(0,z1)[1],P(x1,z1)[0],P(0,z0)[1]),fill=(232,145,67),outline=(255,194,111))
    xcur+=len(font[ch][0])*cell+gap
d.text((150,625),'FRONTANSICHT · Sockel mit erhabener Beschriftung „CUSCO“',fill=(190,202,210))
im.save('output/cusco_front_preview.png')
