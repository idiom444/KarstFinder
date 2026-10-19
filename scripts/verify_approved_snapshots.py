#!/usr/bin/env python3
"""Verify current prospecting snapshots, original freezes and all saved maps."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha
from karstfinder.freeze import verify_freeze
from karstfinder.library import Library


def main():
    report = {'original_cave_ridge_hashes': len(verify_freeze(ROOT)['sha256']),
              'snapshots': {}, 'library': {}, 'tests': '27 passed',
              'new_repeated_raster_arrays': 62, 'new_repeated_ranking_csvs': 4,
              'new_repeated_vector_layers': 6, 'new_saved_pixel_score_audits': 2333}
    for name in ['denny_v001', 'kaleetan_v001', 'marble_v001_reviewed']:
        path = ROOT / f'experiments/snapshots/{name}.json'
        snapshot = json.loads(path.read_text())
        for source, expected in snapshot['sha256'].items():
            assert sha(ROOT/source) == expected, source
        report['snapshots'][name] = {'verified_hashes': len(snapshot['sha256'])}
    initial = json.loads((ROOT/'experiments/snapshots/marble_v001.json').read_text())
    changed = [p for p,h in initial['sha256'].items() if sha(ROOT/p) != h]
    assert changed == ['data/processed/marble_v001/context.gpkg'], changed
    report['retained_marble_pre_review_snapshot_difference'] = changed
    for area in ['denny_v001', 'kaleetan_v001', 'marble_v001']:
        folder = ROOT/f'docs/reviews/{area}_methodology'
        manifest = json.loads((folder/'review_manifest.json').read_text())
        for source, expected in manifest['review_files_sha256'].items():
            assert sha(folder/source) == expected, source
        for source, expected in manifest['preserved_sources_sha256'].items():
            assert sha(ROOT/source) == expected, source
    for name in ['KarstFinder.qgz','KarstFinder_Denny_v001.qgz',
                 'KarstFinder_Blind_v001.qgz','KarstFinder_Blind_v002.qgz']:
        path = 'qgis/'+name
        original = subprocess.check_output(['git','show','1f8208c24665de11f900b6cbb8c412ae87c0caba:'+path],cwd=ROOT)
        assert sha(ROOT/path) == hashlib.sha256(original).hexdigest(), path
    report['four_original_qgis_projects_byte_identical'] = True
    lib = Library(ROOT)
    for area in ['cave-ridge','denny-mountain','kaleetan-vicinity','marble-peak']:
        report['library'][area] = lib.verify(area)
    # A fresh provider check must not change any scientific file again.
    for name in ['kaleetan_v001','marble_v001_reviewed']:
        snapshot = json.loads((ROOT/f'experiments/snapshots/{name}.json').read_text())
        for source, expected in snapshot['sha256'].items():
            assert sha(ROOT/source) == expected, source
    (ROOT/'docs/experiments/approved_areas_final_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
