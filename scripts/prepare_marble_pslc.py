#!/usr/bin/env python3
"""Convert the authoritative 3 ft PSLC bare-earth mosaic to a local metre crop.

Uses GDAL OpenFileGDB and Warp; no custom interpolation or terrain derivatives.
The original archive and source metadata remain unchanged and hashed.
"""
import json
from pathlib import Path
import sys
import numpy as np
from osgeo import gdal, osr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha, CO


def main():
    raw = ROOT / 'data/raw/marble_v001'
    acquisition = json.loads((ROOT / 'docs/experiments/marble_v001_pslc_acquisition.json').read_text())
    assert acquisition['archive_crc_verified']
    assert acquisition['metadata_sha256'] == sha(ROOT / acquisition['metadata_path'])
    databases = list((raw / 'pslc_gdb').rglob('*.gdb'))
    assert len(databases) == 1, databases
    source = gdal.Open(str(databases[0]))
    if not source.RasterCount:
        datasets = source.GetSubDatasets()
        # The archive also exposes tulalip_be_h; select the explicitly named
        # 32-bit bare-earth elevation raster, never the auxiliary raster.
        selected = [item for item in datasets if item[0].rsplit(':',1)[-1] == 'tulalip_be']
        assert len(selected) == 1, datasets
        source = gdal.Open(selected[0][0])
    assert source.RasterCount == 1
    assert source.GetRasterBand(1).DataType == gdal.GDT_Float32
    # Legacy Esri WKT has rounded projection parameters and no root EPSG code.
    # Validate its datum, units and every projection parameter against the
    # supplier-declared CRS before assigning its canonical EPSG definition.
    source_srs = source.GetSpatialRef()
    canonical_srs = osr.SpatialReference(); canonical_srs.ImportFromEPSG(2926)
    assert source_srs.GetAttrValue('DATUM') == canonical_srs.GetAttrValue('DATUM')
    assert source_srs.GetAttrValue('PROJECTION') == canonical_srs.GetAttrValue('PROJECTION')
    assert abs(source_srs.GetLinearUnits()-1200/3937) < 1e-14
    # Lambert's two standard parallels may be serialized in either order.
    parallels = lambda s: sorted(s.GetProjParm(n) for n in ['standard_parallel_1','standard_parallel_2'])
    assert np.allclose(parallels(source_srs),parallels(canonical_srs),rtol=0,atol=1e-6)
    for name in ['latitude_of_origin','central_meridian','false_easting','false_northing']:
        tolerance = .001 if name.startswith('false_') else 1e-6
        assert abs(source_srs.GetProjParm(name)-canonical_srs.GetProjParm(name)) < tolerance, name
    assert np.isclose(source.GetGeoTransform()[1], 3)
    assert np.isclose(source.GetGeoTransform()[5], -3)
    cfgpath = ROOT / 'configs/marble_v001_landscape.json'
    cfg = json.loads(cfgpath.read_text())
    a,b,c,d = cfg['study_bounds']; pad = cfg['buffer_m']+50
    path = ROOT / 'data/raw/shared_elevation_v001/PSLC_Tulalip2013_marble_1m_metres.tif'
    if path.exists():
        raise RuntimeError(f'Refusing converted source overwrite: {path}')
    output = gdal.Warp(str(path), source, srcSRS='EPSG:2926', dstSRS='EPSG:26910',
        outputBounds=[a-pad,b-pad,c+pad,d+pad], xRes=1, yRes=1, resampleAlg='near',
        outputType=gdal.GDT_Float32, dstNodata=-9999, creationOptions=CO, errorThreshold=0)
    z = output.ReadAsArray(); valid = np.isfinite(z) & (z != -9999)
    # Check that GDAL did not implicitly rescale heights: nearest-neighbour
    # output must retain the source foot value before our explicit conversion.
    target_srs = osr.SpatialReference(); target_srs.ImportFromEPSG(26910)
    tx = osr.CoordinateTransformation(target_srs, canonical_srs)
    inv = gdal.InvGeoTransform(source.GetGeoTransform()); gt = output.GetGeoTransform()
    checks = 0
    for row in range(100, z.shape[0], 500):
        for col in range(100, z.shape[1], 500):
            if not valid[row,col]:
                continue
            x,y = gdal.ApplyGeoTransform(gt,col+.5,row+.5)
            sx,sy,_ = tx.TransformPoint(x,y)
            sc,sr = gdal.ApplyGeoTransform(inv,sx,sy)
            value = source.GetRasterBand(1).ReadAsArray(int(sc),int(sr),1,1)[0,0]
            assert abs(float(z[row,col])-float(value)) < .001, 'Review implicit height scaling or source sampling'
            checks += 1
    assert checks > 0
    z[~valid] = -9999
    z[valid] *= 1200 / 3937
    output.GetRasterBand(1).WriteArray(z); output.GetRasterBand(1).SetUnitType('m')
    output = None
    record_path = 'docs/experiments/marble_v001_pslc_conversion.json'
    record = {'source_archive_sha256': acquisition['sha256'], 'gdal_driver': source.GetDriver().ShortName,
        'source_raster_dataset': 'tulalip_be (32-bit bare-earth elevation)',
        'source_native_crs': 'EPSG:2926', 'source_native_cell_size_ftUS': 3,
        'source_geotransform': source.GetGeoTransform(), 'source_units': 'US survey feet',
        'source_original_wkt': source_srs.ExportToWkt(),
        'canonical_crs_assignment': 'Supplier metadata EPSG:2926; legacy WKT datum, linear unit and all six projection parameters checked (angular tolerance 1e-6 degrees, linear tolerance 0.001 ftUS; standard-parallel order is interchangeable).',
        'legacy_vs_epsg_false_easting_difference_ftUS': source_srs.GetProjParm('false_easting')-canonical_srs.GetProjParm('false_easting'),
        'vertical_scale_ftUS_to_m': 1200/3937, 'vertical_datum': 'NAVD88 / Geoid03',
        'output_crs': 'EPSG:26910', 'output_resolution_m': 1, 'resampling': 'nearest neighbour',
        'output_path': str(path.relative_to(ROOT)), 'output_sha256': sha(path),
        'valid_fraction_in_5300m_crop': float(valid.mean()),
        'unscaled_source_pixel_checks': checks,
        'metadata_path': acquisition['metadata_path'], 'metadata_sha256': acquisition['metadata_sha256'],
        'datum_policy': 'GDAL/PROJ horizontal transform; no vertical datum shift or fitted alignment',
        'interpretation': 'A 1 m working grid from native 3 US survey foot bare-earth data; not finer detail inferred from coarse terrain.'}
    (ROOT / record_path).write_text(json.dumps(record, indent=2)+'\n')
    item = {'path': str(path.relative_to(ROOT)), 'year': 2013, 'project': 'PSLC_Tulalip2013',
            'catalog_title': 'PSLC Tulalip 2013 bare-earth mosaic',
            'conversion_record': record_path}
    for kind in ['landscape', 'features']:
        config_path = ROOT / f'configs/marble_v001_{kind}.json'
        config = json.loads(config_path.read_text())
        assert all(s['project'] != item['project'] for s in config['elevation_sources'])
        config['elevation_sources'].insert(0, item)
        config['notes'] += ' Coverage review added PSLC Tulalip 2013 native 3 ftUS bare-earth terrain, converted to metre elevations and a 1 m working grid before the first successful run.'
        config_path.write_text(json.dumps(config, indent=2)+'\n')
    manifest_path = ROOT / cfg['acquisition_manifest']
    manifest = json.loads(manifest_path.read_text())
    manifest.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                     'url': acquisition['url'], 'bytes': path.stat().st_size,
                     'operation_record': record_path})
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    rejected = ROOT / 'data/processed/marble_v001'
    if rejected.exists():
        rejected.rename(rejected.with_name('marble_v001_rejected_partial_01'))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    gdal.UseExceptions()
    main()
