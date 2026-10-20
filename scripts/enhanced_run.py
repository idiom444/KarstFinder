#!/usr/bin/env python3
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config
from karstfinder.enhanced.registry import run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('area',choices=config()['areas']);run(p.parse_args().area)
