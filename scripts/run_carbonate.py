#!/usr/bin/env python3
"""New carbonate-gated analysis, using only existing local measurements."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.carbonate.common import config
from karstfinder.carbonate.pipeline import run
p=argparse.ArgumentParser();p.add_argument('area',choices=list(config()['areas'])+['all']);a=p.parse_args()
for area in config()['areas'] if a.area=='all' else [a.area]:run(area)
