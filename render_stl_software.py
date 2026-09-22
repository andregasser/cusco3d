import struct, math
from PIL import Image, ImageDraw

path='output/cusco_terrain_with_features.stl'
tris=[]
with open(path,'rb') as f:
    f.read(80); n=struct.unpack('<I',f.read(4))[0]
    for _ in range(n):
        f.read(12); tris.append([struct.unpack('<3f',f.read(12)) for _ in range(3)]); f.read(2)

cam=(235,-285,210); target=(75,75,18)
def sub(a,b): return tuple(a[i]-b[i] for i in range(3))
def dot(a,b): return sum(a[i]*b[i] for i in range(3))
def norm(a):
    l=math.sqrt(dot(a,a)); return tuple(x/l for x in a)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
forward=norm(sub(target,cam)); right=norm(cross(forward,(0,0,1))); up=cross(right,forward)
def project(v):
    q=sub(v,target); return (500+dot(q,right)*3.35,460-dot(q,up)*3.35,dot(sub(v,cam),forward))

items=[]
for tri in tris:
    p=[project(v) for v in tri]
    items.append((sum(v[2] for v in p)/3,p))
items.sort(key=lambda x:x[0])
im=Image.new('RGB',(1000,820),(13,22,31)); d=ImageDraw.Draw(im)
for depth,p in items:
    shade=max(.55,min(1.0,.72+(depth+250)/500))
    d.polygon([(int(x),int(y)) for x,y,_ in p],fill=(int(150*shade),int(72*shade),int(28*shade)))
im.save('output/cusco_terrain_preview.png')
