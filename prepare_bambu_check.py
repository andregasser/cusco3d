"""Flatten official installed Bambu profiles for a reproducible local slice check."""
from pathlib import Path
import json

P=Path('/tmp/squashfs-root/resources/profiles/BBL')
OUT=Path(__file__).resolve().parent/'output/print_v2/check'
OUT.mkdir(exist_ok=True)
profiles={}
for p in P.rglob('*.json'):
    d=json.loads(p.read_text())
    if isinstance(d,dict) and 'name' in d: profiles[d['name']]=d

def resolve(name):
    d=profiles[name]
    out=resolve(d['inherits']) if d.get('inherits') else {}
    for inc in d.get('include',[]): out.update(resolve(inc))
    out.update({k:v for k,v in d.items() if k not in {'include','inherits'}})
    return out

machine=resolve('Bambu Lab P1S 0.4 nozzle')
process=resolve('0.16mm Optimal @BBL X1C')
process.update({'name':'Cusco 0.16mm P1S','wall_loops':'3','wall_generator':'arachne','sparse_infill_density':'12%',
    'sparse_infill_pattern':'gyroid','top_shell_layers':'5','bottom_shell_layers':'4',
    'flush_into_infill':'1','infill_combination':'1',
    'enable_support':'0','brim_type':'no_brim','prime_tower_width':'25',
    'prime_tower_brim_width':'1','prime_tower_rib_wall':'0','prime_tower_rib_width':'0',
    'wipe_tower_x':['226'],'wipe_tower_y':['110'],
    'outer_wall_speed':['60','60'],'top_surface_speed':['70','70']})
machine['curr_bed_type']='Textured PEI Plate'
for name,d in [('machine',machine),('process',process)]:
    (OUT/f'{name}.json').write_text(json.dumps(d,indent=2))
colors=json.loads((OUT.parent/'validation.json').read_text())['colors'].values()
for i,color in enumerate(colors,1):
    d=resolve('Generic PLA @BBL P1P')
    d['filament_colour']=[color]; d['name']=f'Cusco PLA {i}'
    d['filament_settings_id']=[d['name']]
    (OUT/f'filament{i}.json').write_text(json.dumps(d,indent=2))
