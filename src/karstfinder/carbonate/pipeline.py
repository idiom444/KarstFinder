"""Reprocess existing measurements only inside documented carbonate geology."""
import csv,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from scipy import ndimage
from osgeo import gdal,ogr,osr
from karstfinder.gis import array,memory,raster,CO
from karstfinder.enhanced.registry import Grid,components
from karstfinder.enhanced.scoring import color
from .common import ROOT,config,safe_path,fresh_directory,write_json,sha,fingerprint
from .scope import formations,union,polygons,geometry_key,surface_area
from .priority import terrain_strength,priority
from .grouping import group_observations

gdal.UseExceptions();ogr.UseExceptions()


def study_polygon(bounds):
    a,b,c,d=bounds
    return ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))')


def burn(geometry,ref):
    target=memory(np.zeros((ref.RasterYSize,ref.RasterXSize),dtype='uint8'),ref)
    source=ogr.GetDriverByName('MEM').CreateDataSource('');layer=source.CreateLayer('mask',ref.GetSpatialRef(),ogr.wkbUnknown)
    if not geometry.IsEmpty():
        feature=ogr.Feature(layer.GetLayerDefn());feature.SetGeometry(geometry);layer.CreateFeature(feature)
        gdal.RasterizeLayer(target,[1],layer,burn_values=[1])
    return target.ReadAsArray().astype(bool)


def crop(path,bounds):
    a,b,c,d=bounds
    return gdal.Translate('',str(path),format='MEM',projWin=[a,d,c,b])


def window(geom,study):
    a,c,b,d=geom.GetEnvelope();s0,s1,s2,s3=study
    return [max(s0,math.floor(a/10)*10),max(s1,math.floor(b/10)*10),min(s2,math.ceil(c/10)*10),min(s3,math.ceil(d/10)*10)]


def summarize(grid,geom):return grid.summary(geom)


def clean_row(row):return {k:v for k,v in row.items() if not k.startswith('_')}


def stable_id(prefix,identifiers):return prefix+hashlib.sha256('|'.join(sorted(identifiers)).encode()).hexdigest()[:16]


