#!/usr/bin/env python3
"""Inspectable GDAL/Whitebox measurements; no custom hydrology or TPI."""
import argparse
from pathlib import Path
import sys
import numpy as np
from osgeo import gdal
from whitebox.whitebox_tools import WhiteboxTools

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,fresh_directory,write_json,sha,fingerprint
from karstfinder.gis import array,raster,CO


def main():
    parser=argparse.ArgumentParser();parser.add_argument('area',choices=config()['areas']);args=parser.parse_args()
    cfg,area=config(args.area);out=fresh_directory(safe_path(area['processed_dir'])/'terrain')
    pre=safe_path(area['baseline_feature_prepared']);processed=safe_path(area['baseline_processed'])
    dem=processed/'dem_10m_buffered.tif';native=processed/'dem_1m_buffered.tif'
    w=WhiteboxTools();w.set_verbose_mode(False);w.set_max_procs(4);logs=[]
    a,b,c,d=area['study_bounds'];window=[a,d,c,b];products=[]

    def tool(name,output,**kwargs):
        result=getattr(w,name)(output=str(output),callback=logs.append,**{k:str(v) if isinstance(v,Path) else v for k,v in kwargs.items()})
        if result or not output.exists():raise RuntimeError(f'{name} failed: {logs[-8:]}')
        products.append(output);print(args.area,output.name,flush=True)

    def crop(name,source):
        target=out/(name+'.tif');gdal.Translate(str(target),str(source),projWin=window,creationOptions=CO)
        products.append(target);return target

    for method in ['slope','hillshade']:
        path=out/(method+'_10m_buffered.tif');gdal.DEMProcessing(str(path),str(dem),method,creationOptions=CO)
        products.append(path);crop(method+'_10m',path)
    for size in cfg['terrain']['local_windows_m']:
        n=size//10
        lo=out/f'local_min_{size}m_buffered.tif';hi=out/f'local_max_{size}m_buffered.tif'
        tool('minimum_filter',lo,i=dem,filterx=n,filtery=n)
        tool('maximum_filter',hi,i=dem,filterx=n,filtery=n)
        z=array(dem);low=array(lo);high=array(hi)
        for name,values in [(f'local_relief_{size}m',high-low),
                            (f'height_above_local_floor_{size}m',z-low),
                            (f'depth_below_local_crest_{size}m',high-z)]:
            path=out/(name+'_buffered.tif');raster(path,values,dem);products.append(path);crop(name,path)
        path=out/f'relative_position_{size}m_buffered.tif'
        tool('relative_topographic_position',path,dem=dem,filterx=n,filtery=n);crop(f'relative_position_{size}m',path)
    for name in ['plan_curvature','profile_curvature','ruggedness_index']:
        path=out/(name+'_buffered.tif');tool(name,path,dem=dem);crop(name,path)
    for size in cfg['terrain']['residual_windows_m']:
        if size==11:source=pre/'residual_11m_buffered.tif'
        else:
            source=out/f'residual_{size}m_buffered.tif';tool('diff_from_mean_elev',source,dem=native,filterx=size,filtery=size)
        crop(f'residual_{size}m',source)
    flow=pre/'contributing_area_10m_buffered.tif';filled=pre/'filled_for_drainage_10m.tif'
    for threshold in cfg['terrain']['stream_sensitivity_areas_m2']:
        path=out/f'modeled_streams_{threshold}m2_buffered.tif'
        tool('extract_streams',path,flow_accum=flow,threshold=threshold,zero_background=True)
        crop(f'modeled_streams_{threshold}m2',path)
    threshold=cfg['terrain']['modeled_stream_area_m2'];streams=out/f'modeled_streams_{threshold}m2_buffered.tif'
    hand=out/'height_above_modeled_drainage_buffered.tif'
    tool('elevation_above_stream',hand,dem=filled,streams=streams);crop('height_above_modeled_drainage',hand)
    contamination=out/'hydrologic_edge_contamination_buffered.tif'
    tool('edge_contamination',contamination,dem=filled,flow_type='d8',zfactor=1);crop('hydrologic_edge_contamination',contamination)
    inverse=out/'inverted_elevation_buffered.tif';raster(inverse,-array(dem),dem);products.append(inverse)
    invfilled=out/'inverted_filled_buffered.tif'
    tool('fill_depressions_wang_and_liu',invfilled,dem=inverse,fix_flats=True)
    invflow=out/'inverted_flow_area_buffered.tif'
    tool('d8_flow_accumulation',invflow,i=invfilled,out_type='catchment area',log=False,clip=False,pntr=False,esri_pntr=False)
    invstreams=out/'modeled_divide_network_buffered.tif'
    tool('extract_streams',invstreams,flow_accum=invflow,threshold=threshold,zero_background=True)
    below=out/'depth_below_modeled_divide_buffered.tif'
    tool('elevation_above_stream',below,dem=invfilled,streams=invstreams);crop('depth_below_modeled_divide',below)
    h=array(hand);v=array(below);den=h+v
    position=np.divide(h,den,out=np.full_like(h,np.nan),where=np.isfinite(den)&(den>0))
    path=out/'normalized_drainage_divide_position_buffered.tif';raster(path,position,dem);products.append(path);crop('normalized_drainage_divide_position',path)
    if cfg['terrain']['lineaments_experimental']:
        for variant in ['vertical','horizontal','45','135']:
            path=out/f'line_filter_{variant}_buffered.tif'
            tool('line_detection_filter',path,i=dem,variant=variant,absvals=True,clip=0)
            crop('line_filter_'+variant,path)
    (out/'whitebox.log').write_text('\n'.join(logs)+'\n')
    report={'area':args.area,'version':cfg['version'],'whitebox':w.version().strip(),
        'whitebox_binary_sha256':sha(Path(w.exe_path)/w.exe_name),
        'inputs':fingerprint([dem,native,flow,filled,pre/'residual_11m_buffered.tif']),
        'products':fingerprint(products),'config_sha256':sha(ROOT/'configs/enhanced_v001.json'),
        'limitations':['Modeled drainage/divides depend on bounded DEM support and exploratory catchment thresholds.',
        'Height above drainage and below divide are terrain proxies, not surveyed valley/ridge elevations.',
        'Line filters are experimental orientation/texture responses, not mapped fractures.',
        'All DEM measurements share a data family; they are not independent confirmations.']}
    write_json(out/'manifest.json',report);write_json(ROOT/f'docs/enhanced_v001/{args.area}_terrain.json',report)


if __name__=='__main__':
    gdal.UseExceptions();main()
