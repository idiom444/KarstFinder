#!/usr/bin/env python3
"""Verify grid alignment, mask handling, component geometry, and ranked attributes."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from osgeo import gdal,ogr

gdal.UseExceptions();ogr.UseExceptions()
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('path',nargs='?',default='results/blind_v001');args=ap.parse_args()
out=ROOT/args.path
cfg=json.loads((out/'config.json').read_text());summary=json.loads((out/'summary.json').read_text())
assert summary['status']=='exploratory_blind_unfrozen'
rasters={p.stem:gdal.Open(str(p)) for p in out.glob('*.tif') if '_buffered' not in p.stem}
ref=rasters['combined_score'];gt=ref.GetGeoTransform()
for name,ds in rasters.items():
    assert ds.GetGeoTransform()==gt,name
    assert (ds.RasterXSize,ds.RasterYSize)==(ref.RasterXSize,ref.RasterYSize),name
    assert ds.GetSpatialRef().GetAuthorityCode(None)=='26910',name
assert gt[1]==cfg['terrain_resolution_m'] and gt[5]==-cfg['terrain_resolution_m']
combined=ref.ReadAsArray();valid=rasters['analysis_valid'].ReadAsArray()==1
assert np.isfinite(combined[valid]).all() and (combined[valid]>=0).all() and (combined[valid]<=1).all()
assert (combined[~valid]==-9999).all()
vec=ogr.Open(str(out/'candidates.gpkg'));layer=vec.GetLayerByName('candidate_areas')
assert layer.GetFeatureCount()==summary['candidate_area_count']
features=list(layer)
for f in features:
    assert f.GetGeometryRef().IsValid()
    assert f.GetGeometryRef().GetArea()==f['area_m2']
    assert f['mean_score']>=cfg['candidate_min_score']
    assert f['area_m2']>=cfg['candidate_min_area_m2']
assert abs(sum(f['area_m2'] for f in features)/1e6-summary['candidate_area_km2'])<1e-9
rows=list(csv.DictReader((out/'candidates.csv').open()))
assert [int(r['rank']) for r in rows]==list(range(1,len(rows)+1))
assert [float(r['mean_score']) for r in rows]==sorted([float(r['mean_score']) for r in rows],reverse=True)
report={'raster_count':len(rasters),'candidate_count':len(rows),'all_grids_aligned':True,
        'geometries_valid':True,'scores_and_masks_valid':True,'area_totals_match':True}
print(json.dumps(report,indent=2))
