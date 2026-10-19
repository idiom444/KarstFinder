#!/usr/bin/env python3
"""Check both real saved investigations and the unchanged original evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.library import Library, read_json, sha, write_json, now
from karstfinder.freeze import verify_freeze

# Last commit before library implementation; archived originals stay recoverable.
ORIGINAL_PROJECT_COMMIT = '1f8208c24665de11f900b6cbb8c412ae87c0caba'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', metavar='AREA_ID', help='Also compare the currently open MCP map; does not change it')
    args = parser.parse_args()
    lib = Library(ROOT)
    report = {'verified_utc': now(), 'areas': {}, 'no_analysis_rerun': True}
    for area_id, expected_layers, expected_candidates in (
            ('denny-mountain', 28, 489), ('cave-ridge', 36, 596)):
        entry = lib.entry(area_id)
        result = lib.verify(area_id)
        assert result['layer_count'] == expected_layers, result
        assert result['candidate_count'] == expected_candidates, result
        # Generate a current verification report without overwriting an archived
        # revision's original evidence record.
        current_report = lib.area_dir(area_id) / 'local' / 'latest_verification.json'
        current_report.parent.mkdir(exist_ok=True)
        lib._qgis('verify', '--project', lib.path(entry['project_path']),
                  '--state', lib.path(entry['state_path']), '--report', current_report,
                  '--repo', ROOT, '--candidates', lib.path(entry['candidate_csv']))
        fresh = read_json(current_report)
        result['candidate_table_check'] = fresh['candidate_table_check']
        result['vector_counts'] = fresh['vector_counts']
        result['map_revision'] = entry['map_revision']
        result['project_path'] = entry['project_path']
        result['project_sha256'] = entry['project_sha256']
        result['view_extent'] = read_json(lib.path(entry['state_path']))['view_extent']
        if area_id == 'denny-mountain':
            counts = result['vector_counts']
            assert counts['All indicators • geological rank + access flags'] == 489
            assert counts['48 cliff patches overlapping mapped marble'] == 48
            assert counts['Top 10 marble priorities • steep/off-trail; NOT destinations'] == 10
            assert counts['OBS triangles • ON mapped trail; canopy visibility unknown'] == 3
        report['areas'][area_id] = result
    report['original_cave_ridge_frozen_hashes_verified'] = len(verify_freeze(ROOT)['sha256'])
    snapshot = read_json(ROOT / 'experiments/snapshots/denny_v001.json')
    for path, expected in snapshot['sha256'].items():
        if sha(ROOT / path) != expected:
            raise RuntimeError(f'Denny scientific snapshot changed: {path}')
    report['denny_scientific_snapshot_hashes_verified'] = len(snapshot['sha256'])
    originals = {}
    for path in ('qgis/KarstFinder.qgz', 'qgis/KarstFinder_Denny_v001.qgz',
                 'qgis/KarstFinder_Blind_v001.qgz', 'qgis/KarstFinder_Blind_v002.qgz'):
        blob = subprocess.check_output(['git', 'show', ORIGINAL_PROJECT_COMMIT + ':' + path], cwd=ROOT)
        expected = hashlib.sha256(blob).hexdigest()
        assert sha(ROOT / path) == expected, f'Original project changed: {path}'
        originals[path] = expected
    report['unchanged_original_projects'] = originals
    for actual, copy in [('results/denny_v001_features/ranked_indicators.csv', 'ranked_indicators.csv'),
                         ('results/denny_v001_access/screened_indicators.csv', 'screened_indicators.csv')]:
        assert sha(ROOT / actual) == sha(ROOT / 'docs/reviews/denny_v001_methodology' / copy)
    report['original_denny_ranking_csvs_byte_identical_to_methodology_review'] = True
    if args.live:
        from karstfinder.qgis_bridge import request
        entry = lib.entry(args.live)
        code = ('import json, importlib\nfrom karstfinder import library_qgis\n'
                'importlib.reload(library_qgis)\np = QgsProject.instance()\n'
                f'expected = json.load(open({str(lib.path(entry["state_path"]))!r}))\n'
                'actual = library_qgis.state(p)\nr = iface.mapCanvas().extent()\n'
                'print(json.dumps({"filename": p.fileName(), '
                '"state_differences": [k for k in expected if expected[k] != actual.get(k)], '
                '"extent": [r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum()], '
                '"expected_extent": expected["view_extent"], "rotation": iface.mapCanvas().rotation()}))')
        response = request('execute_code', {'code': code})
        if not response.get('executed'):
            raise RuntimeError(response)
        live = json.loads(response['stdout'])
        assert Path(live['filename']).resolve() == lib.path(entry['project_path']), live
        assert not live['state_differences'], live
        # Same workstation/window: compare exact captured extent. A different
        # window aspect ratio legitimately expands it when reopened manually.
        assert all(abs(a-b) < 1e-7 for a, b in zip(live['extent'], live['expected_extent'])), live
        report['live_mcp_reopen'] = live
    write_json(ROOT / 'docs/PROSPECTING_LIBRARY_VERIFICATION.json', report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
