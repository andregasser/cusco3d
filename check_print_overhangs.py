"""Check actual joined STL sections against the preceding print layer."""
from pathlib import Path
import hashlib,json
import numpy as np
import manifold3d as md
import trimesh

OUT=Path(__file__).resolve().parent/'output/print_v2'

def main():
    path=OUT/'Cusco_einfarbig.stl'
    mesh=trimesh.load_mesh(path,process=True)
    assert mesh.is_watertight and mesh.is_winding_consistent
    solid=md.Manifold(md.Mesh(np.asarray(mesh.vertices,dtype=np.float32),
                              np.asarray(mesh.faces,dtype=np.uint32)))
    assert solid.status()==md.Error.NoError
    # Bambu's 0.20-mm first layer, then 0.16-mm layers, sampled at their centres.
    levels=np.r_[.1,np.arange(.28,mesh.bounds[1,2],.16)]
    previous=None; maximum=0.
    for z in levels:
        current=solid.slice(float(z))
        assert current.area()>0, f'Empty layer at {z} mm'
        if previous is not None:
            # The pin's 45-degree shoulder needs 0.16 mm of lateral growth.
            # A 0.02-mm allowance covers polygon discretisation and STL precision.
            unsupported=(current-previous.offset(.18)).area()
            maximum=max(maximum,unsupported)
            assert unsupported<1e-5, f'Unsupported region at {z}: {unsupported} mm²'
        previous=current
    checks={'section_count':len(levels),'layer_height_mm':.16,
      'allowed_lateral_step_mm':.18,'max_excess_area_mm2':maximum,
      'joined_stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'stl_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('0*.stl'))},
      'note':'Digital section-support check including the pin shoulder; no physical print claim.'}
    report=json.loads((OUT/'validation.json').read_text())
    report['overhang_checks']=checks
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
