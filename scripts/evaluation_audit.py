#!/usr/bin/env python3
"""Supplemental evaluation audit: tie-averaged baselines and shape-preserving conditional null."""
import json,sys
from pathlib import Path
import numpy as np
from osgeo import gdal,osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.freeze import verify_freeze
from karstfinder.gis import array
from karstfinder.evaluation import select_area
verify_freeze(ROOT);gdal.UseExceptions();osr.UseExceptions()
private=ROOT/'data/private/validation';refs=json.loads((private/'references.geojson').read_text())['features']
ref=gdal.Open(str(ROOT/'results/blind_v002/geology_score_10m.tif'));gt=ref.GetGeoTransform();geo=array(ROOT/'results/blind_v002/geology_score_10m.tif');shape=geo.shape
s=osr.SpatialReference();s.ImportFromEPSG(4326);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);tx=osr.CoordinateTransformation(s,ref.GetSpatialRef())
positions=[]
for f in refs:
 x,y,_=tx.TransformPoint(*f['geometry']['coordinates']);positions.append((int((gt[3]-y)/10),int((x-gt[0])/10)))
positions=np.asarray(positions);offsets=positions-positions[0]
# Translate the whole reference configuration rigidly, preserving observed spatial association.
# Accept only placements with the same geological evidence class at every reference.
anchors=np.argwhere(geo>0);keep=np.ones(len(anchors),bool)
for pos,off in zip(positions,offsets):
 targets=anchors+off;inside=(targets[:,0]>=0)&(targets[:,0]<shape[0])&(targets[:,1]>=0)&(targets[:,1]<shape[1]);same=np.zeros(len(anchors),bool)
 same[inside]=geo[targets[inside,0],targets[inside,1]]==geo[tuple(pos)];keep&=same
anchors=anchors[keep];rng=np.random.default_rng(20261019)
if len(anchors)>999:anchors=anchors[rng.choice(len(anchors),999,replace=False)]
models={'geology':geo,'terrain':array(ROOT/'results/blind_v001/terrain_score.tif'),'landscape_v001':array(ROOT/'results/blind_v001/combined_score.tif'),
 'morphology':array(ROOT/'results/blind_v002/feature_score_10m.tif'),'combined_v002':array(ROOT/'results/blind_v002/combined_score_10m.tif')}
universe=geo>0;n=int(universe.sum());rows=[]
for name,scores in models.items():
 for budget in [.01,.05,.1,.2]:
  positive=universe&np.isfinite(scores)&(scores>0);k=min(int(n*budget),int(positive.sum()))
  selected=select_area(scores,positive,k/positive.sum()) if k else np.zeros(shape,bool)
  probs=[]
  for pos in positions:
   value=scores[tuple(pos)]
   if value<=0:probs.append(0.);continue
   above=int((positive&(scores>value)).sum());equal=int((positive&(scores==value)).sum());probs.append(float(np.clip((k-above)/equal,0,1)))
  simulated=np.zeros(len(anchors),float)
  for off in offsets:
   target=anchors+off;simulated+=selected[target[:,0],target[:,1]]/len(offsets)
  observed=float(selected[positions[:,0],positions[:,1]].mean())
  rows.append({'model':name,'requested_area_fraction':budget,'actual_area_fraction':float(selected.sum()/n),
   'central_reference_fraction_selected':observed,'tie_averaged_expected_central_fraction':float(np.mean(probs)),
   'matched_geology_rigid_translation_mean_fraction':float(simulated.mean()) if simulated.size else None,
   'matched_geology_rigid_translation_5_95_interval':np.percentile(simulated,[5,95]).tolist() if simulated.size else None})
report={'evaluation_stage':'supplemental post-freeze audit; predictions and primary protocol unchanged','reference_count':len(refs),
 'independent_reference_spatial_configurations':1,'accepted_null_placements':len(anchors),
 'null_design':'Whole reference point pattern translated jointly on 10 m grid, requiring identical geological evidence class for each point',
 'inferential_p_values_reported':False,'limitation':'All locations remain unverified, spatially associated and from one mapper. Translation-null results are descriptive, not an independent randomized experiment.',
 'metrics':rows}
(ROOT/'docs/validation_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='metrics'},indent=2))
