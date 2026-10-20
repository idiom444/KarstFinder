"""Traceable polygon geology; unknown mapping is never an unsuitable class."""
import hashlib,json
from osgeo import ogr,osr
from .common import ROOT,safe_path,write_json,sha


def classification(code,name=''):
    text=(name or '').lower()
    if code in ('PMmb(e)','TRmb(e)') or any(w in text for w in ('marble','limestone','dolostone')):return 'mapped_carbonate',1.
    if code=='JTRmt(e)':return 'possible_mixed',.35
    if code in ('wtr','Qta','Qls') or any(w in text for w in ('granodiorite','tonalite','basalt','gabbro','volcanic','stock')):return 'mapped_noncarbonate',0.
    return 'unknown',None


def build(area_id,area,out):
    raw=safe_path(area['raw_dir'])/'geology'
    polygon_source=raw/'100k_units.geojson'
    if polygon_source.exists():
        src=ogr.Open(str(polygon_source));source_layer=src.GetLayer(0)
    else:
        polygon_source=safe_path(area['baseline_processed'])/'context.gpkg'
        src=ogr.Open(str(polygon_source));source_layer=src.GetLayerByName('bedrock')
    name_source=raw/'100k_unit_lithology.json'
    names=json.loads(name_source.read_text())['features'] if name_source.exists() else [];lookup={}
    for f in names:
        p=f['attributes'];lookup.setdefault(p['DMU_100K_MAP_UNIT'],[]).append(p)
    a,b,c,d=area['study_bounds'];clip=ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))')
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out));srs=osr.SpatialReference();srs.ImportFromEPSG(26910)
    fields={'source_id':ogr.OFTString,'unit':ogr.OFTString,'lithology_name':ogr.OFTString,'geo_class':ogr.OFTString,'geo_support':ogr.OFTReal,'scale_denom':ogr.OFTInteger,'contact_proxy_m':ogr.OFTReal,'id_confidence':ogr.OFTString,'source_ref':ogr.OFTString,'zone_id':ogr.OFTString}
    layer=ds.CreateLayer('geology',srs,ogr.wkbUnknown)
    for k,t in fields.items():layer.CreateField(ogr.FieldDefn(k,t))
    zones=ds.CreateLayer('zones',srs,ogr.wkbUnknown)
    for k,t in {**fields,'reference_easting':ogr.OFTReal,'reference_northing':ogr.OFTReal,'candidate_count':ogr.OFTInteger,'max_strength':ogr.OFTReal,'assessment':ogr.OFTString}.items():zones.CreateField(ogr.FieldDefn(k,t))
    records=[]
    for f in source_layer:
        geom=f.GetGeometryRef().Intersection(clip)
        if geom.IsEmpty() or geom.GetArea()==0:continue
        code=f['MAP_UNIT_100K'];quad=dict(f.items()).get('MAP_UNIT_100K_QUAD_NAME','')
        choices=lookup.get(code,[]);matched=[p for p in choices if p['DMU_100K_QUAD_NAME']==quad]
        # Do not silently take a same-code description from another quadrangle.
        p=(matched or [{}])[0];name=p.get('DMU_100K_FULL_NAME') or ''
        cls,g=classification(code,name);source_id=str(f['OBJECTID'])
        zid=f'{area_id}:DNR100k:{source_id}' if cls in ('mapped_carbonate','possible_mixed') else ''
        row={'source_id':source_id,'unit':code,'lithology_name':name,'geo_class':cls,'geo_support':g,'scale_denom':100000,'contact_proxy_m':50.,'id_confidence':f['MAP_UNIT_100K_ID_CONFIDENCE'],'source_ref':str(polygon_source.relative_to(ROOT))+'#OBJECTID='+source_id,'zone_id':zid}
        item=ogr.Feature(layer.GetLayerDefn());item.SetGeometry(geom)
        for k,v in row.items():
            if v is not None:item[k]=v
        layer.CreateFeature(item);records.append((row,geom.Clone()))
        if zid:
            z=ogr.Feature(zones.GetLayerDefn());z.SetGeometry(geom)
            for k,v in row.items():
                if v is not None:z[k]=v
            pt=geom.PointOnSurface();z['reference_easting']=pt.GetX();z['reference_northing']=pt.GetY();z['candidate_count']=0
            z['assessment']='Mapped geological unit footprint; unvalidated prospecting. Approximate contacts; no route verified.';zones.CreateFeature(z)
    # Preserve source structural fields; faults remain neutral context.
    context=ogr.Open(str(safe_path(area['baseline_processed'])/'context.gpkg'))
    for name in ['faults','contacts','orientations','study_area']:
        source=context.GetLayerByName(name)
        if source:ds.CopyLayer(source,name)
    ds=None
    return records


def context_for(geom,records,buffer_m=100):
    overlaps=[];nearest=None
    for row,g in records:
        if row['geo_class']=='mapped_carbonate':
            distance=geom.Distance(g);nearest=distance if nearest is None else min(nearest,distance)
        if geom.Intersects(g):
            size=geom.Intersection(g).GetArea()
            if size>0:overlaps.append((row,size/geom.GetArea()))
    carbon=[(r,f) for r,f in overlaps if r['geo_class']=='mapped_carbonate']
    mixed=[(r,f) for r,f in overlaps if r['geo_class']=='possible_mixed']
    if carbon:cls='mapped_carbonate';support=max(f for r,f in carbon);zid=max(carbon,key=lambda r:r[1])[0]['zone_id']
    elif nearest is not None and nearest<=buffer_m:cls='contact_uncertain';support=.5;zid=''
    elif mixed:cls='possible_mixed';support=.35*sum(f for r,f in mixed);zid=max(mixed,key=lambda r:r[1])[0]['zone_id']
    elif overlaps and all(r['geo_class']=='mapped_noncarbonate' for r,f in overlaps):cls='mapped_noncarbonate';support=0.;zid=''
    else:cls='unknown';support=None;zid=''
    return {'geo_class':cls,'geology_component':support,'zone_id':zid,'distance_carbonate_m':nearest,
            'carbonate_fraction':sum(f for r,f in carbon),'geology_sources':[r['source_ref'] for r,f in overlaps],
            'geological_confidence':.5 if cls=='mapped_carbonate' else .25 if cls in ('possible_mixed','contact_uncertain') else .5 if cls=='mapped_noncarbonate' else 0.}
