#!/usr/bin/env python3
"""Blind landscape baseline: GDAL derivatives, Whitebox DEV, explicit scoring."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
from scipy.ndimage import minimum_filter
from osgeo import gdal, ogr, osr
from whitebox.whitebox_tools import WhiteboxTools

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from karstfinder.model import score_landscape

gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()
CO=['COMPRESS=DEFLATE','TILED=YES']
NODATA=-9999


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def write_raster(path,values,template):
    ds=gdal.GetDriverByName('GTiff').Create(str(path),template.RasterXSize,template.RasterYSize,1,gdal.GDT_Float32,CO)
    ds.SetGeoTransform(template.GetGeoTransform());ds.SetProjection(template.GetProjection())
    ds.GetRasterBand(1).SetNoDataValue(NODATA)
    ds.GetRasterBand(1).WriteArray(np.where(np.isfinite(values),values,NODATA).astype('float32'))
    ds=None


def read(path):
    ds=gdal.Open(str(path));a=ds.ReadAsArray().astype(float);nd=ds.GetRasterBand(1).GetNoDataValue()
    if nd is not None:a[a==nd]=np.nan
    return a


def candidate_areas(out,core,combined,terrain,geology,votes,exposure,slope,cfg):
    binary=np.isfinite(combined)&(combined>=cfg['candidate_min_score'])
    temp=gdal.GetDriverByName('MEM').Create('',core.RasterXSize,core.RasterYSize,1,gdal.GDT_Byte)
    temp.SetGeoTransform(core.GetGeoTransform());temp.SetProjection(core.GetProjection());temp.GetRasterBand(1).WriteArray(binary.astype('uint8'))
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'candidates.gpkg'))
    layer=ds.CreateLayer('candidate_areas',core.GetSpatialRef(),ogr.wkbPolygon)
    specs=[('presence',ogr.OFTInteger),('candidate_id',ogr.OFTString),('rank',ogr.OFTInteger),('area_m2',ogr.OFTReal),
           ('mean_score',ogr.OFTReal),('max_score',ogr.OFTReal),('terrain_mean',ogr.OFTReal),('geo_mean',ogr.OFTReal),
           ('votes_mean',ogr.OFTReal),('exposure_mean',ogr.OFTReal),('slope_mean_deg',ogr.OFTReal),
           ('easting',ogr.OFTReal),('northing',ogr.OFTReal),('longitude',ogr.OFTReal),('latitude',ogr.OFTReal),
           ('geo_evidence',ogr.OFTString),('terrain_evidence',ogr.OFTString),('alternatives',ogr.OFTString),('uncertainty',ogr.OFTString),('status',ogr.OFTString)]
    for n,t in specs:layer.CreateField(ogr.FieldDefn(n,t))
    assert cfg['candidate_connectivity']==4
    gdal.Polygonize(temp.GetRasterBand(1),temp.GetRasterBand(1),layer,0,[])
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    tx=osr.CoordinateTransformation(core.GetSpatialRef(),wgs)
    items=[];deletes=[]
    for feature in layer:
        geom=feature.GetGeometryRef();area=geom.GetArea()
        if area<cfg['candidate_min_area_m2']:
            deletes.append(feature.GetFID());continue
        maskvec=ogr.GetDriverByName('Memory').CreateDataSource('');ml=maskvec.CreateLayer('shape',core.GetSpatialRef(),ogr.wkbPolygon)
        mf=ogr.Feature(ml.GetLayerDefn());mf.SetGeometry(geom);ml.CreateFeature(mf)
        mask=gdal.GetDriverByName('MEM').Create('',core.RasterXSize,core.RasterYSize,1,gdal.GDT_Byte)
        mask.SetGeoTransform(core.GetGeoTransform());mask.SetProjection(core.GetProjection());gdal.RasterizeLayer(mask,[1],ml,burn_values=[1])
        pixels=mask.ReadAsArray().astype(bool)
        point=geom.PointOnSurface();x,y=point.GetX(),point.GetY();lon,lat,_=tx.TransformPoint(x,y)
        row={'area_m2':area,'mean_score':float(combined[pixels].mean()),'max_score':float(combined[pixels].max()),
             'terrain_mean':float(terrain[pixels].mean()),'geo_mean':float(geology[pixels].mean()),'votes_mean':float(votes[pixels].mean()),
             'exposure_mean':float(exposure[pixels].mean()),'slope_mean_deg':float(slope[pixels].mean()),
             'easting':x,'northing':y,'longitude':lon,'latitude':lat,
             'geo_evidence':'Mapped marble PMmb(e), DNR 1:100,000',
             'terrain_evidence':'Multiscale mid-slope votes and slope exposure ramp',
             'alternatives':'Glacial bedrock morphology; talus; landslide scar; non-karst outcrop',
             'uncertainty':'Coarse geological contacts; multi-epoch DEM; no entrance detector or field verification',
             'status':'preliminary landscape area; NOT a cave or entrance prediction'}
        items.append((feature.GetFID(),row))
    for fid in deletes:layer.DeleteFeature(fid)
    items.sort(key=lambda x:(-x[1]['mean_score'],-x[1]['area_m2'],x[1]['easting'],x[1]['northing']))
    for rank,(fid,row) in enumerate(items,1):
        row.update(candidate_id=f'KF-{rank:03d}',rank=rank)
        feature=layer.GetFeature(fid)
        for k,v in row.items():feature[k]=v
        layer.SetFeature(feature)
    ds=None
    fields=[n for n,t in specs if n!='presence']
    with (out/'candidates.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(r for _,r in items)
    return [r for _,r in items],int(binary.sum())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default='configs/blind_v001.json');ap.add_argument('--output',default='results/blind_v001');args=ap.parse_args()
    cfg_path=ROOT/args.config;cfg=json.loads(cfg_path.read_text());out=ROOT/args.output
    if out.exists():raise SystemExit(f'Refusing to overwrite {out}; choose a new experiment output directory')
    out.mkdir(parents=True)
    (out/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    source_manifest=json.loads((ROOT/'docs/acquisition_manifest.json').read_text())
    for rec in source_manifest:
        if sha(ROOT/rec['path'])!=rec['sha256']:raise RuntimeError(f'Input changed: {rec["path"]}')
    source=ROOT/'data/processed/dem_10m_buffered.tif';template=gdal.Open(str(source));valid=np.isfinite(read(source))
    log=[]
    for mode in ['slope','aspect','hillshade']:
        ds=gdal.DEMProcessing(str(out/f'{mode}_buffered.tif'),str(source),mode,creationOptions=CO,**({'scale':1.0} if mode=='slope' else {}));ds=None
    w=WhiteboxTools();w.set_verbose_mode(False);w.set_max_procs(4)
    wbt_version=w.version();deviations=[]
    for n in cfg['tpi_windows_cells']:
        assert n%2==1 and n>1
        path=out/f'dev_{n*cfg["terrain_resolution_m"]}m_buffered.tif'
        result=w.dev_from_mean_elev(str(source),str(path),filterx=n,filtery=n,callback=log.append)
        if result!=0 or not path.exists():raise RuntimeError(f'Whitebox DEV failed: {n}: {log[-10:]}')
        deviations.append(read(path));print(f'DEV window {n} cells complete',flush=True)
    (out/'whitebox.log').write_text('\n'.join(log))
    # A complete window is mandatory: do not silently score missing neighbourhoods.
    max_window=max(cfg['tpi_windows_cells'])
    full_support=minimum_filter(valid.astype('uint8'),size=max_window,mode='constant',cval=0).astype(bool)
    geo=gdal.GetDriverByName('MEM').Create('',template.RasterXSize,template.RasterYSize,1,gdal.GDT_Float32)
    geo.SetGeoTransform(template.GetGeoTransform());geo.SetProjection(template.GetProjection())
    vec=ogr.Open(str(ROOT/'data/processed/context.gpkg'));layer=vec.GetLayerByName('bedrock')
    # Unit polygons should not overlap by compilation; order lower evidence before mapped marble.
    sorted_ds=ogr.GetDriverByName('Memory').CreateDataSource('')
    sorted_layer=sorted_ds.CreateLayer('geology',layer.GetSpatialRef(),ogr.wkbMultiPolygon);sorted_layer.CreateField(ogr.FieldDefn('geo_score',ogr.OFTReal))
    for f in sorted(list(layer),key=lambda f:f['geo_score']):
        nf=ogr.Feature(sorted_layer.GetLayerDefn());nf.SetGeometry(f.GetGeometryRef());nf['geo_score']=f['geo_score'];sorted_layer.CreateFeature(nf)
    gdal.RasterizeLayer(geo,[1],sorted_layer,options=['ATTRIBUTE=geo_score']);geology=geo.ReadAsArray().astype(float)
    slope=read(out/'slope_buffered.tif')
    scores=score_landscape(deviations,slope,geology,full_support,cfg)
    scores['geological_score']=np.where(valid,geology,np.nan)
    scores['analysis_valid']=full_support.astype(float)
    n=cfg['buffer_m']//cfg['terrain_resolution_m'];sl=np.s_[n:-n,n:-n]
    core=gdal.Translate('',template,format='MEM',projWin=[cfg['study_bounds'][0],cfg['study_bounds'][3],cfg['study_bounds'][2],cfg['study_bounds'][1]])
    for name,array in scores.items():write_raster(out/f'{name}.tif',array[sl],core)
    for mode in ['slope','aspect','hillshade']:
        gdal.Translate(str(out/f'{mode}.tif'),str(out/f'{mode}_buffered.tif'),projWin=[cfg['study_bounds'][0],cfg['study_bounds'][3],cfg['study_bounds'][2],cfg['study_bounds'][1]],creationOptions=CO)
    for scale,arr in zip(cfg['tpi_windows_cells'],deviations):write_raster(out/f'dev_{scale*cfg["terrain_resolution_m"]}m.tif',arr[sl],core)
    rows,selected_cells=candidate_areas(out,core,scores['combined_score'][sl],scores['terrain_score'][sl],geology[sl],scores['mid_slope_votes'][sl],scores['exposure'][sl],slope[sl],cfg)
    area_per_cell=cfg['terrain_resolution_m']**2;area_total=core.RasterXSize*core.RasterYSize*area_per_cell
    summary={'experiment_id':cfg['experiment_id'],'status':'exploratory_blind_unfrozen','known_cave_sources_accessed':False,
        'study_area_km2':area_total/1e6,'eligible_area_km2':float(full_support[sl].sum()*area_per_cell/1e6),
        'mapped_marble_area_km2':float((geology[sl]==1).sum()*area_per_cell/1e6),
        'mixed_carbonate_possible_area_km2':float(((geology[sl]>0)&(geology[sl]<1)).sum()*area_per_cell/1e6),
        'threshold_selected_area_km2_before_size_filter':selected_cells*area_per_cell/1e6,
        'candidate_area_count':len(rows),'candidate_area_km2':sum(r['area_m2'] for r in rows)/1e6,
        'candidate_area_fraction_of_study':sum(r['area_m2'] for r in rows)/area_total,
        'cave_detection_or_validation_performed':False,'interpretation':'Landscape hypotheses only. No cave existence probabilities.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'inputs.json').write_text(json.dumps(source_manifest,indent=2)+'\n')
    code_files=sorted((ROOT/'src').rglob('*.py'))+sorted((ROOT/'scripts').glob('*.py'))+[cfg_path]
    outputs={str(p.relative_to(out)):sha(p) for p in sorted(out.glob('*')) if p.is_file()}
    inputs={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'data/processed').glob('*')) if p.is_file()}
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True).stdout.strip() or None
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'git_commit_at_run':commit,
        'git_dirty_at_run':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),
        'source_code_hashes':{str(p.relative_to(ROOT)):sha(p) for p in code_files},'prepared_input_hashes':inputs,
        'python':platform.python_version(),'gdal':gdal.VersionInfo('--version'),'whitebox':wbt_version.strip(),
        'whitebox_binary_sha256':sha(Path(w.exe_path)/w.exe_name),'output_hashes':outputs,'frozen':False}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
