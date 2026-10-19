#!/usr/bin/env python3
"""Hash and protect a finished unvalidated area; never label it a blind freeze."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha
from karstfinder.freeze import verify_freeze


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('area', choices=['kaleetan', 'marble'])
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(); area = args.area+'_v001'
    path = ROOT / f'experiments/snapshots/{area}.json'
    old = verify_freeze(ROOT)
    denny = json.loads((ROOT / 'experiments/snapshots/denny_v001.json').read_text())
    for name, digest in denny['sha256'].items():
        assert sha(ROOT / name) == digest, name
    if args.verify:
        snapshot = json.loads(path.read_text())
        for name, digest in snapshot['sha256'].items():
            assert sha(ROOT / name) == digest, name
        print(json.dumps({'area': area, 'verified_hashes': len(snapshot['sha256']),
                          'original_cave_ridge_hashes': len(old['sha256']),
                          'original_denny_hashes': len(denny['sha256'])}, indent=2))
        return
    if path.exists():
        raise RuntimeError(f'Refusing snapshot overwrite: {path}')
    review = ROOT / f'docs/reviews/{area}_methodology'
    audit = json.loads((review / 'audit_summary.json').read_text())
    assert audit['repeat_comparison']['rasters'] == 31
    assert audit['maximum_measurement_difference'] < 1e-6
    cfg = json.loads((ROOT / f'configs/{area}_landscape.json').read_text())
    files = set((ROOT / 'src/karstfinder').glob('*.py')) | set((ROOT / 'scripts').glob('*.py'))
    files.update((ROOT / 'configs').glob(area+'_*.json'))
    files.update((ROOT / 'docs/experiments').glob(area+'_*'))
    files.update(review.glob('*'))
    files.update(ROOT / name for name in ['docs/APPROVED_AREAS_20261019.md',
        'docs/APPROVED_AREAS_RESULTS_20261019.md', f'docs/proposals/{area}_library_spec.json'])
    files.add(ROOT / f'qgis/KarstFinder_{args.area.title()}_v001.qgz')
    files.update((ROOT / cfg['processed_dir']).rglob('*'))
    for kind in ['landscape', 'features', 'access']:
        files.update((ROOT / f'results/{area}_{kind}').rglob('*'))
    for record in json.loads((ROOT / cfg['acquisition_manifest']).read_text()):
        source = ROOT / record['path']; assert sha(source) == record['sha256'], source
        files.add(source)
    for item in cfg['elevation_sources']:
        files.add(ROOT / item['path'])
        if item.get('conversion_record'):
            conversion = json.loads((ROOT / item['conversion_record']).read_text())
            files.add(ROOT / conversion['metadata_path'])
    files = sorted(p for p in files if p.is_file() and '__pycache__' not in p.parts)
    # Source code is pinned by exact hashes even if an external filesystem issue
    # currently prevents committing. Never misidentify the pre-work HEAD as the
    # commit containing the new implementation.
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    snapshot = {'snapshot_id': area, 'status': 'final_unvalidated_prospecting_snapshot',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'independent_blind_validation': False, 'literature_informed_area_selection': True,
        'entrance_records_used_as_model_inputs': False, 'cave_confirmation_performed': False,
        'git_head_at_snapshot': head, 'implementation_pinning': 'Exact local source-code SHA-256 values below; run manifests retain execution-time HEAD and dirty state.',
        'original_cave_ridge_hashes_verified': len(old['sha256']),
        'original_denny_hashes_verified': len(denny['sha256']),
        'interpretation': 'Reproducible landscape and surface-indicator hypotheses, not fitted cave probabilities, entrance detection or independent cave validation.',
        'sha256': {str(p.relative_to(ROOT)): sha(p) for p in files}}
    path.write_text(json.dumps(snapshot, indent=2)+'\n')
    # Editable review maps and the library are separate from numerical results.
    for kind in ['landscape', 'features', 'access']:
        folder = ROOT / f'results/{area}_{kind}'
        for item in folder.rglob('*'):
            item.chmod(0o555 if item.is_dir() else 0o444)
        folder.chmod(0o555)
    print(json.dumps({'snapshot': str(path.relative_to(ROOT)), 'hashes': len(files)}, indent=2))


if __name__ == '__main__':
    main()
