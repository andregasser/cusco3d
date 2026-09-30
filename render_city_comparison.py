"""Render both city variants with exactly the same camera and lighting."""
from pathlib import Path
import bpy
from mathutils import Vector

OUT=Path(__file__).resolve().parent/'output/print_v2'
sources=[(OUT/'before_dense_city/Cusco_Render.blend','Cusco_Stadt_Vorher.png'),
         (OUT/'Cusco_Render.blend','Cusco_Stadt.png')]
for source,name in sources:
    if not source.exists():
        if name=='Cusco_Stadt_Vorher.png' and (OUT/name).exists():
            continue  # The historical rendering is checked in, the old scene is local.
        raise FileNotFoundError(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    cam=scene.camera
    target=Vector((-.006,.001,.008))
    cam.location=target+Vector((.018,-.047,.056))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.064
    cam.data.clip_start=.001
    scene.render.resolution_x=1600
    scene.render.resolution_y=1100
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
