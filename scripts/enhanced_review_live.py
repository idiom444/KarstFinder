#!/usr/bin/env python3
"""Inspect saved maps in desktop QGIS, preserve dirty sessions via Library.open."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,write_json
from karstfinder.library import Library
from karstfinder.qgis_bridge import request

lib=Library(ROOT);report={}
for aid,area in config()['areas'].items():
    entry=lib.entry(area['enhanced_library_id']);lib.open(area['enhanced_library_id'])
    png=ROOT/f'docs/enhanced_v001/{aid}_live_canvas.png'
    code=f"""
import json
from pathlib import Path
from qgis.core import QgsProject,QgsApplication
p=QgsProject.instance();dirty=p.isDirty()
assert p.crs().authid()=='EPSG:26910'
assert all(l.isValid() for l in p.mapLayers().values())
main=[l for l in p.mapLayers().values() if l.customProperty('karstfinder/enhanced_filter_target',False) and l.geometryType()==0][0]
assert main.featureCount()=={entry['candidate_count']} and main.subsetString()==''
assert p.layerTreeRoot().findLayer(main.id()).isVisible()
assert main.setSubsetString('evidence_strength >= 0.5')
filtered=main.featureCount();assert filtered<= {entry['candidate_count']}
assert main.setSubsetString('');assert main.featureCount()=={entry['candidate_count']}
p.setDirty(dirty)
canvas=iface.mapCanvas();canvas.refresh();QgsApplication.processEvents();canvas.waitWhileRendering();canvas.saveAsImage({str(png)!r})
print(json.dumps({{'crs':p.crs().authid(),'layers':len(p.mapLayers()),'leads':main.featureCount(),'all_retained_default_visible':True,'filter_roundtrip_count':filtered,'default_subset':main.subsetString(),'dirty_state_preserved':p.isDirty()==dirty,'canvas_png':{str(png.relative_to(ROOT))!r}}}))
"""
    result=request('execute_code',{'code':code},timeout=120)
    if not result.get('executed'):raise RuntimeError(result)
    report[aid]=json.loads(result['stdout'].strip().splitlines()[-1]);print(aid,report[aid]['leads'],'live map verified',flush=True)
write_json(ROOT/'docs/enhanced_v001/live_qgis_review.json',report)
