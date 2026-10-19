"""Verify a blind freeze before validation can access local reference records."""
import json
import hashlib
import subprocess
from pathlib import Path
from .gis import sha


def verify_freeze(root,freeze_id='blind_v002'):
    root=Path(root);path=root/'experiments/frozen'/f'{freeze_id}.json'
    if not path.exists():raise RuntimeError('No blind freeze exists; cave validation is prohibited')
    manifest=json.loads(path.read_text())
    if manifest.get('status')!='frozen_before_validation':raise RuntimeError('Invalid freeze state')
    for name,digest in manifest['sha256'].items():
        file=root/name
        if (name.startswith(('src/','scripts/','tests/')) and name.endswith('.py')) or name in ['requirements.lock','pyproject.toml']:
            blob=subprocess.check_output(['git','show',manifest['implementation_git_commit']+':'+name],cwd=root)
            actual=hashlib.sha256(blob).hexdigest()
        else:
            actual=sha(file) if file.exists() else None
        if actual!=digest:raise RuntimeError(f'Frozen artifact changed: {name}')
    return manifest
