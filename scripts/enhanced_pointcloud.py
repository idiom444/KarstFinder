#!/usr/bin/env python3
"""Bounded optional native LAS acquisition, strict units, and DEM fallback."""
import argparse,json,sys,requests
from pathlib import Path
from osgeo import ogr,osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,write_json,sha
from karstfinder.enhanced.pointcloud import process


def main():
    ap=argparse.ArgumentParser();ap.add_argument('area',choices=config()['areas']);args=ap.parse_args()
    cfg,area=config(args.area);raw=safe_path(area['raw_dir'])/'pointcloud';out=safe_path(area['processed_dir'])/'pointcloud'
    existing=ROOT/f'docs/enhanced_v001/{args.area}_pointcloud.json'
    if existing.exists():
        saved=json.loads(existing.read_text())
        if saved.get('status')=='usable_partial':
            for name,digest in saved['products'].items():
                if sha(safe_path(name))!=digest:raise ValueError('Completed point-cloud output changed: '+name)
            print('Verified completed point-cloud acquisition retained:',args.area);return
    out.mkdir(parents=True,exist_ok=True);report={'area':args.area,'optional':True,'status':'unavailable','score_weight':0}
    try:
        catalog=raw/'catalog.json'
        if not catalog.exists():
            raw.mkdir(parents=True,exist_ok=True)
            context=ogr.Open(str(safe_path(area['baseline_processed'])/'context.gpkg'))
            geoms=[f.GetGeometryRef().Clone() for f in context.GetLayerByName('bedrock') if f['MAP_UNIT_100K'] in ('PMmb(e)','TRmb(e)')]
            if not geoms:raise ValueError('No mapped carbonate reference for bounded acquisition')
            point=max(geoms,key=lambda g:g.GetArea()).PointOnSurface();x,y=point.GetX(),point.GetY()
            u=osr.SpatialReference();u.ImportFromEPSG(26910);w=osr.SpatialReference();w.ImportFromEPSG(4326);w.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            lon,lat,_=osr.CoordinateTransformation(u,w).TransformPoint(x,y)
            response=requests.get('https://tnmaccess.nationalmap.gov/api/v1/products',params={'datasets':'Lidar Point Cloud (LPC)','bbox':f'{lon-.004},{lat-.003},{lon+.004},{lat+.003}','max':100},timeout=90);response.raise_for_status();catalog_data=response.json()
            if catalog_data.get('total',0)>100:raise ValueError('Bounded point catalog is incomplete')
            write_json(catalog,{'catalog':catalog_data,'center_utm':[x,y],'center_wgs84':[lon,lat],'request_url':response.url})
        record=json.loads(catalog.read_text());items=record['catalog']['items']
        report['catalog']={'path':str(catalog.relative_to(ROOT)),'sha256':sha(catalog),'request_url':record['request_url']}
        budget=cfg['optional']['pointcloud_max_download_bytes_per_area']
        eligible=[i for i in items if 0<int(i.get('sizeInBytes',0))<=budget]
        if not eligible:raise ValueError('No tile within declared 250 MB budget. Public KingCo EPT footprint does not cover approved mountain areas; no requester-pays data used.')
        item=sorted(eligible,key=lambda i:i['sizeInBytes'])[0];source=raw/Path(item['downloadURL']).name
        if source.exists() and source.stat().st_size!=item['sizeInBytes']:raise ValueError('Incomplete cached download; retain for diagnosis, do not process')
        if not source.exists():
            temp=source.with_suffix('.download');r=requests.get(item['downloadURL'],stream=True,timeout=90);r.raise_for_status();n=0
            with temp.open('wb') as stream:
                for block in r.iter_content(1048576):
                    n+=len(block)
                    if n>budget:raise ValueError('Point-cloud download budget exceeded')
                    stream.write(block)
            if n!=item['sizeInBytes']:raise ValueError('Catalog/download size mismatch')
            temp.rename(source)
        report['source']={'url':item['downloadURL'],'sha256':sha(source),'bytes':source.stat().st_size,'title':item['title']}
        x,y=record['center_utm'];half=cfg['optional']['pointcloud_crop_size_m']/2
        if (out/'normals_pipeline.json').exists():raise FileExistsError('Refusing point-cloud processing overwrite')
        report.update(process(source,out,[x-half,y-half,x+half,y+half],knn=cfg['optional']['pointcloud_knn'],resolution=cfg['optional']['pointcloud_raster_resolution_m'],ground_classes=cfg['optional']['pointcloud_ground_classes']));report['status']='usable_partial'
    except Exception as e:report['reason']=str(e);report['fallback']='DEM remains enabled; unavailable point-cloud fields NULL.'
    write_json(ROOT/f'docs/enhanced_v001/{args.area}_pointcloud.json',report)
    print(json.dumps({'area':args.area,'status':report['status'],'reason':report.get('reason')},indent=2))


if __name__=='__main__':main()
