"""Download and crop ESA WorldCover 2021 v200 for the Cusco model.

Only the small lossless crop and source metadata are kept in the repository.
Run with the model Python environment. Downloads use a temporary directory.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
import hashlib
import json
import math
import rasterio
from rasterio.merge import merge

ROOT = Path(__file__).resolve().parent
LAT, LON = -13.53195, -71.96746
DLAT = 20 / 111.32
DLON = 20 / (111.32 * math.cos(math.radians(LAT)))
SOUTH = LAT - 10 / 111.32
WEST = LON - 10 / (111.32 * math.cos(math.radians(LAT)))
BOUNDS = (WEST, SOUTH, WEST+DLON, SOUTH+DLAT)
PREFIX = 'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'


def main():
    sources = []
    with TemporaryDirectory(prefix='cusco-worldcover-') as tmp:
        paths = []
        for tile in ('S15W075', 'S15W072'):
            url = f'{PREFIX}ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
            path = Path(tmp) / f'{tile}.tif'
            print(f'Downloading {tile}...', flush=True)
            urlretrieve(url, path)
            paths.append(path)
            sources.append({'tile': tile, 'url': url,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        datasets = [rasterio.open(p) for p in paths]
        try:
            data, transform = merge(datasets, bounds=BOUNDS)
        finally:
            for dataset in datasets:
                dataset.close()
    assert (data > 0).all(), 'Missing classes in land-cover crop'
    target = ROOT / 'data/cusco_worldcover_2021.tif'
    with rasterio.open(target, 'w', driver='GTiff', height=data.shape[1],
                       width=data.shape[2], count=1, dtype='uint8',
                       crs='EPSG:4326', transform=transform,
                       compress='deflate', nodata=0) as dst:
        dst.write(data)
    metadata = {
        'dataset': 'ESA WorldCover 10 m 2021 v200',
        'doi': 'https://doi.org/10.5281/zenodo.7254221',
        'license': 'CC BY 4.0',
        'attribution': '© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium',
        'sources': sources, 'requested_bounds_wsen': BOUNDS,
        'crop_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'processing': 'Lossless spatial crop and mosaic; categorical mode resampling occurs during model build.',
        'classes': {'10':'Tree cover','20':'Shrubland','30':'Grassland','40':'Cropland',
                    '50':'Built-up','60':'Bare / sparse vegetation','70':'Snow and ice',
                    '80':'Permanent water','90':'Herbaceous wetland','95':'Mangroves','100':'Moss and lichen'},
        'green_classes': [10,20,30,40,90,95,100],
        'limitations': '2021 land cover, not current or seasonal colours. All vegetation classes share one green filament; other classes use the terrain colour. OSM buildings, roads and airport take precedence.'}
    target.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(target)


if __name__ == '__main__':
    main()
