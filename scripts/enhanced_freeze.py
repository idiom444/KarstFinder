#!/usr/bin/env python3
"""Freeze enhanced prospecting only after successful independent review."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,sha,write_json,fingerprint

p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
path=ROOT/'experiments/snapshots/enhanced_v001.json'
if a.verify:
 j=json.loads(path.read_text())
 for name,digest in j['sha256'].items():assert sha(safe_path(name))==digest,name
 print('Enhanced snapshot verified:',len(j['sha256']),'hashes');raise SystemExit()
if path.exists():raise FileExistsError('Snapshot already frozen; create a new named experiment')
review=json.loads((ROOT/'docs/enhanced_v001/verification.json').read_text());assert len(review['areas'])==4 and all('library' in v for v in review['areas'].values())
files=[ROOT/'configs/enhanced_v001.json']+list((ROOT/'src/karstfinder/enhanced').glob('*.py'))+list((ROOT/'scripts').glob('enhanced_*.py'))+[ROOT/'tests/test_enhanced.py']
files+=list((ROOT/'docs/enhanced_v001').glob('*'))
for aid,area in config()['areas'].items():
 for directory in [safe_path(area['result_dir']),safe_path(area['processed_dir'])]:
  files.extend(p for p in directory.rglob('*') if p.is_file() and '_development_' not in str(p))
 files.extend(p for p in safe_path(area['raw_dir']).rglob('*') if p.is_file())
 folder=ROOT/'prospecting_library'/area['enhanced_library_id'];files+=list(folder.glob('map-v*.qgz'));files+=list((folder/'versions').glob('*'))
 files.append(ROOT/f'qgis/KarstFinder_{aid}_enhanced_v001.qgz')
files=sorted(set(f for f in files if f.is_file()))
# Leave the stable library aliases editable; experimental numerical outputs freeze.
for aid,area in config()['areas'].items():
 folder=safe_path(area['result_dir'])
 for f in folder.iterdir():
  if f.is_file():f.chmod(0o444)
 folder.chmod(0o555)
write_json(path,{'experiment_id':'enhanced_v001','status':'unvalidated prospecting snapshot; NOT a blind validation freeze','known_cave_inputs_used':False,'independently_blind':False,'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),'baseline_commit':'8b0b1877df014ecf5969f1529bcde6fc5fcd29f8','sha256':fingerprint(files)})
print('Frozen enhanced snapshot:',len(files),'files')
