#!/usr/bin/env python3
"""Explicit reviewed geological plate input only; not used in current analyses."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import safe_path
from karstfinder.enhanced.plates import georeference
p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('output');a=p.parse_args()
print(json.dumps(georeference(json.loads(safe_path(a.spec).read_text()),a.output),indent=2))
