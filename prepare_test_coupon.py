"""Export a 40 mm city/hillside coupon from the actual four print solids."""
import hashlib,json,zipfile
from pathlib import Path
import numpy as np
import manifold3d as md
import trimesh
import build_print_model as model

def main():
    out=model.OUT
    bounds=[70.,90.,110.,130.]
    clip=md.Manifold.cube((40,40,40)).translate((bounds[0],bounds[1],0))
    solids=[]; meshes=[]
    for name in model.NAMES:
        mesh=trimesh.load_mesh(out/f'{name}.stl',process=True)
        solid=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
        clipped=(solid^clip).translate((-bounds[0],-bounds[1],0))
        assert clipped.status()==md.Error.NoError and clipped.volume()>0
        mesh=model.as_mesh(clipped)
        assert mesh.is_watertight and mesh.is_winding_consistent
        solids.append(clipped);meshes.append(mesh)
    union=md.Manifold.batch_boolean(solids,md.OpType.Add)
    components=[c for c in union.decompose() if c.volume()>1e-5]
    assert len(components)==1
    coupon_dir=out/'test_coupon'
    coupon_dir.mkdir(exist_ok=True)
    model.OUT=coupon_dir
    model.write_3mf(meshes)
    model.OUT=out
    (coupon_dir/'Cusco_AMS_4_Farben.3mf').replace(out/'Cusco_Testdruck_40mm.3mf')
    report={'crop_xy_mm':bounds,'size_xy_mm':[40,40],'scale_unchanged':True,
      'features':['dense city','hillside','minor roads'],
      'connected_components':len(components),'watertight_parts':4,
      'source_stl_sha256':{n:hashlib.sha256((out/f'{n}.stl').read_bytes()).hexdigest() for n in model.NAMES}}
    (out/'test_coupon_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
