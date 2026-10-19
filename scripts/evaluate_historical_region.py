#!/usr/bin/env python3
"""Section-level historical evidence: evaluate one broad region, never fabricate entrances."""
import json,sys
from pathlib import Path
import numpy as np
from osgeo import gdal,ogr,osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.freeze import verify_freeze
from karstfinder.gis import array,memory
verify_freeze(ROOT);gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()
p=ROOT/'data/private/validation';j=json.loads((p/'sources/plss_sections.geojson').read_text())
sections=[f for f in j['features'] if f['properties']['TOWNSHIP']=='T23R11E' and f['properties']['PLS_TWP_SUBDIV_NO']==28]
assert len(sections)==1
section=sections[0]
(p/'historical_region.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':section['geometry'],
 'properties':{'source_url':'https://www.dnr.wa.gov/publications/ger_ic40_caves_of_wa.pdf','printed_pages':'22-23',
 'record_type':'historical regional presence, not an entrance position','accuracy':'section-level; multiple named caves share the same coarse region',
 'independent_spatial_units':1,'permitted_use':'local_research_only'}}]},indent=2))
ref=gdal.Open(str(ROOT/'results/blind_v002/combined_score_10m.tif'));shape=(ref.RasterYSize,ref.RasterXSize)
s=osr.SpatialReference();s.ImportFromEPSG(4326);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
geom=ogr.CreateGeometryFromJson(json.dumps(section['geometry']));geom.Transform(osr.CoordinateTransformation(s,ref.GetSpatialRef()))
d=ogr.GetDriverByName('MEM').CreateDataSource('');l=d.CreateLayer('region',ref.GetSpatialRef(),ogr.wkbPolygon);f=ogr.Feature(l.GetLayerDefn());f.SetGeometry(geom);l.CreateFeature(f)
mask=memory(np.zeros(shape,dtype='uint8'),ref);gdal.RasterizeLayer(mask,[1],l,burn_values=[1]);region=mask.ReadAsArray().astype(bool)
rows=[]
for name,path in [('original_landscape','results/blind_v001/combined_score.tif'),('combined','results/blind_v002/combined_score_10m.tif'),
 ('surface_morphology','results/blind_v002/feature_score_10m.tif'),('geology','results/blind_v002/geology_score_10m.tif')]:
 scores=array(ROOT/path);positive=np.isfinite(scores)&(scores>0)
 rows.append({'model':name,'positive_prediction_area_in_region_km2':float((positive&region).sum()/10000),
              'fraction_of_region_with_positive_score':float((positive&region).sum()/region.sum()),'any_regional_overlap':bool((positive&region).any()),
              'entrance_localization_test':False})
report={'source':'Halliday 1963, printed pp.22-23; DNR PLSS polygon for historical section reference',
 'independent_reference_regions':1,'historical_region_area_km2':float(geom.GetArea()/1e6),
 'named_caves_not_counted_as_independent_coordinates':True,'metrics':rows,
 'interpretation':'Broad regional consistency only. Any overlap cannot establish individual entrance discovery or added skill over geology.'}
(ROOT/'docs/historical_validation_summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