def run(area_id):
    cfg,area=config(area_id);out=fresh_directory(safe_path(area['result_dir']));prepared=fresh_directory(safe_path(area['processed_dir']))
    write_json(out/'config.json',cfg)
    forms,excluded=formations(cfg,area);study=study_polygon(area['study_bounds']);base=safe_path(area['baseline_features']);enhanced=safe_path(area['source_enhanced_processed'])
    terrain=enhanced/'terrain';original=ogr.Open(str(safe_path(area['source_enhanced_dir'])/'registry.gpkg'))
    old=original.GetLayerByName('lead_footprints');old.SetIgnoredFields([f.GetName() for f in old.schema if f.GetName() not in ('object_id','kind')])
    geo_source=ogr.Open(str(safe_path(area['source_enhanced_dir'])/'geology.gpkg'))
    water=union(f.GetGeometryRef().Clone() for f in geo_source.GetLayerByName('geology') if f['unit']=='wtr')
    gridpaths={'slope':base/'slope_1m.tif','depression_depth':base/'depression_depth_1m.tif','quality':base/'feature_quality_1m.tif','epoch':base/'source_epoch_1m.tif',
        'hand':terrain/'height_above_modeled_drainage.tif','catchment':safe_path(area['baseline_feature_prepared'])/'contributing_area_10m_buffered.tif',
        'edge_contamination':terrain/'hydrologic_edge_contamination.tif'}
    gridpaths.update({f'residual_{w}m':terrain/f'residual_{w}m.tif' for w in cfg['detection']['residual_windows_m']})
    for name in ['ndvi','vegetation_mask','possible_exposed_surface_mask']:gridpaths[name]=enhanced/'imagery'/(name+'.tif')
    for name in ['ground_return_count','normal_z','surface_curvature']:gridpaths['pointcloud_'+name]=enhanced/'pointcloud'/(name+'.tif')
    grids={name:Grid(path,nodata=None if name=='edge_contamination' else 'source') for name,path in gridpaths.items()}
    tx_to_wgs=osr.SpatialReference();tx_to_wgs.ImportFromEPSG(4326);tx_to_wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    srs=osr.SpatialReference();srs.ImportFromEPSG(26910);transform=osr.CoordinateTransformation(srs,tx_to_wgs)
    observations=[];sites=[];memberships=[];scope_report=[];sensitivity=[];suppressed=Counter();cfgd=cfg['detection']
    for formation in forms:
        core=formation['core'].Difference(water);eligible=core.Buffer(cfg['boundary_margin_m']).Intersection(study).Difference(water)
        formation['_eligible']=eligible
        bounds=window(core.Buffer(max(cfg['boundary_sensitivity_m'])),area['study_bounds'])
        directory=fresh_directory(prepared/f"formation_{formation['source_id']}_{formation['geometry_sha256'][:12]}")
        ref=crop(base/'slope_1m.tif',bounds);slopes=ref.ReadAsArray();depth=crop(base/'depression_depth_1m.tif',bounds).ReadAsArray();quality=crop(base/'feature_quality_1m.tif',bounds).ReadAsArray()==1
        eligible_mask=burn(eligible,ref);core_mask=burn(core,ref)
        code=np.where(core_mask,1,np.where(eligible_mask,2,0)).astype('uint8');raster(directory/'eligibility_1m.tif',code,ref,nodata=255,dtype=gdal.GDT_Byte)
        ref10=crop(terrain/'height_above_modeled_drainage.tif',bounds);hand=ref10.ReadAsArray();catch=crop(gridpaths['catchment'],bounds).ReadAsArray()
        qa10=quality.reshape(ref10.RasterYSize,10,ref10.RasterXSize,10).all(axis=(1,3))
        eligible10=burn(eligible,ref10);nd=ref10.GetRasterBand(1).GetNoDataValue();hydro=eligible10&qa10&np.isfinite(hand)&(hand!=nd)&(hand<=cfgd['hydrology_hand_m'])&(catch>=cfgd['hydrology_catchment_m2'])
        raster(directory/'hydrology_eligible_10m.tif',hydro.astype('uint8'),ref10,nodata=255,dtype=gdal.GDT_Byte)
        definitions=[('cliff',(slopes>=cfgd['cliff_slope_deg'])&quality&eligible_mask,ref,cfgd['cliff_min_area_m2']),
            ('depression',(depth>=cfgd['depression_depth_m'])&quality&eligible_mask,ref,cfgd['depression_min_area_m2']),
            ('hydrology',hydro,ref10,cfgd['hydrology_min_area_m2'])]
        local=[]
        for kind,binary,reference,minimum in definitions:
            for raw_geom in components(binary,reference,minimum):
                clipped=raw_geom.Intersection(eligible)
                for geom in polygons(clipped):
                    if geom.GetArea()+1e-7<minimum:suppressed['below_minimum_after_exact_geological_clip']+=1;continue
                    measured={name:summarize(grid,geom) for name,grid in grids.items()}
                    q=measured['quality']
                    if q is None or q['min']<1:suppressed['invalid_native_quality_support']+=1;continue
                    overlap=geom.Intersection(core);fraction=min(1,max(0,surface_area(overlap)/geom.GetArea()))
                    status='mapped_carbonate' if fraction>=1-1e-8 else 'carbonate_and_contact_margin' if fraction>0 else 'boundary_only'
                    observed=terrain_strength(kind,measured,cfg['scoring']);strength,factor=priority(True,fraction,observed,cfg['scoring'])
                    point=overlap.PointOnSurface() if surface_area(overlap)>0 else geom.PointOnSurface()
                    lon,lat,_=transform.TransformPoint(point.GetX(),point.GetY())
                    ident=stable_id(area_id+':O-', [formation['formation_id'],kind,geometry_key(geom)])
                    old.SetSpatialFilter(geom);old.SetAttributeFilter("kind='"+kind+"'")
                    source_ids=sorted(f['object_id'] for f in old if surface_area(f.GetGeometryRef().Intersection(geom))>1e-7)
                    old.SetSpatialFilter(None);old.SetAttributeFilter(None)
                    contradictions=[]
                    if status!='mapped_carbonate':contradictions.append(f'{100*(1-fraction):.1f}% of the footprint is in the assumed 25 m contact margin, not mapped marble.')
                    if (measured['edge_contamination'] or {}).get('max',0)>0:contradictions.append('DEM catchment may receive unmodeled flow beyond the support boundary.')
                    if kind=='hydrology':contradictions.append('Ordinary modeled surface drainage; no measured spring, sink or infiltration.')
                    uncertainty=['1:100,000 contacts are approximate; the 25 m margin is an assumption, not measured accuracy.','No opening confirmed; glacial terrain, talus, forest, snow and airborne overhang occlusion remain.','Representative coordinate is not an entrance or an access route.']
                    alternatives={'cliff':'Glacial rock face, rockfall scar, talus edge or interpolation artifact.','depression':'Glacial hollow, tarn, breakdown, vegetation/DEM artifact or excavation.','hydrology':'Ordinary valley drainage, glacial channel or routing artifact.'}[kind]
                    has_imagery=measured['ndvi'] is not None;has_cloud=(measured['pointcloud_ground_return_count'] or {}).get('max',0)>0
                    row={'object_id':ident,'kind':kind,'formation_id':formation['formation_id'],'source_unit_id':formation['source_id'],'source_unit':formation['unit'],
                        'eligibility_status':status,'carbonate_fraction':fraction,'area_m2':geom.GetArea(),'easting':point.GetX(),'northing':point.GetY(),'longitude':lon,'latitude':lat,
                        'terrain_anomaly_strength':observed,'geological_support_factor':factor,'prospecting_priority':strength,'score':strength,'evidence_strength':strength,'color_hex':color(strength),
                        'data_confidence':.4+.3+.2*has_imagery+.1*has_cloud,'geological_confidence':.25 if status=='boundary_only' else .5,
                        'fieldwork_status':'Not yet investigated','access_status':'Not screened; no route verified','model_version':cfg['version'],'priority_model':cfg['scoring']['version'],
                        'source_v001_ids':source_ids,'source_registry':str((safe_path(area['source_enhanced_dir'])/'registry.gpkg').relative_to(ROOT)),
                        'geology_evidence':formation['description_key'],'measurements':measured,'contradictory_evidence':contradictions,'uncertainty':uncertainty,'alternatives':alternatives,
                        'geometry_sha256':geometry_key(geom),'_geom':geom,'_point':point,'_core_overlap':overlap}
                    local.append(row)
        groups=group_observations(local,eligible,cfg['sites']['maximum_local_gap_m'])
        for group in groups:
            members=group['members'];surface=[r for r in members if r['kind']!='hydrology'];best=max(surface or members,key=lambda r:(r['prospecting_priority'],r['carbonate_fraction'],r['object_id']))
            priority_member=max(surface,key=lambda r:(r['prospecting_priority'],r['object_id']))
            ident=stable_id(area_id+':S-', [formation['formation_id']]+sorted(r['object_id'] for r in (surface or members)))
            geom=union(r['_geom'] for r in members);fraction=min(1,surface_area(geom.Intersection(core))/geom.GetArea());counts=Counter(r['kind'] for r in members)
            status='mapped_carbonate' if all(r['eligibility_status']=='mapped_carbonate' for r in members) else 'boundary_only' if fraction<=1e-9 else 'carbonate_and_contact_margin'
            if any(surface_area(r['_core_overlap'])>0 for r in members):
                point_members=[r for r in surface or members if surface_area(r['_core_overlap'])>0] or [r for r in members if surface_area(r['_core_overlap'])>0]
                best=max(point_members,key=lambda r:(r['prospecting_priority'],r['carbonate_fraction'],r['object_id']))
            point=best['_point'].Clone();lon,lat,_=transform.TransformPoint(point.GetX(),point.GetY())
            strength=priority_member['prospecting_priority'];kinds=', '.join(f'{n} {k}' for k,n in sorted(counts.items()))
            scope_text='documented mapped marble' if status=='mapped_carbonate' else 'mapped marble plus its flagged contact margin' if status!='boundary_only' else 'the uncertain contact margin only; carbonate is not established at this coordinate'
            explanation=f"{formation['unit']} marble, DNR polygon {formation['source_id']}: {kinds} in {scope_text}. Related surface patches overlap or have <=10 m eligible connectors in this same formation. Priority is the strongest cliff/depression member; drainage is context only. The index is not a cave probability."
            row={'object_id':ident,'kind':'cliff' if counts['cliff'] else 'depression' if counts['depression'] else 'hydrology',
                'formation_id':formation['formation_id'],'source_unit':formation['unit'],'source_unit_id':formation['source_id'],'eligibility_status':status,
                'area_m2':geom.GetArea(),'carbonate_fraction':fraction,'easting':point.GetX(),'northing':point.GetY(),'longitude':lon,'latitude':lat,
                'score':strength,'prospecting_priority':strength,'evidence_strength':strength,'color_hex':color(strength),
                'terrain_anomaly_strength':priority_member['terrain_anomaly_strength'],'max_member_terrain_anomaly_strength':max(r['terrain_anomaly_strength'] for r in members),'geological_support_factor':priority_member['geological_support_factor'],
                'data_confidence':best['data_confidence'],'geological_confidence':best['geological_confidence'],'member_count':len(members),'method_types':dict(counts),
                'member_ids':sorted(r['object_id'] for r in members),'source_v001_ids':sorted({v for r in members for v in r['source_v001_ids']}),
                'waypoint_member_id':best['object_id'],'priority_member_id':priority_member['object_id'],'grouping_edges':group['edges'],'drainage_attachments':group['attachments'],
                'evidence':explanation,'contradictory_evidence':sorted({v for r in members for v in r['contradictory_evidence']}),
                'uncertainty':sorted({v for r in members for v in r['uncertainty']}),'alternatives':sorted({r['alternatives'] for r in members}),
                'fieldwork_status':'Not yet investigated','access_status':'Not screened; no route verified','model_version':cfg['version'],'priority_model':cfg['scoring']['version'],
                'geology_evidence':formation['description_key'],'_geom':geom,'_point':point}
            sites.append(row)
            for member in members:memberships.append({'site_id':ident,'observation_id':member['object_id'],'role':'drainage context' if member['kind']=='hydrology' and surface else 'surface evidence' if surface else 'single-method drainage setting','formation_id':formation['formation_id']})
        attached_ids={m['object_id'] for group in groups for m in group['members']}
        for row in local:row['evidence_role']='surface candidate evidence' if row['kind']!='hydrology' else 'attached drainage context' if row['object_id'] in attached_ids else 'unattached drainage context; not a destination'
        observations+=local
        # Geometry-scope sensitivity only, using unchanged detector thresholds.
        for margin in cfg['boundary_sensitivity_m']:
            region=core.Buffer(margin).Intersection(study).Difference(water) if margin else core
            m=burn(region,ref)&quality;counts={}
            for kind,binary,minarea in [('cliff',slopes>=cfgd['cliff_slope_deg'],cfgd['cliff_min_area_m2']),('depression',depth>=cfgd['depression_depth_m'],cfgd['depression_min_area_m2'])]:
                counts[kind]=sum(g.Intersection(region).GetArea()+1e-7>=minarea for g in components(binary&m,ref,minarea))
            sensitivity.append({'formation_id':formation['formation_id'],'margin_m':margin,'native_eligible_pixels':int(m.sum()),'surface_component_counts':counts})
        scope_report.append({**{k:v for k,v in formation.items() if k not in ('core','_eligible')},'mapped_carbonate_area_m2':core.GetArea(),'eligible_area_with_margin_m2':eligible.GetArea(),'observations':len(local),'sites':len(groups),'boundary_only_observations':sum(r['eligibility_status']=='boundary_only' for r in local),'bounds_utm':bounds})
        print(area_id,formation['source_id'],'observations',len(local),'sites',len(groups),flush=True)
    observations.sort(key=lambda r:(-r['score'],r['object_id']));sites.sort(key=lambda r:(-r['score'],r['object_id']))
    for records in [observations,sites]:
        for rank,row in enumerate(records,1):row['rank']=rank
    save(out,srs,forms,observations,sites,memberships,cfg,area)
    report={'version':cfg['version'],'area':area_id,'scope':'Explicit carbonate exposure polygons plus 25 m flagged boundary margin; no blanket melange/unknown eligibility.',
        'formations':scope_report,'excluded_geological_polygons':excluded,'observations':len(observations),'sites':len(sites),'by_kind':dict(Counter(r['kind'] for r in observations)),
        'unattached_context_observations':sum(r['object_id'] not in {m['observation_id'] for m in memberships} for r in observations),
        'boundary_only_sites':sum(r['eligibility_status']=='boundary_only' for r in sites),'single_method_sites':sum(len(r['method_types'])==1 for r in sites),
        'suppressed':dict(suppressed),'geology_insufficient':'Outside the listed mapped marble bodies, local carbonate exposure is not established; no candidates generated there. Finer-scale exposure/karst suitability and within-unit purity remain unresolved.',
        'no_documented_carbonate_coverage':not bool(forms),'caves_confirmed':0,'independently_blind':False,'known_cave_inputs_used':False}
    write_json(out/'summary.json',report);write_json(out/'boundary_sensitivity.json',sensitivity)
    write_json(ROOT/f'docs/carbonate_v001/{area_id}_summary.json',report)
    inputs=[ROOT/'configs/carbonate_v001.json',safe_path(cfg['geology_evidence_file']),safe_path(area['source_enhanced_dir'])/'geology.gpkg',safe_path(area['source_enhanced_dir'])/'registry.gpkg']+[p for p in gridpaths.values() if p.exists()]
    manifest={'area':area_id,'config_sha256':sha(ROOT/'configs/carbonate_v001.json'),'inputs':fingerprint(inputs),
        'prepared':fingerprint(list(prepared.rglob('*.tif'))),'outputs':fingerprint(list(out.iterdir())),
        'code':fingerprint(list((ROOT/'src/karstfinder/carbonate').glob('*.py'))),'scoring_model':cfg['scoring']['version']}
    write_json(out/'manifest.json',manifest);write_json(ROOT/f'docs/carbonate_v001/{area_id}_manifest.json',manifest)
    return report


