"""Shared configuration, provenance and persistent-GIS helpers."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]


def config(area=None):
    value = json.loads((ROOT/'configs/enhanced_v001.json').read_text())
    return (value, value['areas'][area]) if area else value


def safe_path(name):
    path = (ROOT/name).resolve()
    if not path.is_relative_to(ROOT) or 'private' in path.parts:
        raise ValueError('Enhanced inputs/outputs must be public prospecting data inside this repository')
    return path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def fresh_directory(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite experiment artifacts: {path}')
    path.mkdir(parents=True)
    return path


def fingerprint(paths):
    return {str(Path(p).relative_to(ROOT)):sha(p) for p in sorted(paths) if Path(p).is_file()}
