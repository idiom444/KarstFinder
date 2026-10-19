#!/usr/bin/env python3
"""Independent artifact invariants for native feature objects and their representative points."""
import json,sys
from pathlib import Path
import numpy as np
from osgeo import gdal,ogr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array

gdal.UseExceptions();ogr.UseExceptions();out=ROOT/'results/blind_v002'
summary=json.loads((out/'summary.json').read_text());ds=ogr.Open(str(out/'features.gpkg'));poly=ds.GetLayerByName('surface_indicators');pts=ds.GetLayerByName('ranked_indicators')
assert poly.GetFeatureCount()==pts.GetFeatureCount()==summary['surface_indicators']
geos={f['object_id']:f.GetGeometryRef().Clone() for f in poly}
quality=array(out/'feature_quality_1m.tif');geo=array(out/'geological_evidence_1m.tif');ref=gdal.Open(str(out/'depression_depth_1m.tif'));gt=ref.GetGeoTransform()
seen=[]
for f in pts:
 pt=f.GetGeometryRef();r=int((gt[3]-pt.GetY())/-gt[5]);c=int((pt.GetX()-gt[0])/gt[1])
 assert quality[r,c]==1 and geo[r,c]>0
 assert geos[f['object_id']].Intersects(pt)
 assert geos[f['object_id']].IsValid()
 assert 0<=f['score']<=1 and 0<=f['carbonate_fraction']<=1
 assert abs(geos[f['object_id']].GetArea()-f['area_m2'])<1e-6
 seen.append(f['rank'])
assert sorted(seen)==list(range(1,len(seen)+1))
report={'surface_objects':len(seen),'all_polygons_valid':True,'representative_points_in_supported_objects':True,
        'quality_and_geology_support_verified':True,'rank_ids_complete':True,'confirmed_caves':0}
(ROOT/'docs/experiments/blind_v002_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
