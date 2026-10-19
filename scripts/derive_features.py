#!/usr/bin/env python3
"""Established GIS derivatives for the complementary feature analysis."""
import argparse,json,sys
from pathlib import Path
from osgeo import gdal
from whitebox.whitebox_tools import WhiteboxTools
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,raster,sha,CO
import numpy as np

gdal.UseExceptions()
ap=argparse.ArgumentParser();ap.add_argument('--config',default='configs/blind_v002.json');args=ap.parse_args();cfgpath=ROOT/args.config
cfg=json.loads(cfgpath.read_text());out=ROOT/cfg.get('feature_processed_dir','data/processed/features_v002');out.mkdir(parents=True,exist_ok=True)
if (out/'derivatives_manifest.json').exists():raise SystemExit(f'Refusing completed derivative overwrite: {out}')
processed=ROOT/cfg.get('processed_dir','data/processed')
source=processed/'dem_1m_buffered.tif';qa=json.loads((out/'qa.json').read_text())
assert qa['source_hash']==sha(source),'Native source changed; repeat QA with a new version'
assert qa['native_buffered_missing_pixels']==0,'Do not fill a DEM with unreviewed internal NoData holes'
w=WhiteboxTools();w.set_verbose_mode(False);w.set_max_procs(4);log=[]
products={}
for mode in ['slope','hillshade']:
 p=out/f'{mode}_1m_buffered.tif'
 if not p.exists():gdal.DEMProcessing(str(p),str(source),mode,creationOptions=CO,**({'scale':1.0} if mode=='slope' else {}))
 products[p.name]=sha(p);print(mode,'complete',flush=True)
p=out/'depression_depth_1m_buffered.tif'
if not p.exists():
 filled_native=out/'filled_for_depth_1m.tif'
 status=w.fill_depressions_wang_and_liu(str(source),str(filled_native),fix_flats=False,callback=log.append)
 assert status==0 and filled_native.exists(),log[-10:]
 depth=np.maximum(array(filled_native)-array(source),0)
 raster(p,depth,source)
 del depth
products[p.name]=sha(p);print('Closed-depression depth complete',flush=True)
# Continuous flow is used for contextual drainage only, never for cave confirmation.
dem10=processed/'dem_10m_buffered.tif';filled=out/'filled_for_drainage_10m.tif'
if not filled.exists():
 assert w.fill_depressions_wang_and_liu(str(dem10),str(filled),fix_flats=True,callback=log.append)==0
p=out/'contributing_area_10m_buffered.tif'
if not p.exists():
 assert w.d8_flow_accumulation(str(filled),str(p),out_type='catchment area',callback=log.append)==0
products[p.name]=sha(p)
# Native local elevation residual is contextual evidence for hollows/trenches.
p=out/'residual_11m_buffered.tif'
if not p.exists():
 assert w.diff_from_mean_elev(str(source),str(p),filterx=11,filtery=11,callback=log.append)==0
products[p.name]=sha(p)
(out/'derivation.log').write_text('\n'.join(log))
report={'source_sha256':sha(source),'config_sha256':sha(cfgpath),'whitebox_version':w.version().strip(),
        'whitebox_binary_sha256':sha(Path(w.exe_path)/w.exe_name),'products':products}
(out/'derivatives_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
