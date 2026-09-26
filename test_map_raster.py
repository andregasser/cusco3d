"""Regressions for road continuity and geographic orientation."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from scipy import ndimage as ndi
import rasterio
from rasterio.transform import from_bounds
import build_print_model as model


class MapRasterTests(unittest.TestCase):
    def test_diagonal_roads_connect_without_removing_source(self):
        mat = np.zeros((9, 9), dtype=np.uint8)
        for i in range(2, 7):
            mat[i, i] = 1
        source = mat == 1
        model.repair_material_contacts(mat)
        self.assertTrue(np.all(mat[source] == 1))
        self.assertEqual(ndi.label(mat == 1)[1], 1)
        self.assertFalse(mat[[0, -1], :].any())
        self.assertFalse(mat[:, [0, -1]].any())

    def test_mixed_contacts_preserve_roads_and_converge(self):
        rng = np.random.default_rng(12)
        mat = np.pad(rng.integers(0, 4, size=(30, 30), dtype=np.uint8), 1)
        source = mat == 1
        model.repair_material_contacts(mat)
        self.assertTrue(np.all(mat[source] == 1))
        self.assertEqual(model.repair_material_contacts(mat), 0)

    def test_link_classes_are_included(self):
        for kind in ('motorway', 'trunk', 'primary', 'secondary', 'tertiary'):
            self.assertIn(kind + '_link', model.ROAD_WIDTHS)

    def test_coordinates_share_terrain_frame(self):
        west_south = model.xy({'lon':model.WEST, 'lat':model.SOUTH})
        east_north = model.xy({'lon':model.WEST+model.DLON, 'lat':model.SOUTH+model.DLAT})
        np.testing.assert_allclose(west_south, (0, model.SAMPLING_APRON/model.DY), atol=1e-8)
        np.testing.assert_allclose(east_north, (model.NX, model.NY), atol=1e-8)

    def test_landcover_northwest_stays_northwest_in_mesh(self):
        # Only the northwest quadrant is vegetated. A flip or transpose would
        # move the green quadrant; heights and OSM use south-to-north rows.
        with TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'data').mkdir()
            classes = np.full((4, 4), 60, dtype=np.uint8)
            classes[:2, :2] = 10
            transform = from_bounds(model.WEST, model.SOUTH, model.WEST+model.DLON,
                                    model.SOUTH+model.DLAT, 4, 4)
            with rasterio.open(root/'data/cusco_worldcover_2021.tif', 'w', driver='GTiff',
                               width=4, height=4, count=1, dtype='uint8',
                               crs='EPSG:4326', transform=transform) as dst:
                dst.write(classes, 1)
            with patch.multiple(model, ROOT=root, NX=4, NY=4, SAMPLING_APRON=0., DY=50., report={}):
                mask = model.landcover()
            expected = np.zeros((4, 4), dtype=bool)
            expected[2:, :2] = True
            np.testing.assert_array_equal(mask, expected)


if __name__ == '__main__':
    unittest.main()
