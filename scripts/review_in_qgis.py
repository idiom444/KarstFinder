#!/usr/bin/env python3
"""Load the saved result through the live QGIS MCP plugin, preserving old state."""
import json
from pathlib import Path
from datetime import datetime
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from karstfinder.qgis_bridge import request

info=request('get_project_info')
target=ROOT/'qgis/KarstFinder.qgz'
if info['filename']!=str(target) and (info['layer_count'] or info['filename']):
    backup=ROOT/'qgis'/f"session_before_karstfinder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.qgz"
    request('save_project',{'path':str(backup)})
    print('Preserved previous QGIS session at',backup)
loaded=request('load_project',{'path':str(target)})
assert not loaded.get('unavailable_layers'),loaded
request('set_canvas_extent',{'xmin':616900,'ymin':5253400,'xmax':623100,'ymax':5258600,'crs':'EPSG:26910'})
check=request('execute_code',{'code':"print([(l.name(), l.isValid()) for l in QgsProject.instance().mapLayers().values()]); print('Invalid:', sum(not l.isValid() for l in QgsProject.instance().mapLayers().values()))"})
report={'loaded':loaded,'project':request('get_project_info'),'layer_validation':check}
(ROOT/'docs/qgis_live_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
