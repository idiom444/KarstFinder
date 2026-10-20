#!/usr/bin/env python3
"""Bounded, whitelisted geology acquisition; excludes generic points/reports."""
import argparse
import json
from pathlib import Path
import sys
import requests
from osgeo import ogr

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config, safe_path, write_json, sha

SERVICES={
 '24k':('https://gis.dnr.wa.gov/site3/rest/services/Geology/24K_Surface_Geology_WA_GeMS/MapServer',
         49,42,54,'MAP_UNIT_24K','DMU_24K',24000),
 'mid':('https://gis.dnr.wa.gov/site3/rest/services/Geology/25_to_99K_Surface_Geology_WA_GeMS/MapServer',
         11,10,12,'MAP_UNIT_INT','DMU_INT',99000),
 '100k':('https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer',
         11,12,13,'MAP_UNIT_100K','DMU_100K',100000)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('area',choices=config()['areas']);args=parser.parse_args()
    cfg,area=config(args.area);raw=safe_path(area['raw_dir'])/'geology';raw.mkdir(parents=True,exist_ok=True)
    bounds=area['study_bounds'];a,b,c,d=bounds;pad=1100
    common={'geometry':','.join(map(str,[a-pad,b-pad,c+pad,d+pad])),
        'geometryType':'esriGeometryEnvelope','inSR':26910,'outSR':26910,
        'spatialRel':'esriSpatialRelIntersects','resultRecordCount':2000,'where':'1=1'}
    records=[];coverage={};session=requests.Session()

    def get(url,name,params):
        path=raw/name
        if path.exists():j=json.loads(path.read_text())
        else:
            r=session.get(url,params=params,timeout=90);r.raise_for_status();j=r.json()
            if j.get('error') or j.get('exceededTransferLimit') or j.get('properties',{}).get('exceededTransferLimit'):
                raise RuntimeError(f'Incomplete/error source: {url}: {j.get("error")}')
            write_json(path,j)
        records.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),
            'url':requests.Request('GET',url,params=params).prepare().url})
        return j

    for scale,(base,units,sources,dmu,prefix,dp,denominator) in SERVICES.items():
        try:
            meta=get(base+'/'+str(units),scale+'_unit_metadata.json',{'f':'json'})
            fields=[f['name'] for f in meta['fields'] if f['name']=='OBJECTID' or
                    (f['name'].startswith(prefix) and any(f['name'].endswith(s) for s in
                     ['_ID_CONFIDENCE','_QUAD_UNIT','_MAP_AND_UNIT','_PUB_NUMBER','_QUAD_NAME'])) or f['name']==prefix]
            polygons=get(base+'/'+str(units)+'/query',scale+'_units.geojson',
                {**common,'f':'geojson','outFields':','.join(fields)})
            coverage[scale]={'polygons_returned':len(polygons['features']),
                'nominal_scale_denominator':denominator,'scale_note':'25–99k range; actual publication scale required' if scale=='mid' else 'nominal compilation scale',
                'units':sorted({f['properties'].get(prefix) for f in polygons['features'] if f['properties'].get(prefix)})}
            smeta=get(base+'/'+str(sources),scale+'_source_metadata.json',{'f':'json'})
            sf=[f['name'] for f in smeta['fields'] if f['name']=='OBJECTID' or any(s in f['name'] for s in ['CITATION','PUBLISHER','PUB_NUMBER','QUAD','LINK','STATUS'])]
            get(base+'/'+str(sources)+'/query',scale+'_source_catalog.geojson',
                {**common,'f':'geojson','outFields':','.join(sf)})
            dm=get(base+'/'+str(dmu),scale+'_dmu_metadata.json',{'f':'json'})
            # Unit names and controlled geomaterial/age fields only. Free-form
            # historical descriptions may mix geology with known cave locations.
            df=[f['name'] for f in dm['fields'] if f['name']=='OBJECTID' or f['name'].startswith(dp) and
                any(f['name'].endswith(s) for s in ['_MAP_UNIT','_NAME','_FULL_NAME','_GEOMATERIAL','_GEOMATERIAL_CONF','_AGE','_QUAD_UNIT','_MAP_AND_UNIT','_QUAD_NAME','_PUB_NUMBER'])]
            names=coverage[scale]['units']
            where=dp+'_MAP_UNIT IN ('+','.join("'"+n.replace("'","''")+"'" for n in names)+')' if names else '1=0'
            get(base+'/'+str(dmu)+'/query',scale+'_unit_lithology.json',
                {'f':'json','where':where,'outFields':','.join(df),'returnGeometry':'false','resultRecordCount':2000})
        except (requests.RequestException,RuntimeError,ValueError) as error:
            coverage[scale]={'status':'unavailable','reason':str(error),'fallback':'Preserved baseline geology remains available; missing descriptions stay unknown.'}
    report={'area':args.area,'coverage':coverage,'records':records,'cave_reference_sources_read':False,
        'unknown_geology_is_not_unsuitable':True,'notes':['No generic point/station/vent/fossil datasets requested.',
        'Finer mapping only overrides where a returned polygon and explicit lithology support it.',
        'Source catalogs include publications absent from statewide unit coverage; catalog availability does not guarantee a finer map.',
        'Free-form map pamphlets and historical cave-bearing reports were not opened.']}
    write_json(ROOT/f'docs/enhanced_v001/{args.area}_geology_acquisition.json',report)
    print(json.dumps({'area':args.area,'coverage':coverage},indent=2))


if __name__=='__main__':main()
