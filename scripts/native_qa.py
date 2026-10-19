#!/usr/bin/env python3
"""Inspect native coverage and epoch seams before 1 m object detection."""
import argparse,gc,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, binary_dilation
from osgeo import gdal
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,raster,sha,CO

gdal.UseExceptions()
ap=argparse.ArgumentParser();ap.add_argument('--config',default='configs/blind_v002.json');args=ap.parse_args();cfgpath=ROOT/args.config
cfg=json.loads(cfgpath.read_text());out=ROOT/cfg.get('feature_processed_dir','data/processed/features_v002');out.mkdir(parents=True,exist_ok=True)
if (out/'qa.json').exists():raise SystemExit(f'Refusing QA overwrite: {out}')
a,b,c,d=cfg['study_bounds'];pad=cfg['buffer_m'];bounds=[a-pad,b-pad,c+pad,d+pad]
source=ROOT/cfg.get('processed_dir','data/processed')/'dem_1m_buffered.tif';ref=gdal.Open(str(source));dem=array(source);valid=np.isfinite(dem)
report={'native_buffered_pixels':int(valid.size),'native_buffered_missing_pixels':int((~valid).sum()),'native_buffered_valid_fraction':float(valid.mean())}
epoch_arrays={}
for project,year in [('WA_EasternCascades_2019_B19',2019),('WA_KingCounty_2021_B21',2021)]:
    files=sorted(str(p) for p in (ROOT/cfg.get('dem_raw_dir','data/raw')).glob(f'USGS_1M_*_{project}.tif'))
    vrt=gdal.BuildVRT('',files);ds=gdal.Warp('',vrt,format='MEM',dstSRS=cfg['crs'],outputBounds=bounds,xRes=1,yRes=1,resampleAlg='near',dstNodata=-9999)
    arr=ds.ReadAsArray();arr[arr==-9999]=np.nan;epoch_arrays[year]=arr;ds=None;vrt=None
    print('Native acquisition aligned:',year,flush=True)
epoch=np.where(np.isfinite(epoch_arrays[2021]),2021,np.where(np.isfinite(epoch_arrays[2019]),2019,0)).astype('uint16')
assert np.array_equal(epoch>0,valid)
raster(out/'source_epoch_1m_buffered.tif',epoch,ref,nodata=0,dtype=gdal.GDT_UInt16)
# Native overlap diagnostics at every tenth row/column, a fixed deterministic sample.
y21=epoch_arrays[2021][::10,::10];y19=epoch_arrays[2019][::10,::10];both=np.isfinite(y21)&np.isfinite(y19)
diff=y21[both]-y19[both]
report['native_overlap_sample']={'sampling_stride_m':10,'n':int(diff.size),'median_difference_m':float(np.median(diff)),
 'p95_absolute_difference_m':float(np.percentile(np.abs(diff),95)),'p99_absolute_difference_m':float(np.percentile(np.abs(diff),99))}
del epoch_arrays,y21,y19,diff;gc.collect()
seam=np.zeros(epoch.shape,bool)
seam[1:]|=(epoch[1:]!=epoch[:-1])&(epoch[1:]>0)&(epoch[:-1]>0)
seam[:,1:]|=(epoch[:,1:]!=epoch[:,:-1])&(epoch[:,1:]>0)&(epoch[:,:-1]>0)
distance=distance_transform_edt(~seam).astype('float32') if seam.any() else np.full(epoch.shape,1e9,dtype='float32')
raster(out/'seam_distance_1m_buffered.tif',distance,ref)
qvalid=valid&(distance>cfg['seam_exclusion_m'])
if not valid.all():qvalid&=distance_transform_edt(valid)>cfg['void_exclusion_m']
raster(out/'feature_quality_1m_buffered.tif',qvalid.astype('uint8'),ref,nodata=255,dtype=gdal.GDT_Byte)
core=np.s_[pad:-pad,pad:-pad];report.update(native_study_missing_pixels=int((~valid[core]).sum()),
 study_feature_eligible_area_km2=float(qvalid[core].sum()/1e6),study_seam_excluded_area_km2=float((valid[core]&~qvalid[core]).sum()/1e6),
 seam_exclusion_m=cfg['seam_exclusion_m'],native_year_counts={str(y):int((epoch[core]==y).sum()) for y in [0,2019,2021]},
 source_hash=sha(source),config_hash=sha(cfgpath))
(out/'qa.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/cfg.get('native_quality_report','docs/native_quality_v002.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
