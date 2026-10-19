#!/usr/bin/env python3
"""Persist DEMs and clipped geology using GDAL/OGR, never rendered hillshade."""
import json
from pathlib import Path
import numpy as np
from osgeo import gdal, ogr, osr

gdal.UseExceptions(); ogr.UseExceptions(); osr.UseExceptions()
ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT/'data/raw', ROOT/'data/processed'
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((ROOT/'configs/blind_v001.json').read_text())
a,b,c,d = cfg['study_bounds']; pad = cfg['buffer_m']
bounds = [a-pad,b-pad,c+pad,d+pad]
co = ['COMPRESS=DEFLATE','TILED=YES','BIGTIFF=IF_SAFER']
# Older acquisition first; newest valid pixel takes precedence in VRT.
tiles = [str(p) for project in [cfg['fallback_elevation_project'],cfg['elevation_project']]
         for p in sorted(RAW.glob(f'USGS_1M_*_{project}.tif'))]
assert tiles, 'Run acquisition first'
vrt = gdal.BuildVRT(str(OUT/'elevation_source.vrt'),tiles)
raw_info = []
for p in tiles:
 ds = gdal.Open(p);band=ds.GetRasterBand(1)
 raw_info.append({'file':Path(p).name,'crs':ds.GetSpatialRef().GetAuthorityCode(None),'geotransform':ds.GetGeoTransform(),
                  'unit':band.GetUnitType(),'nodata':band.GetNoDataValue(),'size':[ds.RasterXSize,ds.RasterYSize]})
 assert ds.GetSpatialRef().GetAuthorityCode(None) == '26910', 'Unexpected native CRS: evaluate units/realization'
 # Standard USGS tile metadata explicitly declares NAVD88 metres;
 # delivered GeoTIFF bands leave UnitType empty. Supplier-native reports use feet.
 catalog=json.loads((RAW/'usgs_1m_catalog.json').read_text())
 item=next(i for i in catalog['items'] if Path(i['downloadURL']).name==Path(p).name)
 assert 'All bare earth elevation values are in meters' in item['body']
 assert band.GetUnitType() in ('','m','metre','meter'), 'Conflicting elevation units'
 raw_info[-1]['elevation_units_evidence']='USGS standard 1m catalog body: NAVD88 metres; band UnitType is empty'
for res,name in [(1,'dem_1m_buffered'),(cfg['terrain_resolution_m'],'dem_10m_buffered')]:
 path = OUT/f'{name}.tif'
 ds = gdal.Warp(str(path),vrt,dstSRS=cfg['crs'],outputBounds=bounds,xRes=res,yRes=res,
                resampleAlg='average' if res>1 else 'near',dstNodata=-9999,outputType=gdal.GDT_Float32,creationOptions=co)
 ds.GetRasterBand(1).SetUnitType('m');ds=None
 print(name,flush=True)
vrt=None
# Source features are returned in NAD83/UTM10 by the agency service.
gpkg = OUT/'context.gpkg'
if gpkg.exists(): gpkg.unlink()
for i,name in [(11,'bedrock'),(7,'faults'),(9,'contacts'),(1,'orientations')]:
 source=RAW/f'dnr_{i}.geojson'
 # Explicit source CRS because a GeoJSON service may omit a deprecated CRS member.
 src=ogr.Open(str(source));layer=src.GetLayer(0)
 assert layer.GetSpatialRef().GetAuthorityCode(None)=='26910', 'Service returned unexpected vector CRS'
 ds=gdal.VectorTranslate(str(gpkg),src,format='GPKG',accessMode='update' if gpkg.exists() else None,
                         layerName=name,geometryType='PROMOTE_TO_MULTI',srcSRS=cfg['crs'],dstSRS=cfg['crs'],clipDst=bounds)
 ds=None;src=None
vec=ogr.Open(str(gpkg),1);layer=vec.GetLayerByName('bedrock')
layer.CreateField(ogr.FieldDefn('geo_score',ogr.OFTReal))
layer.CreateField(ogr.FieldDefn('evidence',ogr.OFTString))
for f in layer:
 unit=f['MAP_UNIT_100K'];f['geo_score']=cfg['geology_scores'].get(unit,0)
 f['evidence']=('mapped marble; 1:100k contact uncertainty' if unit=='PMmb(e)' else
                'mixed melange may contain unmapped marble' if unit=='JTRmt(e)' else 'no mapped carbonate evidence; not proof of absence')
 layer.SetFeature(f)
srs=osr.SpatialReference();srs.ImportFromEPSG(26910)
study=vec.CreateLayer('study_area',srs,ogr.wkbPolygon)
study.CreateField(ogr.FieldDefn('name',ogr.OFTString));f=ogr.Feature(study.GetLayerDefn());f['name']='Geographic study envelope; no cave locations used'
f.SetGeometry(ogr.CreateGeometryFromWkt(f'POLYGON (({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'));study.CreateFeature(f)
vec=None
# Retain acquisition identity and quantify overlap mismatch; no feathering.
epoch_arrays={}
for project,epoch in [(cfg['fallback_elevation_project'],2019),(cfg['elevation_project'],2021)]:
    v=gdal.BuildVRT('',[p for p in tiles if project in p])
    ds=gdal.Warp('',v,format='MEM',dstSRS=cfg['crs'],outputBounds=bounds,xRes=10,yRes=10,resampleAlg='average',dstNodata=-9999)
    arr=ds.ReadAsArray().astype(float);arr[arr==-9999]=np.nan;epoch_arrays[epoch]=arr
ref=gdal.Open(str(OUT/'dem_10m_buffered.tif'))
epoch=np.where(np.isfinite(epoch_arrays[2021]),2021,np.where(np.isfinite(epoch_arrays[2019]),2019,0)).astype('uint16')
ds=gdal.GetDriverByName('GTiff').Create(str(OUT/'source_epoch_10m.tif'),ref.RasterXSize,ref.RasterYSize,1,gdal.GDT_UInt16,co)
ds.SetGeoTransform(ref.GetGeoTransform());ds.SetProjection(ref.GetProjection());ds.GetRasterBand(1).SetNoDataValue(0);ds.GetRasterBand(1).WriteArray(epoch);ds=None
both=np.isfinite(epoch_arrays[2019])&np.isfinite(epoch_arrays[2021])
difference=epoch_arrays[2021][both]-epoch_arrays[2019][both]
overlap={'overlap_cells_10m':int(both.sum()),'difference_definition':'2021 minus 2019 average-grid elevation',
         'median_difference_m':float(np.median(difference)) if difference.size else None,
         'p95_absolute_difference_m':float(np.percentile(np.abs(difference),95)) if difference.size else None}
# Coverage by study and processing buffer; missing coverage is not infilled.
ds=gdal.Open(str(OUT/'dem_10m_buffered.tif'));z=ds.ReadAsArray();valid=np.isfinite(z)&(z!=ds.GetRasterBand(1).GetNoDataValue())
n=pad//cfg['terrain_resolution_m'];core=valid[n:-n,n:-n]
report={'source_rasters':raw_info,'buffered_valid_fraction':float(valid.mean()),'study_valid_fraction':float(core.mean()),
        'buffered_elevation_min_m':float(z[valid].min()),'buffered_elevation_max_m':float(z[valid].max()),
        'study_area_km2':(c-a)*(d-b)/1e6,'buffer_m':pad,'epoch_overlap':overlap,'epoch_pixel_counts':{str(k):int((epoch==k).sum()) for k in [0,2019,2021]}}
(ROOT/'docs/data_quality.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
