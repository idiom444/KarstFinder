#!/usr/bin/env python3
"""Turn already acquired public OSM records into explicitly uncertain local references."""
import json,sys
from pathlib import Path
from xml.etree import ElementTree as E
from osgeo import osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.freeze import verify_freeze
verify_freeze(ROOT)
private=ROOT/'data/private/validation';sources=private/'sources';source=sources/'osm_study_extract.osm'
xml=E.fromstring(source.read_bytes())
cfg=json.loads((ROOT/'configs/blind_v002.json').read_text());xmin,ymin,xmax,ymax=cfg['study_bounds']
osr.UseExceptions();s=osr.SpatialReference();s.ImportFromEPSG(4326);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
t=osr.SpatialReference();t.ImportFromEPSG(26910);tx=osr.CoordinateTransformation(s,t)
features=[]
for node in xml.findall('node'):
 tags={t.attrib['k']:t.attrib['v'] for t in node.findall('tag')}
 if tags.get('natural')!='cave_entrance':continue
 x,y,_=tx.TransformPoint(float(node.attrib['lon']),float(node.attrib['lat']))
 if not (xmin<=x<xmax and ymin<=y<ymax):continue
 features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[float(node.attrib['lon']),float(node.attrib['lat'])]},
   'properties':{'record_id':f'R{len(features)+1:03d}','name':tags.get('name','unnamed'),
     'source_url':f'https://www.openstreetmap.org/node/{node.attrib["id"]}',
     'source_dataset':'OpenStreetMap public node; unverified accuracy','source_timestamp':node.attrib.get('timestamp'),
     'source_extract':str(source.relative_to(ROOT)),
     'changeset':node.attrib.get('changeset'),'mapper_id':node.attrib.get('uid'),
     'uncertainty_m':100,'uncertainty_basis':'100 m exploratory radius ASSUMED; source supplies no measured accuracy. Not a confidence interval.',
     'accuracy_verified':False,'permitted_use':'local_research_only','license':'ODbL 1.0',
     'independence_limit':'Crowdsourced records may share mapper, visit or original source; not confirmed GNSS ground truth'}})
(private/'references.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},indent=2)+'\n')
print(json.dumps({'public_map_references':len(features),'stated_accuracy_records':0,'assumed_radius_m':100,
                 'distinct_mappers':len(set(f['properties']['mapper_id'] for f in features))},indent=2))
