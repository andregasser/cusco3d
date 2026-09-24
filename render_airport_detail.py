"""Airport and adjacent city blocks from the actual saved STL scene."""
from pathlib import Path
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent / 'output/print_v2'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'Cusco_Render.blend'))
scene = bpy.context.scene
cam = scene.camera
cam.data.clip_start = .001
# Runway midpoint in the model's existing Blender coordinate system.
target = Vector((.031, -.004, .006))
cam.location = (.066, -.074, .115)
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = .072
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.filepath = str(OUT / 'Cusco_Flughafen.png')
bpy.ops.render.render(write_still=True)
