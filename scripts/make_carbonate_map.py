#!/usr/bin/env python3
import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.carbonate.common import config
from karstfinder.carbonate.map_project import build
p=argparse.ArgumentParser();p.add_argument('area',choices=list(config()['areas'])+['all']);a=p.parse_args()
for area in config()['areas'] if a.area=='all' else [a.area]:print(json.dumps(build(area),indent=2))
