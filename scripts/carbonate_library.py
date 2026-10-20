#!/usr/bin/env python3
"""Register the four new carbonate maps without changing earlier Library entries."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.carbonate.common import config
from karstfinder.library import Library

parser = argparse.ArgumentParser()
parser.add_argument('area', choices=list(config()['areas']) + ['all'])
args = parser.parse_args()
lib = Library(ROOT)
for aid in config()['areas'] if args.area == 'all' else [args.area]:
    area = config()['areas'][aid]
    try:
        lib.entry(area['library_id'])
    except KeyError:
        pass
    else:
        raise FileExistsError('Already registered; use ./library save for later map revisions: ' + area['library_id'])
    spec = {'name': area['name'] + ' — Carbonate prospecting v001',
            'general_location': area['name'] + ', Washington; existing approved study window',
            'study_extent': {'crs': 'EPSG:26910', 'bounds': area['study_bounds']},
            'geological_summary': 'Explicit DNR mapped marble plus a flagged 25 m contact-review margin. Mixed/unknown formations excluded. Unvalidated ordinal prospecting; coordinates are surface reference points, not entrances or access routes.',
            'candidate_csv': area['result_dir'] + '/candidates.csv',
            'analysis_references': ['configs/carbonate_v001.json',
                                    'docs/carbonate_v001/METHODOLOGY.md',
                                    'docs/carbonate_v001/GEOLOGY_EVIDENCE.json',
                                    'docs/carbonate_v001/RESULTS.md',
                                    area['result_dir'] + '/manifest.json',
                                    area['result_dir'] + '/summary.json']}
    saved = lib.save(area['library_id'], specification=spec,
                     project=ROOT / f'qgis/KarstFinder_{aid}_carbonate_v001.qgz')
    print(saved['area_id'], saved['candidate_count'], 'sites saved', flush=True)
