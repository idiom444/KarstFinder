"""Shared local configuration and immutable-source helpers."""
import json
from karstfinder.enhanced.common import ROOT,safe_path,sha,write_json,fingerprint,fresh_directory


def config(area=None):
    value=json.loads((ROOT/'configs/carbonate_v001.json').read_text())
    return (value,value['areas'][area]) if area else value
