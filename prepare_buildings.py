"""Crop Microsoft's Cusco tile and retain footprints missing from the OSM source."""
from pathlib import Path
import argparse, gzip, hashlib, json, urllib.request
from shapely.geometry import Polygon, shape, box, mapping
from shapely.strtree import STRtree
from shapely.ops import unary_union
import build_print_model as model

URL='https://bfppub.z5.web.core.windows.net/2026-08-13/global-buildings.geojsonl/RegionName=Peru/quadkey=210031023/part-00142-110f5303-ff85-4c71-a2bf-c6070024fec8.c000.csv.gz'
ROOT=Path(__file__).resolve().parent

def is_duplicate(candidate,existing):
    """Reject majority-overlap matches; remaining raster overlap is unioned later."""
    if not existing or candidate.area<=0:
        return False
    overlap=unary_union([p.intersection(candidate) for p in existing]).area
    return overlap/candidate.area>=.5

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=Path('/tmp/cusco-ms-buildings.geojsonl.gz'))
    archive=parser.parse_args().archive
    if not archive.exists():
        urllib.request.urlretrieve(URL,archive)
    crop=box(model.WEST,model.SOUTH,model.WEST+model.DLON,model.SOUTH+model.DLAT)
    osm=[]
    for e in json.loads((ROOT/'data/cusco_osm.json').read_text())['elements']:
        g=e.get('geometry',[])
        if 'building' not in e.get('tags',{}) or len(g)<4 or g[0]!=g[-1]:
            continue
        p=Polygon([(v['lon'],v['lat']) for v in g])
        if not p.is_valid:p=p.buffer(0)
        if p.intersects(crop):osm.append(p)
    tree=STRtree(osm)
    counts={'tile_features':0,'intersecting_crop':0,'duplicates_rejected':0,
            'small_or_low_confidence_rejected':0,'accepted':0,'accepted_unknown_confidence':0}
    features=[]
    with gzip.open(archive,'rt') as f:
        for line in f:
            feature=json.loads(line); counts['tile_features']+=1
            p=shape(feature['geometry'])
            if not p.intersects(crop):continue
            counts['intersecting_crop']+=1
            if not p.is_valid:p=p.buffer(0)
            p=p.intersection(crop)
            confidence=feature.get('properties',{}).get('confidence',-1)
            area_m2=p.area/model.DLON/model.DLAT*model.AREA**2
            if area_m2<12 or (confidence>=0 and confidence<.65):
                counts['small_or_low_confidence_rejected']+=1;continue
            candidates=[osm[i] for i in tree.query(p,predicate='intersects')]
            if is_duplicate(p,candidates):
                counts['duplicates_rejected']+=1;continue
            counts['accepted']+=1
            counts['accepted_unknown_confidence']+=int(confidence<0)
            features.append({'type':'Feature','geometry':mapping(p),
                             'properties':{'source':'Microsoft','confidence':confidence}})
    target=ROOT/'data/cusco_buildings_ms.geojson.gz'
    payload=json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')).encode()
    target.write_bytes(gzip.compress(payload,mtime=0))
    metadata={'dataset':'Microsoft Global ML Building Footprints','release':'2026-08-13',
      'tile_quadkey':'210031023','url':URL,'license':'CDLA-Permissive-2.0',
      'source_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'crop_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
      'osm_sha256':hashlib.sha256((ROOT/'data/cusco_osm.json').read_bytes()).hexdigest(),
      'crop_lon_lat':list(crop.bounds),'counts':counts,
      'filter':'At least 12 m²; confidence >= 0.65 when supplied; unknown (-1) retained. Reject >=50% area overlap with OSM; residual overlap unioned in raster.',
      'note':'ML-derived footprints may contain omissions and false positives. Unknown confidence is not a high-confidence claim. Accepted polygons are additions to OSM, not a count of newly discovered individual houses. Heights are not used.'}
    (ROOT/'data/cusco_buildings_ms.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata,indent=2),flush=True)

if __name__=='__main__':main()
