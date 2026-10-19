#!/usr/bin/env python3
"""Post-freeze public sources, local-only, with exact acquisition provenance."""
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as E
import requests
from osgeo import osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.freeze import verify_freeze
verify_freeze(ROOT);osr.UseExceptions()
p=ROOT/'data/private/validation/sources';p.mkdir(parents=True,exist_ok=True)
cfg=json.loads((ROOT/'configs/blind_v002.json').read_text());a,b,c,d=cfg['study_bounds']
s=osr.SpatialReference();s.ImportFromEPSG(26910);t=osr.SpatialReference();t.ImportFromEPSG(4326);t.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);tx=osr.CoordinateTransformation(s,t)
corners=[tx.TransformPoint(x,y) for x in [a,c] for y in [b,d]]
bbox=','.join(map(str,[min(x[0] for x in corners),min(x[1] for x in corners),max(x[0] for x in corners),max(x[1] for x in corners)]))
manifest=[]

def fetch(url,name,params=None):
    path=p/name
    if path.exists():
        content=path.read_bytes();actual_url=requests.Request('GET',url,params=params).prepare().url
    else:
        r=requests.get(url,params=params,timeout=60);r.raise_for_status();content=r.content;path.write_bytes(content);actual_url=r.url
    manifest.append({'path':str(path.relative_to(ROOT)),'url':actual_url,'sha256':hashlib.sha256(content).hexdigest(),
                     'checked_utc':datetime.now(timezone.utc).isoformat(),'local_only':True})
    return content
fetch('https://www.dnr.wa.gov/publications/ger_ic40_caves_of_wa.pdf','dnr_ic40_1963.pdf')
content=fetch('https://api.openstreetmap.org/api/0.6/map','osm_study_extract.osm',{'bbox':bbox})
xml=E.fromstring(content)
nodes=[x for x in xml.findall('node') if any(t.attrib.get('k')=='natural' and t.attrib.get('v')=='cave_entrance' for t in x.findall('tag'))]
for cid in sorted(set(x.attrib['changeset'] for x in nodes)):
 fetch(f'https://api.openstreetmap.org/api/0.6/changeset/{cid}',f'osm_changeset_{cid}.xml')
u='https://gis.dnr.wa.gov/site3/rest/services/Public_Boundaries/WADNR_PUBLIC_Public_Land_Survey/MapServer/8/query'
content=fetch(u,'plss_sections.geojson',{'f':'geojson','where':'1=1','geometry':'-121.43,47.44,-121.39,47.475',
 'geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,'outFields':'*'})
assert 'error' not in json.loads(content)
(p/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Public entrance records in full-study geographic envelope:',len(nodes))
