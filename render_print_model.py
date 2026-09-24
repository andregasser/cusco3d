"""Actual STL rendering with Blender Cycles on CPU. No reconstructed geometry."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/print_v2'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
validation=json.loads((OUT/'validation.json').read_text())
palette=[c.lstrip('#') for c in validation['colors'].values()]
objects=[]
def linear(c):
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
for i,p in enumerate(sorted(OUT.glob('0*.stl'))):
    bpy.ops.wm.stl_import(filepath=str(p))
    o=bpy.context.object
    o.name=p.stem
    o.scale=(.001,)*3
    o.location=(-.100,-.100,0)
    mat=bpy.data.materials.new(p.stem)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    rgb=tuple(linear(int(palette[i][j:j+2],16)/255) for j in (0,2,4))
    bsdf.inputs['Base Color'].default_value=(*rgb,1)
    bsdf.inputs['Roughness'].default_value=.72
    o.data.materials.clear(); o.data.materials.append(mat)
    objects.append(o)

bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.0002))
floor=bpy.context.object
mat=bpy.data.materials.new('Studio backdrop'); mat.diffuse_color=(.30,.33,.37,1); mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.30,.33,.37,1)
mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
floor.data.materials.append(mat)

def aim(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,power,size):
    bpy.ops.object.light_add(type='AREA',location=location)
    o=bpy.context.object; o.name=name; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; aim(o,(0,0,0))
area('Large key',(-.18,-.22,.40),7,.25)
area('Soft fill',(.30,.1,.28),4,.22)
area('Rim',(-.1,.28,.35),5,.20)
bpy.ops.object.camera_add(location=(.27,-.36,.38))
cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=.31; aim(cam,(0,0,.008))
cam.data.clip_start=.001
scene=bpy.context.scene; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=8
scene.render.resolution_x=1800; scene.render.resolution_y=1600; scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.82,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-1.25
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'Cusco_Gesamtansicht.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Cusco_Render.blend'))
bpy.ops.render.render(write_still=True)
# Close-up of the horizontal lettering on the internal flat terrain surface.
bounds=validation['lettering']['bounds']
target=Vector(((bounds[0]+bounds[3])*.0005-.100,
               (bounds[1]+bounds[4])*.0005-.100,(bounds[2]+bounds[5])*.0005))
cam.location=target+Vector((.005,-.065,.095)); aim(cam,target); cam.data.ortho_scale=.050
scene.render.resolution_x=1600; scene.render.resolution_y=800
scene.render.filepath=str(OUT/'Cusco_Beschriftung.png')
bpy.ops.render.render(write_still=True)
