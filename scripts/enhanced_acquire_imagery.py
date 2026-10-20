#!/usr/bin/env python3
"""Bounded native-resolution RGB/NIR COG crops with explicit optional fallback."""
import argparse
import json
import math
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse
import numpy as np
import requests
from osgeo import gdal,ogr,osr

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,write_json,sha
from karstfinder.gis import raster,CO


def main():
    parser=argparse.ArgumentParser();parser.add_argument('area',choices=config()['areas']);args=parser.parse_args()
    cfg,area=config(args.area);raw=safe_path(area['raw_dir'])/'imagery';raw.mkdir(parents=True,exist_ok=True)
    out=safe_path(area['processed_dir'])/'imagery';out.mkdir(parents=True,exist_ok=True)
    existing=ROOT/f'docs/enhanced_v001/{args.area}_imagery.json'
    if existing.exists() and json.loads(existing.read_text()).get('status')=='usable':
        for name,digest in json.loads(existing.read_text())['products'].items():
            if sha(safe_path(name))!=digest:raise ValueError('Completed imagery output changed: '+name)
        print('Verified completed acquisition retained:', args.area);return
    report={'area':args.area,'status':'unavailable','optional':True,'score_weight':0,'sources':[]}
    try:
        a,b,c,d=area['study_bounds'];s=osr.SpatialReference();s.ImportFromEPSG(26910)
        w=osr.SpatialReference();w.ImportFromEPSG(4326);w.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        tx=osr.CoordinateTransformation(s,w);xy=[tx.TransformPoint(x,y) for x in [a,c] for y in [b,d]]
        bbox=[min(p[0] for p in xy),min(p[1] for p in xy),max(p[0] for p in xy),max(p[1] for p in xy)]
        catalog=raw/'stac_catalog.json'
        url='https://planetarycomputer.microsoft.com/api/stac/v1/search'
        params={'collections':'naip','bbox':','.join(map(str,bbox)),'limit':100,
                'datetime':'2020-01-01T00:00:00Z/2026-10-20T00:00:00Z'}
        if catalog.exists():j=json.loads(catalog.read_text())
        else:
            response=requests.get(url,params=params,timeout=90);response.raise_for_status();j=response.json();write_json(catalog,j)
        report['catalog']={'path':str(catalog.relative_to(ROOT)),'sha256':sha(catalog),
            'url':requests.Request('GET',url,params=params).prepare().url}
        if any(link['rel']=='next' for link in j.get('links',[])):
            raise RuntimeError('Catalog page incomplete; bounded acquisition refused')
        study=ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))');remaining=study.Clone()
        to_utm=osr.CoordinateTransformation(w,s);selected=[]
        for feature in sorted(j.get('features',[]),key=lambda f:(f['properties']['datetime'],f['id']),reverse=True):
            geom=ogr.CreateGeometryFromJson(json.dumps(feature['geometry']));geom.Transform(to_utm)
            if not geom.Intersects(remaining):continue
            intersection=geom.Intersection(remaining)
            if intersection.IsEmpty() or intersection.GetArea()<1:continue
            selected.append((feature,geom));remaining=remaining.Difference(geom)
            if remaining.GetArea()<1:break
        if not selected:raise RuntimeError('No recent public NAIP footprints cover the study')
        if len(selected)>cfg['optional']['imagery_max_export_requests_per_area']:
            raise RuntimeError('Bounded imagery item budget exceeded')
        resolution=max(float(f['properties']['gsd']) for f,g in selected)
        if (c-a)*(d-b)/resolution**2 > cfg['optional']['imagery_max_pixels_per_area']:
            raise RuntimeError('Bounded imagery pixel budget exceeded')
        files=[];tokens={}
        for feature,geom in selected:
            asset=feature['assets']['image'];href=asset['href'];path=raw/(feature['id']+'.tif')
            assert [v['common_name'] for v in asset['eo:bands']]==['red','green','blue','nir']
            if not path.exists():
                parsed=urlparse(href);account=parsed.hostname.split('.')[0];container=parsed.path.strip('/').split('/')[0]
                key=(account,container)
                if key not in tokens:
                    for attempt in range(4):
                        response=requests.get(f'https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}',timeout=90)
                        if response.status_code!=429:break
                        time.sleep(min(30,5*(attempt+1)))
                    response.raise_for_status();tokens[key]=response.json()['token']
                signed=href+'?'+tokens[key]
                gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN','EMPTY_DIR')
                dataset=gdal.Open('/vsicurl/'+signed)
                assert dataset.RasterCount==4 and dataset.GetSpatialRef().GetAuthorityCode(None)=='26910'
                overlap=geom.Intersection(study);xmin,xmax,ymin,ymax=overlap.GetEnvelope()
                output=gdal.Translate(str(path),dataset,projWin=[xmin,ymax,xmax,ymin],creationOptions=CO)
                assert output.RasterCount==4;output=None;dataset=None
            ds=gdal.Open(str(path));assert ds.RasterCount==4
            files.append(path)
            report['sources'].append({'item_id':feature['id'],'datetime':feature['properties']['datetime'],
                'native_resolution_m':feature['properties']['gsd'],'asset_url':href,
                'bands':['red','green','blue','nir'],'path':str(path.relative_to(ROOT)),
                'sha256':sha(path),'geotransform':ds.GetGeoTransform(),'native_crs':ds.GetProjection(),
                'operation':'native pixel crop from RGBIR COG; no contrast stretch or band substitution'})
            print(args.area,path.name,flush=True)
        final=out/'rgbnir.tif'
        if final.exists():raise FileExistsError('Refusing imagery output overwrite')
        vrt=gdal.BuildVRT('',[str(p) for p in files])
        ds=gdal.Warp(str(final),vrt,outputBounds=[a,b,c,d],dstSRS='EPSG:26910',
            xRes=resolution,yRes=resolution,resampleAlg='near',dstNodata=65535,
            outputType=gdal.GDT_UInt16,warpOptions=['UNIFIED_SRC_NODATA=YES'],creationOptions=CO)
        ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_Undefined)
        red=ds.GetRasterBand(1).ReadAsArray().astype('float32');nir=ds.GetRasterBand(4).ReadAsArray().astype('float32')
        valid=(red!=65535)&(nir!=65535)&((red+nir)>0)
        ndvi=np.divide(nir-red,nir+red,out=np.full_like(red,np.nan),where=valid)
        raster(out/'ndvi.tif',ndvi,ds)
        vegetation=np.where(valid,(ndvi>cfg['optional']['ndvi_vegetation_threshold']).astype('uint8'),255)
        raster(out/'vegetation_mask.tif',vegetation,ds,nodata=255,dtype=gdal.GDT_Byte)
        # A low-vegetation pixel may be rock, soil, water, snow, shadow or built
        # surface. Preserve a screening proxy; never label it confirmed rock.
        brightness=(red+ds.GetRasterBand(2).ReadAsArray()+ds.GetRasterBand(3).ReadAsArray())/3
        bare=np.where(valid,((ndvi<=.2)&(brightness>=40)&(brightness<=220)).astype('uint8'),255)
        raster(out/'possible_exposed_surface_mask.tif',bare,ds,nodata=255,dtype=gdal.GDT_Byte);ds=None;vrt=None
        report.update(status='usable',resolution_m=resolution,coverage_fraction=float(valid.mean()),
            vegetation_fraction_among_valid=float(vegetation[valid].mean()),
            products={str(p.relative_to(ROOT)):sha(p) for p in out.glob('*.tif')},
            limitations=['NDVI threshold is an exploratory vegetation screen, not a validated land-cover classifier.',
             'Possible exposed surface includes soil/snow/water/shadow errors and does not establish rock type.',
             'Imagery does not confirm cave entrances; no imagery score bonus is assigned.',
             'Final grid uses nearest-neighbour reprojection at the coarsest selected native resolution.'])
    except Exception as error:
        report['reason']=re.sub(r'(https?://[^\s?]+)\?[^\s]+',r'\1?[redacted]',str(error))
        report['fallback']='DEM/geological pipeline remains enabled; imagery-derived fields are NULL.'
    write_json(ROOT/f'docs/enhanced_v001/{args.area}_imagery.json',report)
    print(json.dumps({'area':args.area,'status':report['status'],'reason':report.get('reason')},indent=2))


if __name__=='__main__':gdal.UseExceptions();ogr.UseExceptions();main()
