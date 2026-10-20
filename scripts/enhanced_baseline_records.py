#!/usr/bin/env python3
"""Additive complete original measurement record, without changing map datasets."""
import csv,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,sha,write_json
for aid,area in config()['areas'].items():
    source=safe_path(area['baseline_candidate_csv']);destination=safe_path(area['result_dir'])/'baseline_measurement_records.json'
    if destination.exists():raise FileExistsError(destination)
    rows=list(csv.DictReader(source.open()))
    write_json(destination,{'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'interpretation':'Exact original CSV field strings, no numerical conversion or retuning. Enhanced rows link by area-prefixed ID. Private field notes are not read.',
        'records':{aid+':'+r['object_id']:r for r in rows}})
    print(aid,len(rows),'complete original records retained')
