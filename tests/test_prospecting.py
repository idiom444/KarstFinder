"""Regional lithology mapping must preserve the archived scoring categories."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from osgeo import gdal, ogr, osr
from karstfinder.prospecting import geology_codes


def context(tmp_path, marble):
    srs = osr.SpatialReference(); srs.ImportFromEPSG(26910)
    ref = gdal.GetDriverByName('MEM').Create('', 10, 10, 1, gdal.GDT_Byte)
    ref.SetGeoTransform((600000, 1, 0, 5300000, 0, -1)); ref.SetProjection(srs.ExportToWkt())
    path = tmp_path / 'context.gpkg'
    dataset = ogr.GetDriverByName('GPKG').CreateDataSource(str(path))
    layer = dataset.CreateLayer('bedrock', srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('MAP_UNIT_100K', ogr.OFTString))
    # Deliberate overlaps exercise the original water/talus/marble precedence.
    for unit, x, y, width in [('JTRmt(e)', 0, 0, 10), ('wtr', 1, 1, 4), ('Qta', 6, 6, 3), (marble, 2, 2, 2)]:
        f = ogr.Feature(layer.GetLayerDefn()); f['MAP_UNIT_100K'] = unit
        a, b, c, d = 600000+x, 5300000-y-width, 600000+x+width, 5300000-y
        f.SetGeometry(ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'))
        layer.CreateFeature(f)
    dataset = None
    return ref, path


def test_legacy_unit_gives_identical_categories_and_distances(tmp_path):
    ref, path = context(tmp_path, 'PMmb(e)')
    filename = Path(__file__).resolve().parents[1] / 'scripts/run_features.py'
    spec = importlib.util.spec_from_file_location('archived_features', filename)
    legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
    old = legacy.geology(ref, path)
    new = geology_codes(ref, path, ['PMmb(e)'])
    for actual, expected in zip(new, old):
        np.testing.assert_array_equal(actual, expected)


def test_triassic_marble_has_same_class_and_distance_as_old_marble(tmp_path):
    ref, path = context(tmp_path, 'TRmb(e)')
    codes, distance = geology_codes(ref, path, ['TRmb(e)'])
    assert (codes == 1).sum() == 4
    assert codes[2, 2] == 1  # Marble overrides the overlapping water polygon.
    assert codes[1, 1] == 4
    assert codes[7, 7] == 5
    assert distance[2, 2] == 0
    assert distance[2, 1] == 1
    assert distance[1, 1] == pytest.approx(np.sqrt(2))


def test_missing_source_unit_requires_review(tmp_path):
    ref, path = context(tmp_path, 'TRmb(e)')
    with pytest.raises(ValueError, match='No mapped marble'):
        geology_codes(ref, path, ['PMmb(e)'])
