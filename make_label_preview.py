from PIL import Image, ImageDraw, ImageFont

S=7; ox=100; oy=110; im=Image.new('RGB',(1400,620),(18,25,32)); d=ImageDraw.Draw(im)
# Top view: the plaque and lettering are horizontal, not vertical.
d.rectangle((ox,oy,ox+50*S,oy+14*S),fill=(126,65,32),outline=(210,126,67),width=2)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',82)
d.text((ox+55,oy+18),'CUSCO',font=font,fill=(232,145,67),stroke_width=1,stroke_fill=(255,190,105))
d.text((ox,oy+150),'DRAUFSICHT · flache Randplatte · Reliefhöhe der Schrift: 0,6 mm',fill=(205,214,220))
im.save('output/cusco_label_front_preview.png')
