#!/usr/bin/env python3
"""Freeze a completed corrected analysis; never overwrite earlier experiments."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.carbonate.common import config, safe_path, sha, write_json, fingerprint

parser = argparse.ArgumentParser(); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
destination = ROOT / 'experiments/snapshots/carbonate_v001.json'
if args.verify:
    snapshot = json.loads(destination.read_text())
    for name, digest in snapshot['sha256'].items():
        assert sha(safe_path(name)) == digest, name
    print('Carbonate snapshot verified:', len(snapshot['sha256']), 'hashes')
    raise SystemExit()
if destination.exists():
    raise FileExistsError('Already frozen; use a new named experiment for revisions')
review = json.loads((ROOT / 'docs/carbonate_v001/verification.json').read_text())
maps = json.loads((ROOT / 'docs/carbonate_v001/map_review.json').read_text())
assert len(review['areas']) == len(maps['areas']) == 4
assert all('library' in v for v in review['areas'].values())
assert all('live_state' in v for v in maps['areas'].values())
files = [ROOT / 'configs/carbonate_v001.json', ROOT / 'tests/test_carbonate.py']
files += list((ROOT / 'src/karstfinder/carbonate').glob('*.py'))
files += [ROOT / 'scripts' / name for name in ['run_carbonate.py', 'make_carbonate_map.py', 'verify_carbonate.py', 'carbonate_library.py', 'review_carbonate_maps.py', 'carbonate_freeze.py']]
files += [f for f in (ROOT / 'docs/carbonate_v001').glob('*') if f.is_file()]
for aid, area in config()['areas'].items():
    for folder in [safe_path(area['result_dir']), safe_path(area['processed_dir'])]:
        files += [f for f in folder.rglob('*') if f.is_file()]
    folder = ROOT / 'prospecting_library' / area['library_id']
    files += list(folder.glob('map-v*.qgz')) + list((folder / 'versions').glob('*'))
    files.append(ROOT / f'qgis/KarstFinder_{aid}_carbonate_v001.qgz')
    manifest = json.loads((safe_path(area['result_dir']) / 'manifest.json').read_text())
    files += [safe_path(name) for name in manifest['inputs']]
files = sorted(set(files))
for area in config()['areas'].values():
    for directory in [safe_path(area['result_dir']), safe_path(area['processed_dir'])]:
        for f in directory.rglob('*'):
            f.chmod(0o555 if f.is_dir() else 0o444)
        directory.chmod(0o555)
write_json(destination, {'experiment_id': 'carbonate_v001', 'priority_model': 'carbonate_priority_v001',
                        'status': 'Corrected carbonate-only unvalidated prospecting; not an independently blind validation',
                        'known_cave_inputs_used': False, 'independently_blind': False,
                        'implementation_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=ROOT).strip(),
                        'sha256': fingerprint(files)})
print('Frozen carbonate snapshot:', len(files), 'files')
