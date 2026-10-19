#!/usr/bin/env python3
"""Preserve existing rankings and audit their measurements; no acquisition or refit."""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,sha
from karstfinder.freeze import verify_freeze

gdal.UseExceptions();ogr.UseExceptions()
ap=argparse.ArgumentParser()
ap.add_argument('--output',default='docs/reviews/denny_v001_methodology')
ap.add_argument('--verify',action='store_true')
args=ap.parse_args();out=ROOT/args.output


def check_snapshots():
    snapshot=json.loads((ROOT/'experiments/snapshots/denny_v001.json').read_text())
    for name,digest in snapshot['sha256'].items():
        assert sha(ROOT/name)==digest,name
    original=verify_freeze(ROOT)
    return len(snapshot['sha256']),len(original['sha256'])


before=check_snapshots()
if args.verify:
    manifest=json.loads((out/'review_manifest.json').read_text())
    for name,digest in manifest['review_files_sha256'].items():
        assert sha(out/name)==digest,name
    for name,digest in manifest['preserved_sources_sha256'].items():
        assert sha(ROOT/name)==digest,name
    print(json.dumps({'review_files_verified':len(manifest['review_files_sha256']),
                      'denny_snapshot_hashes_verified':before[0],
                      'cave_ridge_hashes_verified':before[1]},indent=2))
    raise SystemExit(0)
if out.exists():raise SystemExit(f'Refusing review overwrite: {out}')
out.mkdir(parents=True)
preserve={
    'landscape_candidates.csv':'results/denny_v001_landscape/candidates.csv',
    'ranked_indicators.csv':'results/denny_v001_features/ranked_indicators.csv',
    'screened_indicators.csv':'results/denny_v001_access/screened_indicators.csv',
    'landscape_config.json':'configs/denny_v001_landscape.json',
    'feature_config.json':'configs/denny_v001_features.json',
}
for name,source in preserve.items():shutil.copyfile(ROOT/source,out/name)
cfg=json.loads((out/'feature_config.json').read_text())
feature=ROOT/'results/denny_v001_features'
rasters={name:array(feature/f'{name}.tif') for name in
         ['geological_evidence_1m','slope_1m','residual_11m','depression_depth_1m','feature_quality_1m','source_epoch_1m']}
terrain=np.repeat(np.repeat(array(ROOT/'results/denny_v001_landscape/terrain_score.tif'),10,axis=0),10,axis=1)
ref=gdal.Open(str(feature/'slope_1m.tif'));gt=ref.GetGeoTransform()
source=ogr.Open(str(feature/'features.gpkg'))
polygons={f['object_id']:f.GetGeometryRef().Clone() for f in source.GetLayerByName('surface_indicators')}
rows=list(csv.DictReader((out/'ranked_indicators.csv').open()))
access=list(csv.DictReader((out/'screened_indicators.csv').open()))
assert [(r['object_id'],r['rank']) for r in rows]==[(r['object_id'],r['rank']) for r in access]
audited=[];max_error=0.
for row in rows:
    geom=polygons[row['object_id']];xmin,xmax,ymin,ymax=geom.GetEnvelope()
    col=int(round((xmin-gt[0])/gt[1]));r=int(round((gt[3]-ymax)/-gt[5]))
    width=int(round((xmax-xmin)/gt[1]));height=int(round((ymax-ymin)/-gt[5]))
    mask=gdal.GetDriverByName('MEM').Create('',width,height,1,gdal.GDT_Byte)
    mask.SetProjection(ref.GetProjection());mask.SetGeoTransform((xmin,gt[1],0,ymax,0,gt[5]))
    vector=ogr.GetDriverByName('MEM').CreateDataSource('')
    layer=vector.CreateLayer('object',ref.GetSpatialRef(),ogr.wkbPolygon)
    f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(geom);layer.CreateFeature(f)
    gdal.RasterizeLayer(mask,[1],layer,burn_values=[1]);valid=mask.ReadAsArray().astype(bool)
    sl=np.s_[r:r+height,col:col+width]
    g=float(rasters['geological_evidence_1m'][sl][valid].mean())
    t=float(terrain[sl][valid].mean())
    slope=float(rasters['slope_1m'][sl][valid].mean())
    residual=float(rasters['residual_11m'][sl][valid].min())
    depth=float(rasters['depression_depth_1m'][sl][valid].max())
    f_score=min(1,depth/3) if row['kind']=='depression' else .5*np.clip((slope-45)/30,0,1)+.5*np.clip(-residual/2,0,1)
    weights=cfg['feature_weights']
    contribution=[weights['geology']*g,weights['landscape']*t,weights['morphology']*f_score]
    score=sum(contribution)
    measured={'area_m2':float(valid.sum()),'geo_score':g,'terrain_score':t,
              'mean_slope_deg':slope,'min_residual_m':residual,'max_depth_m':depth,
              'morphology_score':float(f_score),'score':float(score),
              'carbonate_fraction':float((rasters['geological_evidence_1m'][sl][valid]>0).mean()),
              'fraction_2021':float((rasters['source_epoch_1m'][sl][valid]==2021).mean())}
    errors=[abs(value-float(row[key])) for key,value in measured.items()]
    max_error=max(max_error,*errors)
    assert max(errors)<1e-6,(row['object_id'],measured)
    assert (rasters['feature_quality_1m'][sl][valid]==1).all(),row['object_id']
    audited.append({'object_id':row['object_id'],'rank':int(row['rank']),'kind':row['kind'],
                    'rank_within_kind':int(row['rank_within_kind']),
                    'geology_contribution':contribution[0],'terrain_contribution':contribution[1],
                    'morphology_contribution':contribution[2],'recomputed_score':float(score),
                    'stored_score':float(row['score']),'maximum_measurement_difference':max(errors)})
