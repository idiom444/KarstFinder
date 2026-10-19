#!/usr/bin/env python3
"""Acquire public geology, numeric DEMs and access context for two approved areas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from osgeo import osr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha

AREAS = {'kaleetan': ('kaleetan_v001', 'Kaleetan Peak vicinity', 'kaleetan-vicinity',
                     ['PMmb(e)'], [('WA_EasternCascades_2019_B19', 2019), ('WA_KingCounty_2021_B21', 2021)]),
         'marble': ('marble_v001', 'Marble Peak / upper Marble Gulch', 'marble-peak',
                    ['TRmb(e)'], [('WA_Western_North_2016', 2016), ('WA_KingCounty_2021_B21', 2021)])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('area', choices=AREAS)
    args = parser.parse_args()
    area, title, proposal, units, sources = AREAS[args.area]
    raw = ROOT / 'data/raw' / area
    raw.mkdir(exist_ok=True)
    shared = ROOT / 'data/raw/shared_elevation_v001'
    shared.mkdir(exist_ok=True)
    records = []
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])))

    def fetch(url, path, params=None, json_data=True):
        if not path.exists():
            with session.get(url, params=params, stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                temp = path.with_suffix(path.suffix + '.part')
                with temp.open('wb') as stream:
                    for block in response.iter_content(1024 * 1024):
                        stream.write(block)
                if json_data:
                    value = json.loads(temp.read_text())
                    if 'error' in value or value.get('exceededTransferLimit') or value.get('properties', {}).get('exceededTransferLimit'):
                        raise RuntimeError(f'Incomplete source rejected: {path}: {value.get("error")}')
                temp.replace(path)
        record = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                  'url': requests.Request('GET', url, params=params).prepare().url,
                  'bytes': path.stat().st_size, 'checked_utc': datetime.now(timezone.utc).isoformat()}
        records.append(record)
        print(path.relative_to(ROOT), path.stat().st_size, flush=True)
        return json.loads(path.read_text()) if json_data else path

    proposals = json.loads((ROOT / 'docs/proposals/20261019_carbonate_scope.json').read_text())
    window = next(p for p in proposals['proposed_study_windows'] if p['proposal_id'] == proposal)
    a, b, c, d = window['bounds']
    source = osr.SpatialReference(); source.ImportFromEPSG(26910)
    target = osr.SpatialReference(); target.ImportFromEPSG(4326)
    target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    tx = osr.CoordinateTransformation(source, target)
    xy = [tx.TransformPoint(x, y) for x in [a-1100, c+1100] for y in [b-1100, d+1100]]
    bbox = ','.join(map(str, [min(p[0] for p in xy), min(p[1] for p in xy), max(p[0] for p in xy), max(p[1] for p in xy)]))
    # An earlier read-only catalog screen may already have cached this response.
    catalog = fetch('https://tnmaccess.nationalmap.gov/api/v1/products', raw / 'usgs_1m_catalog.json',
                    {'bbox': bbox, 'datasets': 'Digital Elevation Model (DEM) 1 meter', 'max': 500})
    assert catalog['total'] <= 500
    elevation = []
    for project, year in sources:
        selected = [i for i in catalog['items'] if project in i['downloadURL']]
        if not selected:
            raise RuntimeError(f'Expected acquisition absent: {project}')
        for item in selected:
            name = Path(urlparse(item['downloadURL']).path).name
            original = ROOT / 'data/raw' / name
            path = original if original.exists() else shared / name
            fetch(item['downloadURL'], path, json_data=False)
            assert 'meter' in item['body'].lower() or 'metre' in item['body'].lower()
            elevation.append({'path': str(path.relative_to(ROOT)), 'year': year, 'project': project,
                              'catalog_title': item['title'], 'catalog_body': item['body']})
    common = {'f': 'geojson', 'where': '1=1', 'geometry': bbox, 'geometryType': 'esriGeometryEnvelope',
              'inSR': 4326, 'outSR': 26910, 'spatialRel': 'esriSpatialRelIntersects', 'resultRecordCount': 2000}
    base = 'https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer'
    fields = {11: 'OBJECTID,MAP_UNIT_100K,MAP_UNIT_100K_ID_CONFIDENCE,MAP_UNIT_100K_QUAD_UNIT',
              7: 'OBJECTID,FAULTS_100K_TYPE,FAULTS_100K_IS_CONCEALED,FAULTS_100K_LOC_CONFIDENCE_M',
              9: 'OBJECTID,CONTACTS_100K_TYPE,CONTACTS_100K_IS_CONCEALED,CONTACTS_100K_LOC_CONFIDENCE_M',
              1: 'OBJECTID,ORIENTATION_100K_TYPE,ORIENTATION_100K_AZIMUTH,ORIENTATION_100K_INCLINATION'}
    for layer, names in fields.items():
        value = fetch(f'{base}/{layer}/query', raw / f'dnr_{layer}.geojson', {**common, 'outFields': names})
        print('Geology', layer, len(value['features']), flush=True)
    for name, service, names in [
            ('trails', 'EDW_TrailNFSPublish_01', 'objectid,trail_name,trail_no,hiker_pedestrian_managed,hiker_pedestrian_restricted'),
            ('ownership', 'EDW_BasicOwnership_01', 'objectid,ownerclassification,forestname')]:
        fetch(f'https://apps.fs.usda.gov/arcx/rest/services/EDW/{service}/MapServer/0/query',
              raw / f'usfs_{name}.geojson', {**common, 'outFields': names})
    original = json.loads((ROOT / 'configs/denny_v001_landscape.json').read_text())
    landscape = {**original, 'experiment_id': area + '_landscape', 'area_name': title,
                 'study_bounds': window['bounds'], 'raw_dir': str(raw.relative_to(ROOT)),
                 'processed_dir': f'data/processed/{area}', 'elevation_sources': elevation,
                 'marble_units': units, 'geology_scores': {**original['geology_scores'], **{u: 1.0 for u in units}},
                 'acquisition_manifest': f'docs/experiments/{area}_acquisition.json',
                 'quality_report': f'docs/experiments/{area}_data_quality.json',
                 'public_literature_screening_before_selection': True, 'independently_blind': False,
                 'notes': 'User approved this 3x3 km proposal on 2026-10-19. Literature-informed unvalidated prospecting. Existing numerical scales/thresholds/weights retained. No entrance records used for scoring.'}
    features = {**json.loads((ROOT / 'configs/denny_v001_features.json').read_text()),
                'experiment_id': area + '_features', 'area_name': title, 'study_bounds': window['bounds'],
                'landscape_run': f'results/{area}_landscape', 'processed_dir': landscape['processed_dir'],
                'feature_processed_dir': f'data/processed/{area}/features',
                'native_quality_report': f'docs/experiments/{area}_native_quality.json',
                'marble_units': units, 'mixed_units': ['JTRmt(e)'],
                'elevation_sources': elevation, 'public_literature_screening_before_selection': True,
                'independently_blind': False, 'notes': landscape['notes']}
    for kind, config in [('landscape', landscape), ('features', features)]:
        path = ROOT / f'configs/{area}_{kind}.json'
        text = json.dumps(config, indent=2) + '\n'
        if path.exists() and path.read_text() != text:
            raise RuntimeError(f'Refusing changed configuration overwrite: {path}')
        path.write_text(text)
    (ROOT / landscape['acquisition_manifest']).write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    osr.UseExceptions()
    main()
