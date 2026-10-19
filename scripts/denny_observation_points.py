#!/usr/bin/env python3
"""GDAL bare-earth viewsheds from samples on the official Denny Creek trail."""
import csv
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from osgeo import gdal, ogr, osr

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import memory, sha
gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()
cfg=json.loads((ROOT/'configs/denny_v001_features.json').read_text())
out=ROOT/'results/denny_v001_observation'
if out.exists():raise SystemExit(f'Refusing overwrite: {out}')
out.mkdir(parents=True)
source=ROOT/cfg['processed_dir']/'dem_10m_buffered.tif';ref=gdal.Open(str(source));gt=ref.GetGeoTransform()
shape=(ref.RasterYSize,ref.RasterXSize)
context=ogr.Open(str(ROOT/cfg['processed_dir']/'context.gpkg'));bedrock=context.GetLayerByName('bedrock')
bedrock.SetAttributeFilter("MAP_UNIT_100K='PMmb(e)' AND OBJECTID=29438")
mask=memory(np.zeros(shape,dtype='uint8'),ref);gdal.RasterizeLayer(mask,[1],bedrock,burn_values=[1])
marble_mask=mask.ReadAsArray()==1
parts=[]
for f in bedrock:
    parts.append(f.GetGeometryRef().Clone())
access=ogr.Open(str(ROOT/'results/denny_v001_access/access.gpkg'));trails=access.GetLayerByName('trails')
trails.SetAttributeFilter("trail_name='DENNY CREEK'")
a,b,c,d=cfg['study_bounds'];samples=[]
for f in trails:
    multi=f.GetGeometryRef()
    lines=[multi] if ogr.GT_Flatten(multi.GetGeometryType())==ogr.wkbLineString else list(multi)
    for line in lines:
        for along in np.arange(0,line.Length(),100):
            p=line.Value(float(along));x,y=p.GetX(),p.GetY()
            if not (a<=x<c and b<=y<d):continue
            gap=min(g.Distance(p) for g in parts)
            if gap>1000 or any(p.Distance(prev[1])<50 for prev in samples):continue
            ds=gdal.ViewshedGenerate(ref.GetRasterBand(1),'MEM','',[],x,y,1.7,0,255,0,0,0,
                                    .85714,gdal.GVM_Edge,1500)
            aligned=gdal.Warp('',ds,format='MEM',outputBounds=[gt[0],gt[3]+gt[5]*shape[0],gt[0]+gt[1]*shape[1],gt[3]],
                              width=shape[1],height=shape[0],dstNodata=0,resampleAlg='near')
            visible=aligned.ReadAsArray()==255
            count=int((visible&marble_mask).sum())
            row=dict(easting=x,northing=y,marble_distance_m=gap,visible_marble_cells_10m=count,
                     modeled_visible_marble_fraction=count/int(marble_mask.sum()))
            samples.append((row,p.Clone()))
samples.sort(key=lambda item:(-item[0]['visible_marble_cells_10m'],item[0]['marble_distance_m']))
selected=[]
for row,p in samples:
    if row['visible_marble_cells_10m']==0:continue
    if any(p.Distance(q)<200 for _,q in selected):continue
    selected.append((row,p))
    if len(selected)==3:break
ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'observation.gpkg'))
layer=ds.CreateLayer('trail_observation_points',ref.GetSpatialRef(),ogr.wkbPoint)
for name,typ in [('station_id',ogr.OFTString),('easting',ogr.OFTReal),('northing',ogr.OFTReal),('longitude',ogr.OFTReal),('latitude',ogr.OFTReal),
                 ('marble_distance_m',ogr.OFTReal),('visible_marble_cells_10m',ogr.OFTInteger),('modeled_visible_marble_fraction',ogr.OFTReal),
                 ('meaning',ogr.OFTString)]:layer.CreateField(ogr.FieldDefn(name,typ))
wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
tx=osr.CoordinateTransformation(ref.GetSpatialRef(),wgs);rows=[]
gpx=ET.Element('gpx',version='1.1',creator='KarstFinder',xmlns='http://www.topografix.com/GPX/1/1')
for i,(row,p) in enumerate(selected,1):
    row['station_id']=f'OBS-{i:02d}';row['longitude'],row['latitude'],_=tx.TransformPoint(p.GetX(),p.GetY())
    row['meaning']='Point ON mapped Denny Creek trail; possible geological observation only. Bare-earth view excludes canopy, snow and weather. Not an entrance, verified viewpoint or off-trail route.'
    f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(p)
    for key,value in row.items():f[key]=value
    layer.CreateFeature(f);rows.append(row)
    w=ET.SubElement(gpx,'wpt',lat=str(row['latitude']),lon=str(row['longitude']))
    ET.SubElement(w,'name').text=row['station_id']+' trail observation'
    ET.SubElement(w,'desc').text=row['meaning']
    # Preserve the chosen viewshed in standard raster form, without vegetation claims.
    gdal.ViewshedGenerate(ref.GetRasterBand(1),'GTiff',str(out/f'{row["station_id"]}_bare_earth_viewshed.tif'),
                         ['COMPRESS=DEFLATE','TILED=YES'],p.GetX(),p.GetY(),1.7,0,255,0,0,0,.85714,gdal.GVM_Edge,1500)
ds=None
ET.indent(gpx);ET.ElementTree(gpx).write(out/'trail_observation_waypoints.gpx',encoding='utf-8',xml_declaration=True)
if rows:
    with (out/'trail_observation_points.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
report=dict(method='GDAL ViewshedGenerate, 10 m bare-earth DEM, 1.7 m observer, ground target, 1500 m range',
            target_marble_objectid=29438,target_marble_cells_10m=int(marble_mask.sum()),
            trail_sample_interval_m=100,minimum_station_separation_m=200,samples_evaluated=len(samples),
            stations=rows,ground_only=True,canopy_visibility_or_entrance_detection_claimed=False,
            note='A terrain viewshed is not proof that rock or entrances are visible through trees, nor that access is currently open.')
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'manifest.json').write_text(json.dumps({'source_dem':str(source.relative_to(ROOT)),'source_sha256':sha(source),
      'outputs':{p.name:sha(p) for p in out.iterdir() if p.is_file()}},indent=2)+'\n')
(ROOT/'docs/experiments/denny_v001_observation_summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'trail_samples_evaluated':len(samples),'on_trail_observation_stations':len(rows)},indent=2))
