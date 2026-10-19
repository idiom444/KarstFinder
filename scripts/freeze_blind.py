#!/usr/bin/env python3
"""Create a write-protected blind freeze, only from a clean committed implementation."""
import json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import sha

if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):raise SystemExit('Commit all work before freezing')
target=ROOT/'experiments/frozen/blind_v002.json'
if target.exists():raise SystemExit('Freeze already exists; never overwrite it')
assert not any((ROOT/'data/private').rglob('*.geojson')),'Unexpected private location records exist before blind freeze'
assert json.loads((ROOT/'docs/experiments/blind_v002_verification.json').read_text())['confirmed_caves']==0
files=set()
for folder in ['data/raw','data/processed','results/blind_v001','results/blind_v002','configs','src','scripts','tests']:
    files.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'))
files.update([ROOT/'qgis/KarstFinder_Blind_v002.qgz',ROOT/'qgis/KarstFinder_Blind_v001.qgz',ROOT/'requirements.lock',ROOT/'pyproject.toml'])
# Rejected tools/development products do not form part of this frozen experiment.
files={p for p in files if 'rejected_v002' not in p.parts}
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
record={'experiment_id':'blind_v002','status':'frozen_before_validation','created_utc':datetime.now(timezone.utc).isoformat(),
        'implementation_git_commit':commit,'known_cave_sources_accessed_before_freeze':False,
        'methods':['v001 landscape suitability','v002 closed-depression cores','v002 cliff/outcrop exposure','descriptive seeded terrain clustering'],
        'validation_protocol':'configs/validation_v001.json','sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}}
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
target.chmod(0o444)
for folder in ['results/blind_v001','results/blind_v002']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file():p.chmod(0o444)
    for p in sorted((ROOT/folder).rglob('*'),reverse=True):
        if p.is_dir():p.chmod(0o555)
    (ROOT/folder).chmod(0o555)
print(json.dumps({'frozen':str(target.relative_to(ROOT)),'implementation_commit':commit,'hashed_files':len(files)},indent=2))
