#!/usr/bin/env python3
"""Register enhanced maps through the existing Library, never replace originals."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,write_json,safe_path
from karstfinder.library import Library

p=argparse.ArgumentParser();p.add_argument('area',choices=config()['areas']);a=p.parse_args()
cfg,area=config(a.area);identifier=area['enhanced_library_id'];out=safe_path(area['result_dir'])
spec={'name':area['name']+' — Enhanced Analysis v001','general_location':area['name']+', Washington Cascades',
 'study_extent':{'crs':'EPSG:26910','bounds':area['study_bounds']},
 'geological_summary':'Unvalidated union of preserved original leads and enhanced terrain/hydrological hypotheses. DNR 1:100,000 carbonate/mixed-unit zones; unknown geology retained. Continuous ordinal evidence strength, separate uncertainty. No cave entrance or access route confirmed.',
 'candidate_csv':str((out/'candidates.csv').relative_to(ROOT)),
 'analysis_references':['configs/enhanced_v001.json','docs/enhanced_v001/METHODOLOGY.md','docs/enhanced_v001/GEOLOGY_SOURCES.md',str((out/'run_manifest.json').relative_to(ROOT))]}
path=ROOT/f'docs/enhanced_v001/{a.area}_library_spec.json';write_json(path,spec)
lib=Library(ROOT)
result=lib.save(identifier,specification=spec,project=ROOT/f'qgis/KarstFinder_{a.area}_enhanced_v001.qgz')
print(json.dumps({k:result[k] for k in ['area_id','candidate_count','layer_count','project_path']},indent=2))
