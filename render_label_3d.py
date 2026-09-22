from PIL import Image, ImageDraw

S=8; ox=100; front=470; depth=55; cell=1.2; gap=1.5
im=Image.new('RGB',(1400,650),(18,25,32)); d=ImageDraw.Draw(im)
def q(x,z,y=0):
    return (int(ox+x*S+y*0.45), int(front-z*S-y*0.30))

d.polygon([q(0,0),q(150,0),q(150,4),q(0,4)],fill=(83,43,28),outline=(190,111,57))
d.polygon([q(0,4),q(150,4),q(150,4,depth),q(0,4,depth)],fill=(126,65,32),outline=(210,126,67))
d.polygon([q(150,0),q(150,4),q(150,4,depth),q(150,0,depth)],fill=(56,31,24))

font={'C':["1111","1000","1000","1000","1000","1000","1111"], 'U':["1001","1001","1001","1001","1001","1001","0110"], 'S':["1111","1000","1000","1110","0001","0001","1110"], 'O':["0110","1001","1001","1001","1001","1001","0110"]}
word='CUSCO'; width=sum(4*cell for _ in word)+gap*4; x=(150-width)/2
for ch in word:
    for row,line in enumerate(font[ch]):
        for col,on in enumerate(line):
            if on == '1':
                x0=x+col*cell; x1=x0+cell; z0=.35+(6-row)*cell; z1=z0+cell
                d.polygon([q(x0,z0,-1),q(x1,z0,-1),q(x1,z1,-1),q(x0,z1,-1)],fill=(225,139,72))
                d.polygon([q(x0,z1,-1),q(x1,z1,-1),q(x1,z1,5),q(x0,z1,5)],fill=(255,182,97))
    x += 4*cell+gap
d.text((ox,560),'CUSCO · erhabene Reliefschrift auf der vorderen Sockelwand',fill=(205,214,220))
im.save('output/cusco_label_3d_render.png')
