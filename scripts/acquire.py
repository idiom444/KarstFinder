#!/usr/bin/env python3
"""Acquire only whitelisted blind-stage geographic data; cache and hash files."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from osgeo import osr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
RAW.mkdir(parents=True, exist_ok=True)
session = requests.Session()
session.mount('https://', HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
records = []


def fetch(url, name, params=None, binary=False):
    path = RAW / name
    req = requests.Request('GET', url, params=params).prepare()
    if not path.exists():
        with session.get(url, params=params, timeout=(20, 120), stream=True) as r:
            r.raise_for_status()
            tmp = path.with_suffix(path.suffix + '.part')
            with tmp.open('wb') as f:
                for block in r.iter_content(1024 * 1024):
                    f.write(block)
            if not binary:
                j = json.loads(tmp.read_text())
                if 'error' in j or j.get('exceededTransferLimit'):
                    raise RuntimeError(f'API error/truncation: {name}: {j.get("error")}')
            tmp.replace(path)
    record = {'path': str(path.relative_to(ROOT)), 'url': req.url,
              'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(),
              'bytes': path.stat().st_size,
              'verified_utc': datetime.now(timezone.utc).isoformat()}
    records.append(record)
    print(name, record['bytes'], flush=True)
    return path


def main():
    cfg = json.loads((ROOT / 'configs/blind_v001.json').read_text())
    osr.UseExceptions()
    src = osr.SpatialReference(); src.ImportFromEPSG(26910)
    dst = osr.SpatialReference(); dst.ImportFromEPSG(4326)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform = osr.CoordinateTransformation(src, dst)
    a, b, c, d = cfg['study_bounds']; pad = cfg['buffer_m']
    corners = [transform.TransformPoint(x, y) for x in [a-pad, c+pad] for y in [b-pad, d+pad]]
    bbox = [min(p[0] for p in corners), min(p[1] for p in corners), max(p[0] for p in corners), max(p[1] for p in corners)]
    bbox_text = ','.join(map(str, bbox))
    fetch('https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/5/query', 'gnis_ridge.json',
          {'f':'json', 'where':"gaz_name = 'Cave Ridge' AND state_alpha = 'WA'", 'outFields':'gaz_id,gaz_name,gaz_featureclass,state_alpha,county_name','outSR':4326})
    cat = fetch('https://tnmaccess.nationalmap.gov/api/v1/products', 'usgs_1m_catalog.json',
                {'bbox':bbox_text, 'datasets':'Digital Elevation Model (DEM) 1 meter', 'max':100})
    catalog = json.loads(cat.read_text())
    assert catalog['total'] <= 100, 'Catalog pagination required'
    tiles = [i for i in catalog['items'] if any(project in i['title'] for project in [cfg['elevation_project'], cfg['fallback_elevation_project']])]
    assert tiles, 'Expected LiDAR acquisition unavailable'
    for item in tiles:
        fetch(item['downloadURL'], Path(urlparse(item['downloadURL']).path).name, binary=True)
    base = 'https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer'
    # Exclude notes, generic point layers, inventories, and place-name annotations.
    fields = {11:'OBJECTID,MAP_UNIT_100K,MAP_UNIT_100K_SYMBOL,MAP_UNIT_100K_ID_CONFIDENCE,MAP_UNIT_100K_QUAD_UNIT',
              7:'OBJECTID,FAULTS_100K_TYPE,FAULTS_100K_IS_CONCEALED,FAULTS_100K_LOC_CONFIDENCE_M',
              9:'OBJECTID,CONTACTS_100K_TYPE,CONTACTS_100K_IS_CONCEALED,CONTACTS_100K_LOC_CONFIDENCE_M',
              1:'OBJECTID,ORIENTATION_100K_TYPE,ORIENTATION_100K_AZIMUTH,ORIENTATION_100K_INCLINATION,ORIENTATION_100K_LOC_CONF_M'}
    for layer, field_list in fields.items():
        fetch(f'{base}/{layer}',f'dnr_layer_{layer}_metadata.json', {'f':'json'})
        fetch(f'{base}/{layer}/query',f'dnr_{layer}.geojson',
              {'f':'geojson','where':'1=1','geometry':bbox_text,'geometryType':'esriGeometryEnvelope',
               'inSR':4326,'outSR':26910,'spatialRel':'esriSpatialRelIntersects','outFields':field_list})
    (ROOT / 'docs/acquisition_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Manifest saved; no known cave location sources requested.')


if __name__ == '__main__':
    main()
