#!/usr/bin/env python3
"""Evaluate permitted local validation records; never write locations into tracked results."""
import csv,json,sys
from pathlib import Path
import numpy as np
from osgeo import gdal,ogr,osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,memory,sha
from karstfinder.freeze import verify_freeze
from karstfinder.evaluation import select_area,uncertainty_coverage,prediction_gain,kvamme_gain
from karstfinder.evaluation import qualifies_for_localization

gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()
freeze=verify_freeze(ROOT)
protocol=json.loads((ROOT/'configs/validation_v001.json').read_text())
private=ROOT/'data/private/validation';path=private/'references.geojson'
if not path.exists():raise SystemExit('Freeze verified. Supply independently sourced, permitted references at data/private/validation/references.geojson')
refs=json.loads(path.read_text());private.mkdir(parents=True,exist_ok=True)
ref=gdal.Open(str(ROOT/'results/blind_v002/combined_score_10m.tif'));shape=(ref.RasterYSize,ref.RasterXSize);gt=ref.GetGeoTransform()
models={'geology':array(ROOT/'results/blind_v002/geology_score_10m.tif'),
 'terrain':array(ROOT/'results/blind_v001/terrain_score.tif'),
 'landscape_v001':array(ROOT/'results/blind_v001/combined_score.tif'),
 'morphology':array(ROOT/'results/blind_v002/feature_score_10m.tif'),
 'combined_v002':array(ROOT/'results/blind_v002/combined_score_10m.tif')}
source=osr.SpatialReference();source.ImportFromEPSG(4326);source.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
tx=osr.CoordinateTransformation(source,ref.GetSpatialRef())
validation=[]
for item in refs['features']:
    props=item['properties'];assert props.get('source_url') and props.get('uncertainty_m') is not None
    assert props.get('permitted_use')=='local_research_only'
    assert item['geometry']['type']=='Point'
    point=ogr.CreateGeometryFromJson(json.dumps(item['geometry']));point.Transform(tx)
    radius=float(props['uncertainty_m']);assert radius>0
    regionvec=ogr.GetDriverByName('MEM').CreateDataSource('');layer=regionvec.CreateLayer('uncertainty',ref.GetSpatialRef(),ogr.wkbPolygon)
    f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(point.Buffer(radius,48));layer.CreateFeature(f)
    mask=memory(np.zeros(shape,dtype='uint8'),ref);gdal.RasterizeLayer(mask,[1],layer,burn_values=[1],options=['ALL_TOUCHED=TRUE'])
    r=int((gt[3]-point.GetY())/10);c=int((point.GetX()-gt[0])/10)
    validation.append({'id':props['record_id'],'point':point,'radius':radius,'region':mask.ReadAsArray().astype(bool),
                       'central_cell':(r,c) if 0<=r<shape[0] and 0<=c<shape[1] else None,'source':props})
rows=[]
for universe_name,universe in [('study',np.ones(shape,bool)),('comparable_geology',models['geology']>0)]:
    n=int(universe.sum())
    for model,scores in models.items():
        for budget in protocol['area_budgets']:
            # Cap at positive support: zero-score ties never manufacture a prediction.
            positive=universe&np.isfinite(scores)&(scores>0);k=min(int(n*budget),int(positive.sum()))
            selected=select_area(scores,positive,k/positive.sum(),protocol['seed']) if k and positive.any() else np.zeros(shape,bool)
            actual=float(selected.sum()/n);central=[];possible=[];robust=[];coverage=[]
            for item in validation:
                cell=item['central_cell'];central.append(bool(cell and selected[cell]))
                hit=uncertainty_coverage(selected,item['region']);possible.append(hit['possible']);robust.append(hit['robust'])
                if hit['coverage_fraction'] is not None:coverage.append(hit['coverage_fraction'])
            recall=float(np.mean(central)) if central else None
            rows.append({'universe':universe_name,'model':model,'requested_area_fraction':budget,'actual_area_fraction':actual,
                 'universe_area_km2':n*abs(gt[1]*gt[5])/1e6,'selected_area_km2':int(selected.sum())*abs(gt[1]*gt[5])/1e6,
                 'central_reference_fraction_selected':recall,'possible_uncertainty_fraction':float(np.mean(possible)) if possible else None,
                 'robust_uncertainty_fraction':float(np.mean(robust)) if robust else None,'mean_uncertainty_region_coverage':float(np.mean(coverage)) if coverage else None,
                 'descriptive_prediction_gain':prediction_gain(recall,actual) if recall is not None else None,
                 'kvamme_gain':kvamme_gain(recall,actual) if recall is not None else None,
                 'random_uniform_matched_geology_expected_fraction':actual if universe_name=='comparable_geology' else None})
# Only sufficiently precise independent records can test entrance localization.
features=ogr.Open(str(ROOT/'results/blind_v002/features.gpkg'));polys=features.GetLayerByName('surface_indicators');geometries=[f.GetGeometryRef().Clone() for f in polys]
localization=[]
for item in validation:
    if not qualifies_for_localization(item['source'],protocol['max_entrance_location_uncertainty_m']):continue
    distances=[geom.Distance(item['point']) for geom in geometries]
    localization.append({'record_id':item['id'],'min_indicator_geometry_distance_m':min(distances) if distances else None,
       'uncertainty_m':item['radius'],'tolerance_matches':{str(t):bool(distances and min(distances)<=t) for t in protocol['localization_tolerances_m']},
       'meaning':'Proximity to a surface indicator is not proof the entrance itself was detected'})
result={'freeze_commit':freeze['implementation_git_commit'],'reference_sha256':sha(path),'reference_count':len(validation),
 'precise_reference_count':len(localization),'uncertainty_m':[item['radius'] for item in validation],
 'localization_eligibility':'Source accuracy must be verified and uncertainty must be within the predeclared maximum; assumed radii never qualify',
 'spatial_independence_established':False,'inferential_p_values_reported':False,
 'limitations':['Presence-only incomplete inventory','Reference selection and historical exploration bias','Spatially clustered caves are not independent',
               'Large location uncertainty cannot establish entrance localization','Area fractions describe raster coverage, not probabilities'],
 'metrics':rows,'localization':localization}
(private/'evaluation_detailed.json').write_text(json.dumps(result,indent=2)+'\n')
public={k:v for k,v in result.items() if k not in ['localization','uncertainty_m']}
public['location_uncertainty_range_m']=[min(x['radius'] for x in validation),max(x['radius'] for x in validation)] if validation else None
(ROOT/'docs/validation_summary.json').write_text(json.dumps(public,indent=2)+'\n')
print(json.dumps({k:v for k,v in public.items() if k!='metrics'},indent=2))
