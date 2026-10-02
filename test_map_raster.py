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
    def test_building_priority_preserves_main_roads_and_minor_core(self):
        raw=np.zeros((15,15),bool); raw[6:9,6:9]=True
        roads=np.zeros_like(raw); roads[:,5:9]=True; roads[2:5,:]=True
        main=np.zeros_like(raw); main[2:5,:]=True
        core=np.zeros_like(raw); core[:,6:8]=True
        retained=model.prioritize_buildings(raw,roads,main,core)
        self.assertTrue(retained[main].all())
        self.assertTrue(retained[core].all())
        self.assertFalse(retained[7,8])

    def test_supplement_deduplicates_overlap_without_discarding_neighbours(self):
        from prepare_buildings import is_duplicate
        from shapely.geometry import box
        existing=[box(0,0,1,1)]
        self.assertTrue(is_duplicate(box(.1,.1,1.1,1.1),existing))
        self.assertFalse(is_duplicate(box(.9,0,1.9,1),existing))

    def test_terrain_refinement_preserves_original_diagonal(self):
        # A saddle distinguishes triangle interpolation from bilinear smoothing.
        coarse=np.array([[0.,8.],[4.,0.]])
        fine=model.refine_terrain(coarse)
        np.testing.assert_array_equal(fine[::2,::2],coarse)
        self.assertEqual(fine[1,1],6.)
        self.assertEqual(fine[0,1],4.)

    def test_buildings_do_not_grow_across_road_barrier(self):
        raw=np.zeros((30,30),bool); raw[15,12]=True
        roads=np.zeros_like(raw); roads[:,14:17]=True
        with patch.object(model,'report',{}):
            grouped=model.group_buildings(raw,roads)
        self.assertTrue(grouped.any())
        self.assertFalse((grouped&roads).any())
        self.assertFalse(grouped[:,17:].any())

    def test_building_caps_are_flat_above_sloping_ground(self):
        y,x=np.mgrid[:9,:9]; ground=4.+x*.13+y*.07
        mat=np.zeros((8,8),np.uint8); mat[2:5,2:5]=2
        with patch.object(model,'report',{}):
            roofs=model.building_roof_heights(ground,mat)
        expected=ground[2:6,2:6].max()+model.BUILDING_RISE
        np.testing.assert_allclose(roofs[2:6,2:6],expected)
        np.testing.assert_array_equal(roofs[0],ground[0])
        with patch.object(model,'SIZE',8.):
            solids=[model.solid_for_material(k,x.astype(float),y.astype(float),
                        roofs if k==2 else ground,ground-.64,mat) for k in (0,2)]
        self.assertLess(abs((solids[0]^solids[1]).volume()),1e-6)
        joined=solids[0]+solids[1]
        self.assertEqual(len(joined.decompose()),1)
        self.assertTrue(model.as_mesh(joined).is_watertight)

    def test_height_tiers_preserve_flat_roofs_and_clear_slopes(self):
        y,x=np.mgrid[:51,:51]; ground=4.+x*.02+y*.03
        mat=np.zeros((50,50),np.uint8)
        groups=[(slice(2,4),slice(2,4)),(slice(8,16),slice(8,16)),
                (slice(25,43),slice(25,43))]
        for rows,cols in groups:mat[rows,cols]=2
        with patch.object(model,'report',{}):
            roofs=model.building_roof_heights(ground,mat)
        for (rows,cols),rise in zip(groups,[.48,.64,.80]):
            vertices=(slice(rows.start,rows.stop+1),slice(cols.start,cols.stop+1))
            np.testing.assert_allclose(roofs[vertices],ground[vertices].max()+rise)

    def test_information_card_preserves_mapped_features_and_points_north(self):
        y,x=np.meshgrid(np.arange(201.),np.arange(201.),indexing='ij')
        ground=4.+x*.02+y*.03;upper=ground.copy();lower=ground-.64
        mat=np.zeros((200,200),np.uint8);mat[:,100]=1;mat[20:30,20:30]=2
        protected=np.isin(mat,[1,2]);old=mat.copy()
        with patch.multiple(model,DX=1.,DY=1.,report={}):
            left,bottom,level=model.information_surface(x,y,upper,lower,mat)
            decoration=model.information_solid(left,bottom,level)
            self.assertEqual(model.report['scale']['north_direction'],'positive model Y')
            self.assertEqual(model.report['pins']['count'],0)
        np.testing.assert_array_equal(mat[protected],old[protected])
        mesh=model.as_mesh(decoration)
        self.assertTrue(mesh.is_watertight)
        self.assertTrue(mesh.is_winding_consistent)
        self.assertGreater(mesh.bounds[0,0],left)
        self.assertLess(mesh.bounds[1,0],left+38)
        self.assertGreater(mesh.bounds[0,1],bottom)
        self.assertLess(mesh.bounds[1,1],bottom+18)
        self.assertAlmostEqual(mesh.bounds[1,2],level+model.LABEL_RISE,places=5)

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

    def test_joined_body_rejects_detached_geometry_but_discards_numerical_debris(self):
        body=model.trimesh.creation.box()
        detached=body.copy(); detached.apply_translation((3,0,0))
        with patch.object(model,'report',{}):
            with self.assertRaisesRegex(AssertionError,'2 detached pieces'):
                model.joined_body(model.trimesh.util.concatenate([body,detached]))
            detached.apply_scale(.0001)
            joined=model.joined_body(model.trimesh.util.concatenate([body,detached]))
            self.assertAlmostEqual(joined.volume,body.volume)
            self.assertEqual(model.report['connected_components'],1)
            self.assertEqual(model.report['boolean_zero_volume_fragments_removed'],1)

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
            with patch.multiple(model, ROOT=root, NX=4, NY=4, SAMPLING_APRON=0., DX=50., DY=50., report={}):
                mask = model.landcover()
            expected = np.zeros((4, 4), dtype=bool)
            expected[2:, :2] = True
            np.testing.assert_array_equal(mask, expected)


if __name__ == '__main__':
    unittest.main()
