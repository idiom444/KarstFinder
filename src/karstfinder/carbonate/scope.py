"""Explicit documented-carbonate gate, not a lithology name heuristic."""
import hashlib,json
from osgeo import ogr
from .common import ROOT,safe_path,sha


def polygons(geometry):
    kind=ogr.GT_Flatten(geometry.GetGeometryType())
    if kind==ogr.wkbPolygon:
        if not geometry.IsEmpty() and geometry.GetArea()>0:yield geometry.Clone()
    elif kind in (ogr.wkbMultiPolygon,ogr.wkbGeometryCollection):
        for part in geometry:
            yield from polygons(part)


def surface_area(geometry):
    return sum(part.GetArea() for part in polygons(geometry))


def geometry_key(geom):return hashlib.sha256(bytes(geom.Normalize().ExportToWkb())).hexdigest()


def union(geometries):
    geoms=list(geometries)
    if not geoms:return ogr.Geometry(ogr.wkbMultiPolygon)
    result=geoms[0].Clone()
    for geom in geoms[1:]:result=result.Union(geom)
    return result


def formations(cfg,area):
    evidence_path=safe_path(cfg['geology_evidence_file']);evidence=json.loads(evidence_path.read_text())
    descriptions={f['attributes']['DMU_FEATURE_QUAD_UNIT']:f['attributes'] for f in evidence['features']}
    source=safe_path(area['source_enhanced_dir'])/'geology.gpkg';ds=ogr.Open(str(source))
    layer=ds.GetLayerByName('geology');records=[];excluded=[]
    for feature in layer:
        code=feature['unit'];ident=feature['source_id']
        if code not in cfg['eligible_units']:
            excluded.append({'source_id':ident,'unit':code,'reason':'No separately documented local carbonate exposure admitted; mixed/unknown rock is not eligible.'});continue
        key=cfg['eligible_units'][code]['description_key']
        # The whitelist is an explicit reviewed decision; no word/placename match
        # can silently promote a mixed unit or a site called Marble Creek.
        if key not in descriptions:raise ValueError('Missing required carbonate lithology evidence: '+key)
        description=descriptions[key]
        if description['DMU_100K_MAP_UNIT']!=code:raise ValueError('Unit evidence mismatch')
        for part in polygons(feature.GetGeometryRef()):
            digest=geometry_key(part);records.append({'formation_id':f"{area['baseline_area_id']}:F-{ident}-{digest[:12]}",
                'source_id':ident,'unit':code,'source_ref':str(source.relative_to(ROOT))+'#source_id='+ident,
                'lithology':cfg['eligible_units'][code]['lithology'],'description_key':key,'description_source':cfg['geology_source_url'],
                'description_input':str(evidence_path.relative_to(ROOT)),'description_input_sha256':sha(evidence_path),
                'scale_denominator':100000,'unit_id_confidence':feature['id_confidence'],
                'geometry_sha256':digest,'core':part,'mixed_unit_eligible':False})
    records.sort(key=lambda f:f['formation_id'])
    return records,excluded
