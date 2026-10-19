#!/usr/bin/env python3
"""Parameterize the established preparation/QA workflow for actual survey epochs."""
import argparse
import gc
from itertools import combinations
import json
from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import distance_transform_edt
from osgeo import gdal, ogr, osr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import array, raster, sha, CO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('area', choices=['kaleetan', 'marble'])
    args = parser.parse_args()
    area = args.area + '_v001'
    cfgpath = ROOT / f'configs/{area}_landscape.json'
    cfg = json.loads(cfgpath.read_text())
    feature_cfg = ROOT / f'configs/{area}_features.json'
    out = ROOT / cfg['processed_dir']
    if out.exists():
        raise RuntimeError(f'Refusing prepared-input overwrite: {out}')
    out.mkdir(parents=True)
    pre = out / 'features'; pre.mkdir()
    a, b, c, d = cfg['study_bounds']; pad = cfg['buffer_m']
    bounds = [a-pad, b-pad, c+pad, d+pad]
    sources = cfg['elevation_sources']
    tiles = [str(ROOT / item['path']) for item in sources]
    native = []
    for item, path in zip(sources, tiles):
        dataset = gdal.Open(path)
        assert dataset.GetSpatialRef().GetAuthorityCode(None) == '26910', f'Review native CRS before proceeding: {path}'
        if item.get('conversion_record'):
            conversion = json.loads((ROOT / item['conversion_record']).read_text())
            assert conversion['output_path'] == item['path']
            assert conversion['output_sha256'] == sha(path)
            assert conversion['vertical_scale_ftUS_to_m'] == 1200 / 3937
            units_evidence = item['conversion_record']
        else:
            assert 'All bare earth elevation values are in meters' in item['catalog_body']
            units_evidence = 'USGS catalog declaration'
        assert dataset.GetRasterBand(1).GetUnitType() in ('', 'm', 'metre', 'meter')
        native.append({'path': item['path'], 'year': item['year'], 'project': item['project'],
                       'crs': 'EPSG:26910', 'size': [dataset.RasterXSize, dataset.RasterYSize],
                       'geotransform': dataset.GetGeoTransform(), 'vertical_datum': 'NAVD88',
                       'elevation_units': 'metres; ' + units_evidence, 'sha256': sha(path)})
    # Source list is in oldest-to-newest order, exactly as in the established workflow.
    vrt = gdal.BuildVRT(str(out / 'elevation_source.vrt'), tiles)
    for res, name in [(1, 'dem_1m_buffered'), (10, 'dem_10m_buffered')]:
        dataset = gdal.Warp(str(out / (name + '.tif')), vrt, dstSRS=cfg['crs'], outputBounds=bounds,
                            xRes=res, yRes=res, resampleAlg='near' if res == 1 else 'average',
                            dstNodata=-9999, outputType=gdal.GDT_Float32, creationOptions=CO)
        dataset.GetRasterBand(1).SetUnitType('m'); dataset = None
        print(area, name, flush=True)
    vrt = None
    ref = gdal.Open(str(out / 'dem_1m_buffered.tif'))
    valid = np.isfinite(array(out / 'dem_1m_buffered.tif'))
    if not valid.all():
        raise RuntimeError(f'{area}: {int((~valid).sum())} native buffer cells missing; no unreviewed infill allowed')
    epoch = np.zeros(valid.shape, dtype='uint16'); years = sorted({s['year'] for s in sources})
    samples = {}
    for year in years:
        files = [str(ROOT / s['path']) for s in sources if s['year'] == year]
        vrt = gdal.BuildVRT('', files)
        dataset = gdal.Warp('', vrt, format='MEM', dstSRS=cfg['crs'], outputBounds=bounds,
                            xRes=1, yRes=1, resampleAlg='near', dstNodata=-9999)
        z = dataset.ReadAsArray(); z[z == -9999] = np.nan
        epoch[np.isfinite(z)] = year
        samples[year] = z[::10, ::10].copy()
        del z; dataset = None; vrt = None; gc.collect()
    assert np.array_equal(epoch > 0, valid)
    raster(pre / 'source_epoch_1m_buffered.tif', epoch, ref, nodata=0, dtype=gdal.GDT_UInt16)
    epoch10 = epoch.reshape(epoch.shape[0]//10, 10, epoch.shape[1]//10, 10).max(axis=(1, 3))
    raster(out / 'source_epoch_10m.tif', epoch10, out / 'dem_10m_buffered.tif', nodata=0, dtype=gdal.GDT_UInt16)
    seam = np.zeros(epoch.shape, bool)
    seam[1:] |= (epoch[1:] != epoch[:-1]) & (epoch[1:] > 0) & (epoch[:-1] > 0)
    seam[:, 1:] |= (epoch[:, 1:] != epoch[:, :-1]) & (epoch[:, 1:] > 0) & (epoch[:, :-1] > 0)
    distance = distance_transform_edt(~seam).astype('float32') if seam.any() else np.full(epoch.shape, 1e9, dtype='float32')
    raster(pre / 'seam_distance_1m_buffered.tif', distance, ref)
    quality = valid & (distance > 25)
    raster(pre / 'feature_quality_1m_buffered.tif', quality.astype('uint8'), ref, nodata=255, dtype=gdal.GDT_Byte)
    overlaps = []
    for older, newer in combinations(years, 2):
        both = np.isfinite(samples[older]) & np.isfinite(samples[newer])
        diff = samples[newer][both] - samples[older][both]
        overlaps.append({'older_year': older, 'newer_year': newer, 'sampling_stride_m': 10, 'n': int(diff.size),
                   'median_difference_m': float(np.median(diff)) if diff.size else None,
                   'p95_absolute_difference_m': float(np.percentile(np.abs(diff), 95)) if diff.size else None,
                   'p99_absolute_difference_m': float(np.percentile(np.abs(diff), 99)) if diff.size else None})
    core = np.s_[pad:-pad, pad:-pad]
    qa = {'native_buffered_pixels': int(valid.size), 'native_buffered_missing_pixels': int((~valid).sum()),
          'native_buffered_valid_fraction': float(valid.mean()), 'native_study_missing_pixels': int((~valid[core]).sum()),
          'native_overlap_sample': overlaps[-1] if overlaps else {}, 'native_overlap_samples': overlaps,
          'study_feature_eligible_area_km2': float(quality[core].sum()/1e6),
          'study_seam_excluded_area_km2': float((valid[core] & ~quality[core]).sum()/1e6), 'seam_exclusion_m': 25,
          'native_year_counts': {str(y): int((epoch[core] == y).sum()) for y in [0] + years},
          'source_hash': sha(out / 'dem_1m_buffered.tif'), 'config_hash': sha(feature_cfg)}
    (pre / 'qa.json').write_text(json.dumps(qa, indent=2) + '\n')
    (ROOT / f'docs/experiments/{area}_native_quality.json').write_text(json.dumps(qa, indent=2) + '\n')
    srs = osr.SpatialReference(); srs.ImportFromEPSG(26910)
    gpkg = out / 'context.gpkg'
    for ident, name, geometry in [(11, 'bedrock', ogr.wkbMultiPolygon), (7, 'faults', ogr.wkbMultiLineString),
                                   (9, 'contacts', ogr.wkbMultiLineString), (1, 'orientations', ogr.wkbMultiPoint)]:
        path = ROOT / cfg['raw_dir'] / f'dnr_{ident}.geojson'
        value = json.loads(path.read_text())
        if value['features']:
            source = ogr.Open(str(path))
            result = gdal.VectorTranslate(str(gpkg), source, format='GPKG', layerName=name,
                                          accessMode='update' if gpkg.exists() else None,
                                          geometryType='PROMOTE_TO_MULTI', srcSRS=cfg['crs'], dstSRS=cfg['crs'], clipDst=bounds)
            result = None; source = None
        else:
            dest = ogr.Open(str(gpkg), 1)
            dest.CreateLayer(name, srs, geometry); dest = None
    dest = ogr.Open(str(gpkg), 1); layer = dest.GetLayerByName('bedrock')
    layer.CreateField(ogr.FieldDefn('geo_score', ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn('evidence', ogr.OFTString))
    for feature in layer:
        unit = feature['MAP_UNIT_100K']; feature['geo_score'] = cfg['geology_scores'].get(unit, 0)
        feature['evidence'] = ('mapped marble; 1:100k contact uncertainty' if unit in cfg['marble_units'] else
                               'mixed melange may contain unmapped marble' if unit == 'JTRmt(e)' else
                               'no mapped carbonate evidence; not proof of absence')
        layer.SetFeature(feature)
    study = dest.CreateLayer('study_area', srs, ogr.wkbPolygon)
    study.CreateField(ogr.FieldDefn('name', ogr.OFTString))
    feature = ogr.Feature(study.GetLayerDefn()); feature['name'] = cfg['area_name'] + ' | approved 9 km2 | unvalidated'
    feature.SetGeometry(ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'))
    study.CreateFeature(feature); dest = None
    report = {'source_rasters': native, 'study_area_km2': 9, 'buffer_m': pad,
              'buffered_valid_fraction': float(valid.mean()), 'study_valid_fraction': float(valid[core].mean()),
              'native_qa': qa, 'epoch_10m_interpretation': 'newest contributing native epoch per 10m cell; native seam mask governs 1m detection',
              'mosaic_policy': 'oldest first, newest valid precedence; native nearest-neighbour, 10m average; no seam feathering'}
    (ROOT / cfg['quality_report']).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    gdal.UseExceptions(); ogr.UseExceptions(); osr.UseExceptions()
    main()
