#!/usr/bin/env python3
"""Fresh-process verification of Denny products, repeatability and QGIS sources."""
import json
import os
import sqlite3
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np
from osgeo import gdal, ogr
from qgis.core import QgsApplication,QgsProject,QgsVectorLayer

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import sha
from karstfinder.freeze import verify_freeze
gdal.UseExceptions();ogr.UseExceptions()
report={}
for kind,ranking in [('landscape','candidates.csv'),('features','ranked_indicators.csv')]:
    first=ROOT/f'results/denny_v001_{kind}';second=ROOT/f'results/denny_v001_{kind}_repeat';checked=[]
    for path in first.glob('*.tif'):
        other=second/path.name;assert other.exists(),other
        a=gdal.Open(str(path));b=gdal.Open(str(other))
        assert a.GetGeoTransform()==b.GetGeoTransform()
        np.testing.assert_array_equal(a.ReadAsArray(),b.ReadAsArray());checked.append(path.name)
    assert (first/ranking).read_bytes()==(second/ranking).read_bytes()
    report[kind]={'identical_raster_arrays':len(checked),'ranking_csv_byte_identical':True}
for kind,filename in [('features','features.gpkg'),('access','access.gpkg')]:
    with sqlite3.connect(ROOT/f'results/denny_v001_{kind}'/filename) as first, sqlite3.connect(ROOT/f'results/denny_v001_{kind}_repeat'/filename) as second:
        tables=[r[0] for r in first.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            columns=[r[1] for r in first.execute(f'PRAGMA table_info("{table}")') if r[1]!='last_change']
            names=','.join('"'+c+'"' for c in columns)
            a=first.execute(f'SELECT {names} FROM "{table}"').fetchall()
            b=second.execute(f'SELECT {names} FROM "{table}"').fetchall()
            assert a==b,(kind,table)
    report[kind+'_geopackage_rows_match_repeat_except_creation_timestamps']=True
for manifest in ['denny_v001_acquisition.json','denny_v001_access_sources.json']:
    for record in json.loads((ROOT/'docs/experiments'/manifest).read_text()):
        assert sha(ROOT/record['path'])==record['sha256'],record['path']
access=ogr.Open(str(ROOT/'results/denny_v001_access/access.gpkg'))
trails=access.GetLayerByName('trails');trails.SetAttributeFilter("trail_name='DENNY CREEK'")
geoms=[f.GetGeometryRef().Clone() for f in trails]
obs=ogr.Open(str(ROOT/'results/denny_v001_observation/observation.gpkg'))
stations=obs.GetLayerByName('trail_observation_points')
for f in stations:
    assert min(g.Distance(f.GetGeometryRef()) for g in geoms)<.01
    assert 0<=f['modeled_visible_marble_fraction']<=1
assert stations.GetFeatureCount()==3
points=access.GetLayerByName('screened_indicators');assert points.GetFeatureCount()==489
marble_count=0
for f in points:
    assert f['route_verified']==0 and f['hiking_ready']==0
    assert f['trail_distance_m']>=0 and 0<=f['object_fs_fraction']<=1
    if f['mapped_marble_overlap_m2']>0:
        assert f['kind']=='cliff';marble_count+=1
assert marble_count==48
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance()
assert p.read(str(ROOT/'qgis/KarstFinder_Denny_v001.qgz'))
counts={}
for layer in p.mapLayers().values():
    assert layer.isValid(),layer.name()
    assert 'data/private' not in layer.source() and 'validation.gpkg' not in layer.source()
    if isinstance(layer,QgsVectorLayer):
        count=layer.featureCount();assert count>=0,layer.name();counts[layer.name()]=count
assert len(p.mapLayers())==28
assert counts['48 cliff patches overlapping mapped marble']==48
assert counts['Mapped marble PMmb(e) • approximate contacts']==1
assert counts['OBS triangles • ON mapped trail; canopy visibility unknown']==3
report.update(observation_points_on_official_trail=3,access_screen_count=489,
              direct_mapped_marble_cliffs=48,project_layers=len(p.mapLayers()),
              fresh_process_vector_counts=counts,entrance_reference_layers=0,
              source_hashes_verified=True,cave_ridge_frozen_hashes_verified=len(verify_freeze(ROOT)['sha256']))
(ROOT/'docs/experiments/denny_v001_reproducibility.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
