#!/usr/bin/env python3
"""Filter enhanced display layers in live QGIS; --reset restores every lead."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.filters import subset
from karstfinder.qgis_bridge import request

p=argparse.ArgumentParser();p.add_argument('--reset',action='store_true');p.add_argument('--min-strength',type=float);p.add_argument('--min-geological-confidence',type=float)
for name in ['method','geology','zone','status','availability']:p.add_argument('--'+name)
a=p.parse_args();sql='' if a.reset else subset(a.min_strength,a.method,a.geology,a.zone,a.status,a.availability,a.min_geological_confidence)
code="""
from qgis.core import QgsProject
layers=[l for l in QgsProject.instance().mapLayers().values() if l.customProperty('karstfinder/enhanced_filter_target',False)]
if not layers:raise ValueError('Open an enhanced map first')
for layer in layers:
    if not layer.setSubsetString(SQL):raise ValueError('Provider rejected reversible subset')
iface.mapCanvas().refresh()
print({'subset':SQL,'visible_counts':{l.name():l.featureCount() for l in layers}})
""".replace('SQL',repr(sql))
print(json.dumps(request('execute_code',{'code':code}),indent=2))
