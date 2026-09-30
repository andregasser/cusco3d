"""Actual mesh comparison at the three previously sparse city quarters."""
from pathlib import Path
import math
import bpy
from mathutils import Vector

OUT=Path(__file__).resolve().parent/'output/print_v2'
LAT,LON=-13.53195,-71.96746
DLAT=20/111.32; DLON=20/(111.32*math.cos(math.radians(LAT)))
ZONES=[('Nordwest',-13.513037074,-71.996794995),
       ('Suedwest',-13.541610351,-71.986891649),
       ('Flughafenumfeld',-13.535798322,-71.940185508)]
for prefix,source in [('Vorher',OUT/'before_building_data/Cusco_Render.blend'),
                       ('Jetzt',OUT/'Cusco_Render.blend')]:
    if not source.exists():
        if prefix=='Vorher' and all((OUT/f'Cusco_{name}_Vorher.png').exists() for name,_,_ in ZONES):
            continue
        raise FileNotFoundError(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    cam=scene.camera
    for name,lat,lon in ZONES:
        target=Vector(((lon-LON)/DLON*.2,(lat-LAT)/DLAT*.2,.010))
        cam.location=target+Vector((.009,-.027,.032))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=.034; cam.data.clip_start=.001
        scene.render.resolution_x=1200; scene.render.resolution_y=1000
        scene.render.filepath=str(OUT/f'Cusco_{name}_{prefix}.png')
        bpy.ops.render.render(write_still=True)
