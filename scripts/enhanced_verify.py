#!/usr/bin/env python3
"""Independent saved-output, baseline-preservation and fresh-library verification."""
import argparse,csv,json,os,sys
from pathlib import Path
import numpy as np
from osgeo import ogr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,sha,write_json
from karstfinder.enhanced.registry import geom_key
from karstfinder.enhanced.scoring import color,combine,morphology
from karstfinder.freeze import verify_freeze
from karstfinder.library import Library


def main():
    p=argparse.ArgumentParser();p.add_argument('--without-library',action='store_true');args=p.parse_args()
    baseline=json.loads((ROOT/'docs/enhanced_v001/baseline_audit.json').read_text())
    for name,digest in baseline['scientific_file_sha256'].items():assert sha(safe_path(name))==digest,name
    report={'baseline_file_hashes_preserved':len(baseline['scientific_file_sha256']),'initial_blind_freeze_hashes':len(verify_freeze(ROOT)['sha256']),'areas':{}}
    lib=Library(ROOT);original=json.loads((ROOT/'docs/enhanced_v001/baseline_library_catalog.json').read_text())
    for entry in original['areas']:assert lib.entry(entry['area_id'])==entry,entry['area_id']
    for area_id,area in config()['areas'].items():
        out=safe_path(area['result_dir']);rows=json.loads((out/'candidate_evidence.json').read_text());csvrows=list(csv.DictReader((out/'candidates.csv').open()))
        old={r['object_id']:r for r in csv.DictReader(safe_path(area['baseline_candidate_csv']).open())}
        complete=json.loads((out/'baseline_measurement_records.json').read_text())
        assert complete['source_sha256']==sha(safe_path(area['baseline_candidate_csv']))
        assert complete['records']=={area_id+':'+key:value for key,value in old.items()}
        legacy={r['baseline_object_id']:r for r in rows if r['baseline_object_id']};assert set(legacy)==set(old)
        for ident,r in legacy.items():
            assert r['easting']==float(old[ident]['easting']) and r['northing']==float(old[ident]['northing'])
            assert r['baseline_rank']==int(old[ident]['rank']) and r['baseline_score']==float(old[ident]['score'])
            assert r['baseline_prediction_sha256']==sha(safe_path(area['baseline_candidate_csv']))
        baseline_ds=ogr.Open(str(safe_path(area['baseline_features'])/'features.gpkg'))
        for f in baseline_ds.GetLayerByName('surface_indicators'):
            assert legacy[f['object_id']]['geometry_sha256']==geom_key(f['kind'],f.GetGeometryRef())
        assert len({r['object_id'] for r in rows})==len(rows)==len(csvrows)
        for r,c in zip(rows,csvrows):
            assert r['score']==r['evidence_strength']==float(c['score'])
            assert r['score']==combine(r['evidence_components'])[0]
            assert r['color_hex']==color(r['score'])
            depth=r['measurements']['depth']
            residuals=[(r['measurements'][f'residual_{w}m'] or {}).get('q10') for w in [11,31,61]]
            assert r['terrain_component']==morphology(r['kind'],depth['max'] if depth else None,residuals)
            assert r['fieldwork_status']=='Not yet investigated'
            assert r['has_pointcloud']==int((r['measurements']['pointcloud_ground_return_count'] or {}).get('max',0)>0)
            assert not r['independently_blind']
        manifest=json.loads((out/'run_manifest.json').read_text())
        for group in ['inputs','outputs']:
            for name,digest in manifest[group].items():assert sha(safe_path(name))==digest,name
        info={'retained_originals':len(legacy),'all_leads':len(rows),'weak_below_025':sum(r['score']<.25 for r in rows),'pointcloud_covered':sum(r['has_pointcloud'] for r in rows),'baseline_coordinates_ranks_scores_geometries_unchanged':True}
        if not args.without_library:info['library']=lib.verify(area['enhanced_library_id'])
        report['areas'][area_id]=info
    # Repeat baseline hashes after fresh providers have opened everything.
    for name,digest in baseline['scientific_file_sha256'].items():assert sha(safe_path(name))==digest,name
    write_json(ROOT/'docs/enhanced_v001/verification.json',report);print(json.dumps(report,indent=2))


if __name__=='__main__':main()