assert [int(r['rank']) for r in rows]==list(range(1,len(rows)+1))
expected=sorted(rows,key=lambda r:(-float(r['score']),-float(r['morphology_score']),r['kind'],float(r['easting']),float(r['northing'])))
assert [r['object_id'] for r in rows]==[r['object_id'] for r in expected]
for kind in ['cliff','depression']:
    assert [int(r['rank_within_kind']) for r in rows if r['kind']==kind]==list(range(1,sum(r['kind']==kind for r in rows)+1))
with (out/'score_audit.csv').open('w') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(audited[0]));writer.writeheader();writer.writerows(audited)
marble=[r for r in access if float(r['mapped_marble_overlap_m2'])>0]
top=access[:10]
table=['| Map rank | Object ID | Area m² | Mean slope ° | Min residual m | G | T | F | Combined | Trail gap m |',
       '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for row in top:
    table.append(f"| C{row['rank_within_kind']} | {row['object_id']} | {float(row['area_m2']):.0f} | {float(row['mean_slope_deg']):.3f} | {float(row['min_residual_m']):.3f} | {float(row['geo_score']):.3f} | {float(row['terrain_score']):.6f} | {float(row['morphology_score']):.6f} | {float(row['score']):.6f} | {float(row['trail_distance_m']):.1f} |")
(out/'top10_evidence.md').write_text('# Existing top-ten cliff evidence\n\nRounded display; the byte-identical CSVs retain original precision. No ranks changed.\n\n'+'\n'.join(table)+'\n')
report={'ranked_objects':len(rows),'cliffs':sum(r['kind']=='cliff' for r in rows),
        'depressions':sum(r['kind']=='depression' for r in rows),'marble_overlap_objects':len(marble),
        'marble_overlap_depressions':sum(r['kind']=='depression' for r in marble),
        'core_score_and_geometry_measurements_recomputed_from_saved_object_pixels':True,
        'audited_measurement_fields':list(measured),
        'maximum_measurement_difference':max_error,'deterministic_ranking_verified':True,
        'native_G_equal_one_pixels':int((rasters['geological_evidence_1m']==1).sum()),
        'comparison_geological_support_km2':float((array(feature/'geology_score_10m.tif')>0).sum()*100/1e6),
        'sum_object_areas_m2':sum(float(r['area_m2']) for r in rows),
        'marble_object_area_sum_m2':sum(float(r['area_m2']) for r in marble),
        'vector_marble_overlap_area_sum_m2':sum(float(r['mapped_marble_overlap_m2']) for r in marble),
        'cave_reference_data_read':False,'network_requests':0,'rankings_or_models_modified':False,
        'meaning':'Numerical traceability audit, not independent validation of cave-prediction skill.'}
(out/'audit_summary.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'methodology_at_review.md').write_bytes((ROOT/'METHODOLOGY.md').read_bytes())
(out/'README.md').write_text('''# Preserved Denny methodology review\n\nThis is a review of existing unvalidated predictions, not a new model run or\ncave-location search. No original candidate rank, measurement or geometry was\nchanged. Computational coordinates describe model objects, not known entrances.\n\n- `landscape_candidates.csv`: exact original one-area landscape CSV.\n- `ranked_indicators.csv`: exact original 489-object ranking and evidence fields.\n- `screened_indicators.csv`: exact 489-object ranking plus separate access and\n  mapped-marble intersection measurements; no access-based reordering.\n- Config JSONs: byte-identical executable parameters.\n- `score_audit.csv`: existing IDs/ranks and recomputed weighted contributions.\n- `top10_evidence.md`: rounded display of the unchanged top-ten cliff evidence.\n- `audit_summary.json`: explicit fields checked against saved object pixels.\n- `methodology_at_review.md`: methodology text at this review; later changes to\n  the working methodology do not change this preserved explanation.\n- `review_manifest.json`: original-source and bundle-file SHA-256 hashes.\n\nOriginal polygons/representative points remain in the write-protected\n`results/denny_v001_features/features.gpkg`; original GeoTIFFs retain the pixel\nmeasurements. The existing 144-file snapshot is not overwritten. Refer to\n`experiments/snapshots/denny_v001.json` for final geometry/raster/config hashes\nand committed implementation. Initial provider metadata differences are explained\nin `docs/experiments/denny_v001_provider_audit.json`.\n\nFrom the repository root, verify without rerunning the models or reading cave\nreferences:\n\n```bash\n.venv/bin/python scripts/audit_denny_methodology.py --verify\n```\n\nTo independently repeat the pixel audit into a new review directory, run the\nsame script with a new `--output` path. Existing review directories are refused.\nThe audit verifies model-raster arithmetic and rank consistency; it does not\nvalidate that any object is a cave or that a cliff is safely reachable.\n''')
assert check_snapshots()==before
manifest={'source_snapshot':'experiments/snapshots/denny_v001.json',
          'source_implementation_git_commit':'dfaf523',
          'audit_script_sha256':sha(Path(__file__)),
          'preserved_sources_sha256':{source:sha(ROOT/source) for source in preserve.values()},
          'review_files_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},
          'snapshot_hashes_verified_before_and_after':{'denny':before[0],'cave_ridge':before[1]}}
(out/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