def write_layer(ds,name,records,geometry_type,srs,geometry_key_name):
    layer=ds.CreateLayer(name,srs,geometry_type)
    # Empty areas have a valid schema and no fabricated candidates.
    fields={k for row in records for k in row if not k.startswith('_')} or {'object_id','rank','score','kind','easting','northing'}
    integer={'rank','member_count'};real={k for row in records for k,v in row.items() if isinstance(v,float)}
    order=sorted(fields)
    for k in order:layer.CreateField(ogr.FieldDefn(k,ogr.OFTInteger if k in integer else ogr.OFTReal if k in real else ogr.OFTString))
    for row in records:
        feature=ogr.Feature(layer.GetLayerDefn())
        if geometry_key_name:feature.SetGeometry(row[geometry_key_name])
        for k in order:
            value=row.get(k)
            if value is not None:feature[k]=json.dumps(value,separators=(',',':'),allow_nan=False) if isinstance(value,(list,dict)) else value
        layer.CreateFeature(feature)
    return layer


def save(out,srs,forms,observations,sites,memberships,cfg,area):
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'prospecting.gpkg'))
    for name,records,kind,geom in [('candidates',sites,ogr.wkbPoint,'_point'),('candidate_footprints',sites,ogr.wkbUnknown,'_geom'),('observations',observations,ogr.wkbPoint,'_point'),('observation_footprints',observations,ogr.wkbUnknown,'_geom'),('membership',memberships,ogr.wkbNone,None)]:write_layer(ds,name,records,kind,srs,geom)
    formation_rows=[];margin_rows=[]
    for f in forms:
        member_sites=[r for r in sites if r['formation_id']==f['formation_id']]
        row={k:v for k,v in f.items() if k not in ('core','_eligible')};row.update(site_count=len(member_sites),observation_count=sum(r['formation_id']==f['formation_id'] for r in observations),site_ids=[r['object_id'] for r in member_sites],assessment='Documented marble with local noncarbonate interbeds possible; unvalidated cave prospecting. No route verified.',_geom=f['core'])
        formation_rows.append(row);margin_rows.append({**row,'margin_m':cfg['boundary_margin_m'],'_geom':f['_eligible'].Difference(f['core'])})
    write_layer(ds,'formations',formation_rows,ogr.wkbUnknown,srs,'_geom');write_layer(ds,'uncertainty_margins',margin_rows,ogr.wkbUnknown,srs,'_geom');ds=None
    for name,records in [('observations',observations),('candidates',sites)]:
        plain=[clean_row(r) for r in records];write_json(out/(name+'.json'),plain)
        fields=list(plain[0]) if plain else ['object_id','rank','score','kind','easting','northing']
        with (out/(name+'.csv')).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in plain)
    write_json(out/'membership.json',memberships)
    # Persistent, scoped score display for the exact continuous legend.
    a,b,c,d=area['study_bounds'];path=out/'priority_display_10m.tif'
    ref=gdal.Open(str(safe_path(area['baseline_landscape'])/'combined_score.tif'))
    ds=gdal.GetDriverByName('GTiff').Create(str(path),ref.RasterXSize,ref.RasterYSize,1,gdal.GDT_Float32,CO);ds.SetGeoTransform(ref.GetGeoTransform());ds.SetProjection(ref.GetProjection());ds.GetRasterBand(1).SetNoDataValue(-9999);ds.GetRasterBand(1).Fill(-9999)
    source=ogr.Open(str(out/'prospecting.gpkg'));layer=source.ExecuteSQL('SELECT * FROM candidate_footprints ORDER BY score ASC');gdal.RasterizeLayer(ds,[1],layer,options=['ATTRIBUTE=score','ALL_TOUCHED=TRUE']);ds=None;source=None
