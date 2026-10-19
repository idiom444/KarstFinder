#!/usr/bin/env python3
"""Acquire geology and public access context for the approved Denny follow-up."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from osgeo import osr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.freeze import verify_freeze

verify_freeze(ROOT)
osr.UseExceptions()
cfg = json.loads((ROOT / 'configs/denny_v001_landscape.json').read_text())
raw = ROOT / cfg['raw_dir']
raw.mkdir(parents=True, exist_ok=True)
source = osr.SpatialReference(); source.ImportFromEPSG(26910)
target = osr.SpatialReference(); target.ImportFromEPSG(4326)
target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
tx = osr.CoordinateTransformation(source, target)
a, b, c, d = cfg['study_bounds']; pad = cfg['buffer_m']
corners = [tx.TransformPoint(x, y) for x in [a-pad, c+pad] for y in [b-pad, d+pad]]
bbox = ','.join(map(str, [min(p[0] for p in corners), min(p[1] for p in corners),
                         max(p[0] for p in corners), max(p[1] for p in corners)]))
query = dict(f='geojson', where='1=1', geometry=bbox, geometryType='esriGeometryEnvelope',
             inSR=4326, outSR=26910, spatialRel='esriSpatialRelIntersects', resultRecordCount=2000)
records = []


def fetch(url, name, params):
    path = raw / name
    prepared = requests.Request('GET', url, params=params).prepare().url
    if not path.exists():
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        value = r.json()
        if 'error' in value:
            raise RuntimeError(value['error'])
        if value.get('exceededTransferLimit') or value.get('properties', {}).get('exceededTransferLimit'):
            raise RuntimeError('Pagination required; incomplete source rejected')
        path.write_bytes(r.content)
    value = json.loads(path.read_text())
    records.append(dict(path=str(path.relative_to(ROOT)), url=prepared,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
                        checked_utc=datetime.now(timezone.utc).isoformat()))
    return value


base = 'https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer'
fields = {
    11: 'OBJECTID,MAP_UNIT_100K,MAP_UNIT_100K_SYMBOL,MAP_UNIT_100K_ID_CONFIDENCE,MAP_UNIT_100K_QUAD_UNIT',
    7: 'OBJECTID,FAULTS_100K_TYPE,FAULTS_100K_IS_CONCEALED,FAULTS_100K_LOC_CONFIDENCE_M',
    9: 'OBJECTID,CONTACTS_100K_TYPE,CONTACTS_100K_IS_CONCEALED,CONTACTS_100K_LOC_CONFIDENCE_M',
    1: 'OBJECTID,ORIENTATION_100K_TYPE,ORIENTATION_100K_AZIMUTH,ORIENTATION_100K_INCLINATION,ORIENTATION_100K_LOC_CONF_M',
}
for layer, names in fields.items():
    value = fetch(f'{base}/{layer}/query', f'dnr_{layer}.geojson', dict(query, outFields=names))
    print('Geological layer', layer, 'features:', len(value['features']), flush=True)

access = {
    'trails': ('EDW_TrailNFSPublish_01', 'objectid,trail_name,trail_no,trail_type,trail_class,trail_surface,hiker_pedestrian_managed,hiker_pedestrian_restricted,allowed_terra_use'),
    'ownership': ('EDW_BasicOwnership_01', 'objectid,ownerclassification,region,forestname'),
}
for name, (service, names) in access.items():
    url = f'https://apps.fs.usda.gov/arcx/rest/services/EDW/{service}/MapServer/0/query'
    value = fetch(url, f'usfs_{name}.geojson', dict(query, outFields=names))
    print('USFS', name, 'features:', len(value['features']), flush=True)

# Coverage counts only: never request generic points, cave annotations or inventories.
for service in ['24K_Surface_Geology_WA_GeMS', '25_to_99K_Surface_Geology_WA_GeMS']:
    url = f'https://gis.dnr.wa.gov/site3/rest/services/Geology/{service}/MapServer'
    metadata = fetch(url, f'{service}_metadata.json', {'f': 'json'})
    layers = [l for l in metadata['layers'] if l.get('geometryType') == 'esriGeometryPolygon'
              and 'Map Unit' in l['name']]
    for layer in layers:
        params = dict(query, f='json', returnCountOnly='true')
        value = fetch(f'{url}/{layer["id"]}/query', f'{service}_coverage.json', params)
        print('Finer geological coverage:', service, value, flush=True)

original = json.loads((ROOT / 'docs/acquisition_manifest.json').read_text())
tiles = [r for r in original if r['path'].endswith('.tif') and 'USGS_1M_' in r['path']]
assert len(tiles) == 4
records.extend(dict(r, reused_from_frozen_cave_ridge_acquisition=True) for r in tiles)
manifest = ROOT / cfg['acquisition_manifest']
manifest.write_text(json.dumps(records, indent=2) + '\n')
print('Saved acquisition manifest:', manifest.relative_to(ROOT))

policy_urls = {
    'trailhead': 'https://www.fs.usda.gov/r06/mbs/recreation/denny-creek-trailhead',
    'trail': 'https://www.fs.usda.gov/r06/mbs/recreation/trails/denny-creek-trail-1014',
    'forest_alerts': 'https://www.fs.usda.gov/r06/mbs/alerts',
    'north_bend_roads': 'https://www.fs.usda.gov/r06/mbs/alerts/road-damages-closures-snoqualmie-district-north-bend-area',
    'alpental_policy': 'https://www.summitatsnoqualmie.com/uphill-travel-guide',
}
policies = []
for name, url in policy_urls.items():
    path = raw / f'{name}.html'
    if not path.exists():
        r = requests.get(url, timeout=60); r.raise_for_status(); path.write_bytes(r.content)
    policies.append(dict(path=str(path.relative_to(ROOT)), url=url,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         checked_utc=datetime.now(timezone.utc).isoformat()))
(ROOT / 'docs/experiments/denny_v001_access_sources.json').write_text(json.dumps(policies, indent=2) + '\n')
