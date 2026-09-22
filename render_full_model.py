import struct, math
from PIL import Image, ImageDraw

parts=[('output/cusco_ams_01_terrain_brown.stl',(156,82,35)),('output/cusco_ams_02_roads_asphalt_gray.stl',(54,55,52)),('output/cusco_ams_03_buildings_label_terracotta.stl',(190,88,48)),('output/cusco_ams_04_vegetation_green.stl',(62,122,54))]
cam=(240,-300,220); target=(75,75,18)
def sub(a,b): return tuple(a[i]-b[i] for i in range(3))
def dot(a,b): return sum(a[i]*b[i] for i in range(3))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
    q=math.sqrt(dot(a,a)) or 1; return tuple(v/q for v in a)
forward=norm(sub(target,cam)); right=norm(cross(forward,(0,0,1))); up=cross(right,forward)
def project(v):
    q=sub(v,target); return (600+dot(q,right)*3.2,470-dot(q,up)*3.2,dot(sub(v,cam),forward))

items=[]
for path,base in parts:
    with open(path,'rb') as f:
        f.read(80); count=struct.unpack('<I',f.read(4))[0]
        for _ in range(count):
            f.read(12); tri=[struct.unpack('<3f',f.read(12)) for _ in range(3)]; f.read(2)
            p=[project(v) for v in tri]
            ux,uy,uz=tri[1][0]-tri[0][0],tri[1][1]-tri[0][1],tri[1][2]-tri[0][2]
            vx,vy,vz=tri[2][0]-tri[0][0],tri[2][1]-tri[0][1],tri[2][2]-tri[0][2]
            nn=norm((uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx))
            light=max(.45,min(1.15,.62+.38*abs(nn[2])+.18*max(0,dot(nn,forward))))
            items.append((sum(v[2] for v in p)/3,p,tuple(int(c*light) for c in base)))
items.sort(key=lambda x:x[0],reverse=True)
im=Image.new('RGB',(1200,900),(18,25,32)); d=ImageDraw.Draw(im)
for _,p,col in items:
    d.polygon([(int(x),int(y)) for x,y,_ in p],fill=col)
d.text((42,35),'CUSCO · AMS-Farbansicht',fill=(220,225,228))
d.text((42,62),'Terrain · Asphaltstraßen · Terrakotta-Gebäude · Grünflächen/Vegetation',fill=(166,178,186))
im.save('output/cusco_full_model_render.png')
