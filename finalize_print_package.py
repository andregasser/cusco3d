"""Package the native Bambu project only after a successful checked slice."""
from pathlib import Path
import argparse, json, zipfile, io, hashlib, re
import xml.etree.ElementTree as ET
from PIL import Image

OUT=Path(__file__).resolve().parent/'output/print_v2'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check-dir',type=Path,default=OUT/'check')
CHECK=parser.parse_args().check_dir
result=json.loads((CHECK/'result.json').read_text())
assert result['return_code']==0, result
assert len(result.get('sliced_plates',[]))==1 and .15<float(result['layer_height'])<.17, 'Need actual slice result, not an export-only result'
assert result['sliced_plates'][0]['warning_message']=='', result['sliced_plates'][0]['warning_message']
source=CHECK/'Cusco_unsliced.3mf'
assert source.exists(), 'Missing native Bambu export'
target=OUT/'Cusco_P1S_AMS.3mf'
preview=Image.open(OUT/'Cusco_Gesamtansicht.png')
thumbs={}
for name,size in [('Metadata/plate_1.png',512),('Metadata/plate_1_small.png',128)]:
    im=preview.copy(); im.thumbnail((size,size)); buf=io.BytesIO(); im.save(buf,format='PNG'); thumbs[name]=buf.getvalue()

# Deliver an editable project, without a stale machine-specific print payload.
with zipfile.ZipFile(source) as src, zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as dst:
    for name in src.namelist():
        if name in thumbs or '.gcode' in name: continue
        data=src.read(name)
        if name=='Metadata/model_settings.config':
            root=ET.fromstring(data)
            for node in root.findall('.//metadata[@key="gcode_file"]'): node.set('value','')
            data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        dst.writestr(name,data)
    for name,data in thumbs.items():dst.writestr(name,data)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    settings=json.loads(z.read('Metadata/project_settings.config'))
    config=ET.fromstring(z.read('Metadata/model_settings.config'))
    parts=config.findall('object/part')
    assert len(parts)==4
    assert [p.find("metadata[@key='extruder']").attrib['value'] for p in parts]==['1','2','3','4']
    assert settings['printer_model']=='Bambu Lab P1S'
    expected_colors=list(json.loads((OUT/'validation.json').read_text())['colors'].values())
    assert settings['filament_colour']==expected_colors
    assert settings['flush_into_infill']=='1' and settings['infill_combination']=='1'
    assert settings['prime_tower_rib_wall']=='0'
    repairs=[n.attrib for n in config.findall('.//mesh_stat')]
    assert all(int(v)==0 for a in repairs for k,v in a.items() if k!='face_count')

header=[]
with (CHECK/'plate_1.gcode').open() as f:
    for _ in range(14):header.append(next(f).rstrip())
validation=json.loads((OUT/'validation.json').read_text())
validation['bambu_studio']={'version':'02.08.02.61','result':result,
  'four_part_assignment_verified':True,'native_import_mesh_repairs':repairs,
  'gcode_header':header,'project_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
validation['stl_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('0*.stl'))}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
# Keep the standalone print guide; the README now references repository assets.
assert (OUT/'Druckhinweise.md').exists(), 'Missing standalone print guide'
with zipfile.ZipFile(OUT/'Cusco_STL_Alternativ.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.glob('0*.stl')):z.write(p,p.name)
    z.write(OUT/'Druckhinweise.md','Druckhinweise.md')
print('Native Bambu project verified, thumbnails embedded, STL archive ready.')
print('\n'.join(header[:8]))
