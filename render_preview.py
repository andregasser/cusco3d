import bpy, math
from mathutils import Vector

stl = "/home/andre/projects/cusco3d/output/cusco_terrain_150mm.stl"
png = "/home/andre/projects/cusco3d/output/cusco_terrain_preview.png"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.stl_import(filepath=stl)
obj = bpy.context.selected_objects[0]
obj.name = "Cusco terrain relief"

mat = bpy.data.materials.new("warm terracotta PLA")
mat.diffuse_color = (0.55, 0.16, 0.055, 1.0)
mat.metallic = 0.0
mat.roughness = 0.78
obj.data.materials.append(mat)

obj.location -= Vector((75, 75, 0))

def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()

bpy.ops.object.camera_add(location=(205, -235, 195))
cam = bpy.context.object
point_camera(cam, (0, 0, 16))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 215
bpy.context.scene.camera = cam

bpy.ops.object.light_add(type='AREA', location=(-75, -90, 230))
key = bpy.context.object
key.data.energy = 1100
key.data.shape = 'DISK'
key.data.size = 150
point_camera(key, (0, 0, 0))
bpy.ops.object.light_add(type='AREA', location=(170, 100, 100))
fill = bpy.context.object
fill.data.energy = 500
fill.data.size = 120
point_camera(fill, (0, 0, 10))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = png
scene.render.film_transparent = False
scene.world.color = (0.035, 0.05, 0.07)
scene.view_settings.look = 'AgX - Medium High Contrast'
bpy.ops.wm.save_as_mainfile(filepath="/home/andre/projects/cusco3d/output/cusco_terrain_preview.blend")
bpy.ops.render.render(write_still=True)
