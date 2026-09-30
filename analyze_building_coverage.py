"""Measure source coverage and model building area in the previously sparse quarters."""
import gzip,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
import rasterio
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_bounds
import build_print_model as m

ZONES=[('Nordwest',-13.513037074,-71.996794995),
       ('Suedwest',-13.541610351,-71.986891649),
       ('Flughafenumfeld',-13.535798322,-71.940185508)]

def main():
    osm=Image.new('1',(m.NX,m.NY)); draw=ImageDraw.Draw(osm)
    for e in json.loads((m.ROOT/'data/cusco_osm.json').read_text())['elements']:
        g=e.get('geometry',[])
        if 'building' in e.get('tags',{}) and len(g)>=4 and g[0]==g[-1]:
            draw.polygon([m.xy(p) for p in g],fill=1)
    merged=osm.copy(); draw=ImageDraw.Draw(merged)
    data=json.loads(gzip.decompress((m.ROOT/'data/cusco_buildings_ms.geojson.gz').read_bytes()))
    for f in data['features']:
        geom=f['geometry']
        for polygon in geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]:
            if len(polygon)==1:
                draw.polygon([m.xy({'lon':lon,'lat':lat}) for lon,lat in polygon[0]],fill=1)
                continue
            mask=Image.new('1',(m.NX,m.NY)); d=ImageDraw.Draw(mask)
            for i,ring in enumerate(polygon):
                d.polygon([m.xy({'lon':lon,'lat':lat}) for lon,lat in ring],fill=int(i==0))
            merged.paste(1,mask=mask)
    masks={'osm':np.array(osm,bool),'osm_plus_microsoft':np.array(merged,bool)}
    classes=np.zeros((m.NY,m.NX),np.uint8)
    with rasterio.open(m.ROOT/'data/cusco_worldcover_2021.tif') as src:
        reproject(rasterio.band(src,1),classes,src_transform=src.transform,src_crs=src.crs,
          dst_transform=from_bounds(m.WEST,m.SOUTH-m.SAMPLING_APRON/m.SIZE*m.DLAT,
                                    m.WEST+m.DLON,m.SOUTH+m.DLAT,m.NX,m.NY),
          dst_crs='EPSG:4326',resampling=Resampling.mode,src_nodata=0,dst_nodata=0)
    x,y=np.meshgrid((np.arange(m.NX)+.5)*m.DX,(np.arange(m.NY)+.5)*m.DY-m.SAMPLING_APRON)
    urban=(np.flipud(classes)==50)&(y>=0)
    report={'note':'Built-up land-cover is settlement evidence, not individual building outlines. Each local comparison covers the same 2 x 2 km square.'}
    distances={name:ndi.distance_transform_edt(~mask,sampling=(m.DY*100,m.DX*100)) for name,mask in masks.items()}
    report['built_up_without_building_within_100m_percent']={name:float(100*(urban&(dist>100)).sum()/urban.sum()) for name,dist in distances.items()}
    mat,_=m.raster_layers()
    report['model_building_area_mm2']=float(((mat==2)&(y>=0)).sum()*m.DX*m.DY)
    report['zones']=[]
    for name,lat,lon in ZONES:
        px=(lon-m.WEST)/m.DLON*m.SIZE; py=(lat-m.SOUTH)/m.DLAT*m.SIZE
        roi=(abs(x-px)<10)&(abs(y-py)<10)
        report['zones'].append({'name':name,'latitude':lat,'longitude':lon,
          'source_footprint_area_mm2':{key:float((mask&roi).sum()*m.DX*m.DY) for key,mask in masks.items()},
          'urban_without_nearby_building_percent':{key:float(100*(roi&urban&(dist>100)).sum()/(roi&urban).sum()) for key,dist in distances.items()},
          'model_building_area_mm2':float(((mat==2)&roi).sum()*m.DX*m.DY)})
    (m.OUT/'building_coverage_comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
