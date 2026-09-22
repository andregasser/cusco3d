"""Render the README banner from the saved, actual STL scene (Blender CPU)."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
source = ROOT / 'output/print_v2/Cusco_Render.blend'
if not source.exists():
    raise FileNotFoundError('Run render_print_model.py first to create the STL scene.')
bpy.ops.wm.open_mainfile(filepath=str(source))
scene = bpy.context.scene
camera = scene.camera
rotation = camera.rotation_euler.to_quaternion()
right = rotation @ Vector((1, 0, 0))
up = rotation @ Vector((0, 1, 0))
forward = rotation @ Vector((0, 0, -1))
camera.location -= right * .084
camera.data.ortho_scale = .49
camera.data.clip_start = .001
scene.render.resolution_x = 2400
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.cycles.samples = 64
scene.render.filepath = str(ROOT / 'hero.png')

def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*color, 1)
    mat.node_tree.links.new(emission.outputs[0], out.inputs['Surface'])
    return mat

ink = material('Banner ink', (.028, .039, .040))
muted = material('Banner secondary ink', (.10, .13, .13))
font = bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
bold = bpy.data.fonts.load('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')

def text(body, x, y, size, mat=ink, heavy=False):
    curve = bpy.data.curves.new('Hero typography', 'FONT')
    curve.body = body
    curve.font = bold if heavy else font
    curve.size = size
    curve.space_line = 1.35
    obj = bpy.data.objects.new(body, curve)
    scene.collection.objects.link(obj)
    obj.location = camera.location + forward * .10 + right * x + up * y
    obj.rotation_euler = camera.rotation_euler
    curve.materials.append(mat)
    # Graphic overlay only; never add these objects to the printable meshes.
    obj.visible_shadow = False

text('PERU  /  PRINT THE ANDES', -.224, .074, .0062, muted)
text('CUSCO', -.226, .030, .044, heavy=True)
text('Eine Stadt. Ein Relief.\nVier Farben.', -.224, .005, .008)
text('20 × 20 km Landschaft\n200 × 216 mm auf deinem Druckbett', -.224, -.032, .0058, muted)
text('BAMBU LAB P1S  +  AMS', -.224, -.076, .0058, heavy=True)
text('Echtes Mesh-Rendering', -.224, -.088, .0052, muted)
bpy.ops.render.render(write_still=True)
