"""Union registry: immutable baseline leads plus independently retained methods."""
import csv,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from scipy import ndimage,stats
from osgeo import gdal,ogr,osr
from karstfinder.gis import array,memory,raster,polygon_layer
from .common import ROOT,config,safe_path,fresh_directory,sha,write_json,fingerprint
from .geology import build,context_for
from .scoring import combine,morphology,color

gdal.UseExceptions();ogr.UseExceptions()


def geom_key(kind,geom):
    normalized=geom.Normalize()
    return hashlib.sha256(kind.encode()+bytes(normalized.ExportToWkb())).hexdigest()


class Grid:
    """Exact footprint summaries of a persistent raster, NULL without coverage."""
    def __init__(self,path,nodata='source'):
        self.nodata=nodata
        self.path=Path(path);self.ds=gdal.Open(str(path)) if self.path.exists() else None
    def values(self,geom):
        if self.ds is None:return np.array([],dtype='float32')
        ds=self.ds;gt=ds.GetGeoTransform();xmin,xmax,ymin,ymax=geom.GetEnvelope();r=gt[1]
        x0=max(0,int(math.floor((xmin-gt[0])/r)));x1=min(ds.RasterXSize,int(math.ceil((xmax-gt[0])/r)))
        y0=max(0,int(math.floor((gt[3]-ymax)/r)));y1=min(ds.RasterYSize,int(math.ceil((gt[3]-ymin)/r)))
        if x1<=x0 or y1<=y0:return np.array([],dtype='float32')
        ref=gdal.GetDriverByName('MEM').Create('',x1-x0,y1-y0,1,gdal.GDT_Byte)
        ref.SetGeoTransform([gt[0]+x0*r,r,0,gt[3]-y0*r,0,-r]);ref.SetProjection(ds.GetProjection())
        src=ogr.GetDriverByName('MEM').CreateDataSource('');layer=src.CreateLayer('mask',ds.GetSpatialRef(),ogr.wkbUnknown)
        f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(geom);layer.CreateFeature(f)
        gdal.RasterizeLayer(ref,[1],layer,burn_values=[1])
        mask=ref.ReadAsArray()==1
        values=ds.GetRasterBand(1).ReadAsArray(x0,y0,x1-x0,y1-y0).astype('float32')[mask]
        nodata=ds.GetRasterBand(1).GetNoDataValue() if self.nodata=='source' else self.nodata
        return values[np.isfinite(values)&(values!=nodata)] if nodata is not None else values[np.isfinite(values)]
    def summary(self,geom):
        values=self.values(geom)
        if not len(values):return None
        return {'mean':float(values.mean()),'median':float(np.median(values)),'q10':float(np.quantile(values,.1)),'q90':float(np.quantile(values,.9)),'min':float(values.min()),'max':float(values.max()),'valid_pixels':int(len(values))}


def components(binary,ref,min_area):
    """Four-neighbor GIS components. No maximum-area or strength retention gate."""
    labels,n=ndimage.label(binary);counts=np.bincount(labels.ravel());res=ref.GetGeoTransform()[1]
    keep=counts*res**2>=min_area;keep[0]=False;labels[~keep[labels]]=0
    mem=memory(labels,ref,gdal.GDT_Int32);ds=ogr.GetDriverByName('MEM').CreateDataSource('')
    layer=ds.CreateLayer('objects',ref.GetSpatialRef(),ogr.wkbPolygon);layer.CreateField(ogr.FieldDefn('component',ogr.OFTInteger))
    gdal.Polygonize(mem.GetRasterBand(1),mem.GetRasterBand(1),layer,0,[])
    return [f.GetGeometryRef().Clone() for f in layer]


def serial(value):return json.dumps(value,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def run(area_id):
    cfg,area=config(area_id);out=fresh_directory(safe_path(area['result_dir']));pre=safe_path(area['processed_dir'])
    baseline=safe_path(area['baseline_features']);terrain=pre/'terrain'
    georecords=build(area_id,area,out/'geology.gpkg')
    rows={r['object_id']:r for r in csv.DictReader(safe_path(area['baseline_candidate_csv']).open())}
    source=ogr.Open(str(baseline/'features.gpkg'));entries=[];keys={}
    for f in source.GetLayerByName('surface_indicators'):
        old=rows[f['object_id']];geom=f.GetGeometryRef().Clone();key=geom_key(old['kind'],geom)
        obj={'object_id':area_id+':'+old['object_id'],'kind':old['kind'],'baseline_object_id':old['object_id'],'baseline_rank':int(old['rank']),'baseline_score':float(old['score']),'easting':float(old['easting']),'northing':float(old['northing']),'methods':{'baseline_'+old['kind']},'geom':geom,'baseline_row':old,'geometry_sha256':key}
        keys[key]=obj;entries.append(obj)
    assert len(entries)==len(rows)
    native=gdal.Open(str(baseline/'slope_1m.tif'));quality=array(baseline/'feature_quality_1m.tif')==1
    # Connected geometry is created before QA filtering, like the baseline;
    # never split a seam-crossing patch into apparently independent leads.
    for kind,name,threshold,minarea in [('cliff','slope_1m',cfg['terrain']['cliff_slope_degrees'],cfg['terrain']['cliff_min_area_m2']),('depression','depression_depth_1m',cfg['terrain']['depression_depth_m'],cfg['terrain']['depression_min_area_m2'])]:
        for geom in components(array(baseline/(name+'.tif'))>=threshold,native,minarea):
            key=geom_key(kind,geom)
            if key in keys:keys[key]['methods'].add('terrain_'+kind);continue
            obj={'object_id':f'{area_id}:E-{kind[:1].upper()}-{key[:16]}','kind':kind,'baseline_object_id':'','baseline_rank':None,'baseline_score':None,'methods':{'terrain_'+kind},'geom':geom,'baseline_row':{},'geometry_sha256':key}
            entries.append(obj);keys[key]=obj
        print(area_id,kind,'union',len(entries),flush=True)
    # Hydro-setting objects require carbonate context, modeled convergence and
    # low height above modeled drainage. A modeled endpoint is never a sink.
    ref10=gdal.Open(str(terrain/'height_above_modeled_drainage.tif'))
    mask=memory(np.zeros((ref10.RasterYSize,ref10.RasterXSize),dtype='uint8'),ref10)
    ds=ogr.GetDriverByName('MEM').CreateDataSource('');ly=ds.CreateLayer('carbonate',ref10.GetSpatialRef(),ogr.wkbUnknown)
    for row,g in georecords:
        if row['geo_class'] not in ('mapped_carbonate','possible_mixed'):continue
        f=ogr.Feature(ly.GetLayerDefn());f.SetGeometry(g.Buffer(cfg['terrain']['contact_context_m']));ly.CreateFeature(f)
    gdal.RasterizeLayer(mask,[1],ly,burn_values=[1]);context=mask.ReadAsArray()==1
    hand=array(terrain/'height_above_modeled_drainage.tif')
    a,b,c,d=area['study_bounds']
    catch=gdal.Translate('',str(safe_path(area['baseline_feature_prepared'])/'contributing_area_10m_buffered.tif'),format='MEM',projWin=[a,d,c,b]).ReadAsArray()
    hydro=context&np.isfinite(hand)&(hand<=cfg['terrain']['hydrology_setting_hand_m'])&(catch>=cfg['terrain']['modeled_stream_area_m2'])
    raster(out/'hydrological_setting_mask_10m.tif',hydro.astype('uint8'),ref10,dtype=gdal.GDT_Byte,nodata=255)
    for geom in components(hydro,ref10,cfg['terrain']['hydrology_min_area_m2']):
        key=geom_key('hydrology',geom);entries.append({'object_id':f'{area_id}:E-H-{key[:16]}','kind':'hydrology','baseline_object_id':'','baseline_rank':None,'baseline_score':None,'methods':{'hydrological_setting'},'geom':geom,'baseline_row':{},'geometry_sha256':key})
    structural=ogr.Open(str(safe_path(area['baseline_processed'])/'context.gpkg'))
    structures={name:[(dict(f.items()),f.GetGeometryRef().Clone()) for f in structural.GetLayerByName(name)] for name in ['faults','contacts','orientations']}
    # Actual mapped fault-contact intersections in carbonate, not proximity clusters.
    seen=set()
    for fr,fg in structures['faults']:
        for cr,cg in structures['contacts']:
            if not fg.Intersects(cg):continue
            intersection=fg.Intersection(cg)
            if intersection.IsEmpty() or intersection.GetDimension()!=0:continue
            points=[intersection] if intersection.GetGeometryCount()==0 else list(intersection)
            for pt in points:
                if pt.GetGeometryType() not in (ogr.wkbPoint,ogr.wkbPoint25D):continue
                geom=pt.Buffer(10).Intersection(ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'))
                if geom.IsEmpty() or geom.GetArea()==0:continue
                geo=context_for(geom,georecords)
                if geo['geo_class']!='mapped_carbonate':continue
                key=geom_key('structure',geom)
                if key in seen:continue
                seen.add(key);entries.append({'object_id':f'{area_id}:E-S-{key[:16]}','kind':'structure','baseline_object_id':'','baseline_rank':None,'baseline_score':None,'methods':{'mapped_structural_intersection'},'geom':geom,'baseline_row':{},'geometry_sha256':key})
    gridpaths={'hydrological_setting_mask_10m':out/'hydrological_setting_mask_10m.tif','contributing_area':safe_path(area['baseline_feature_prepared'])/'contributing_area_10m_buffered.tif','slope':baseline/'slope_1m.tif','depth':baseline/'depression_depth_1m.tif','quality':baseline/'feature_quality_1m.tif','epoch':baseline/'source_epoch_1m.tif'}
    gridpaths.update({f'residual_{w}m':terrain/f'residual_{w}m.tif' for w in [11,31,61]})
    gridpaths.update({p.stem:p for p in terrain.glob('*.tif') if not p.stem.endswith('buffered')})
    for name in ['ndvi','vegetation_mask','possible_exposed_surface_mask']:gridpaths[name]=pre/'imagery'/(name+'.tif')
    for name in ['all_return_count','ground_return_count','normal_z','surface_curvature','ground_z_stdev']:gridpaths['pointcloud_'+name]=pre/'pointcloud'/(name+'.tif')
    # Whitebox EdgeContamination encodes unflagged cells as zero with
    # nodata=0. Our source DEM support is complete, so zero is a measured
    # unflagged cell, not missing coverage. Preserve the original raw mask.
    grids={k:Grid(v,nodata=None if k=='hydrologic_edge_contamination' else 'source') for k,v in gridpaths.items()};rejected=Counter();retained=[]
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER);tx=osr.CoordinateTransformation(native.GetSpatialRef(),wgs)
    for n,obj in enumerate(entries):
        geom=obj.pop('geom');old=obj.pop('baseline_row');measurements={k:grid.summary(geom) for k,grid in grids.items()}
        q=measurements['quality'];legacy=bool(obj['baseline_object_id'])
        geo=context_for(geom,georecords,cfg['terrain']['contact_context_m'])
        # Suppress known bad/noise observations for NEW detections only; all old
        # coordinates survive. Geological absence never suppresses a terrain lead.
        if not legacy and obj['kind'] in ('cliff','depression') and (q is None or q['min']<1):rejected['new_component_intersects_QA_exclusion']+=1;continue
        if not legacy and any(r['unit']=='wtr' and geom.Intersects(g) and geom.Intersection(g).GetArea()>0 for r,g in georecords):rejected['new_component_intersects_mapped_open_water']+=1;continue
        pt=geom.PointOnSurface()
        if not legacy:obj.update(easting=pt.GetX(),northing=pt.GetY())
        longitude,latitude,_=tx.TransformPoint(obj['easting'],obj['northing'])
        def metric(name,key='mean'):
            value=measurements.get(name);return value.get(key) if value else None
        terrain_component=morphology(obj['kind'],metric('depth','max'),[metric(f'residual_{w}m','q10') for w in [11,31,61]])
        hydro_observed=metric('hydrological_setting_mask_10m','max')
        hydrology_component=.4 if hydro_observed==1 else 0. if hydro_observed is not None else None
        if hydrology_component:obj['methods'].add('hydrological_context')
        families={'geology_structure':{'lithology':geo['geology_component']},'terrain_hydrology_pointcloud':{'morphology':terrain_component,'hydrology_setting':hydrology_component,'pointcloud':None}}
        score,contributions,coverage=combine(families,cfg['scoring']['family_weights'])
        # Add method support labels only for actually measured positive context.
        if geo['geology_component'] and geo['geology_component']>0:obj['methods'].add('geological_context')
        if (metric('pointcloud_ground_return_count','max') or 0)>0:obj['methods'].add('pointcloud_context')
        if metric('ndvi') is not None:obj['methods'].add('imagery_context')
        dist={name:min((geom.Distance(g) for row,g in records),default=None) for name,records in structures.items()}
        nearest_orientation=min(structures['orientations'],key=lambda p:geom.Distance(p[1]),default=None)
        contradictions=[]
        if geo['geo_class']=='mapped_noncarbonate':contradictions.append('Mapped surface unit has no identified carbonate lithology; underlying carbonate is not established.')
        if geo['geo_class']=='unknown':contradictions.append('Lithology insufficiently resolved; no carbonate support assigned, no absence inferred.')
        if metric('hydrologic_edge_contamination','max') and metric('hydrologic_edge_contamination','max')>0:contradictions.append('Modeled catchment may receive flow across bounded DEM edge.')
        if old.get('talus_or_slide')=='1':contradictions.append('Original patch intersects mapped talus or slide material.')
        uncertainty=['100k geology; 50 m cartographic contact proxy is not positional accuracy.','Overhead DEM misses overhangs; glacial, talus, snow and survey artifacts remain.','Reference point is a feature representative, not an entrance or route.']
        if geo['geo_class']=='contact_uncertain':uncertainty.append('Only assumed 100 m contact context supports carbonate proximity; not mapped carbonate at the lead.')
        if metric('quality','min')!=1:uncertainty.append('Incomplete DEM/epoch QA coverage; preserved original lead.')
        alternatives={'cliff':'Glacial rock face, rockfall scar, talus margin, nonkarst cliff or interpolation artifact.', 'depression':'Glacial hollow, tarn, talus/breakdown, excavation or DEM artifact.', 'hydrology':'Ordinary surface drainage or glacial valley, not measured infiltration/discharge.', 'structure':'Mapped structural intersection may be sealed, inaccurate or unrelated to cave formation.'}[obj['kind']]
        data_availability={'terrain':q is not None,'geology':geo['geo_class']!='unknown','imagery':metric('ndvi') is not None,'pointcloud':(metric('pointcloud_ground_return_count','max') or 0)>0}
        confidence=sum(w*data_availability[k] for k,w in [('terrain',.4),('geology',.3),('imagery',.2),('pointcloud',.1)])
        detection=[m for m in obj['methods'] if m.startswith('terrain_') or m.endswith('_setting') or m=='mapped_structural_intersection']
        if not detection:detection=['baseline_'+obj['kind']]
        obj.update(candidate_id=obj['object_id'],area_m2=geom.GetArea(),longitude=longitude,latitude=latitude,**geo,
            methods='|'.join(sorted(obj['methods'])),detection_methods='|'.join(sorted(detection)),method_count=len(detection),
            score=score,evidence_strength=score,color_hex=color(score),terrain_component=terrain_component,hydrology_component=hydrology_component,
            geological_contribution=contributions['geology_structure'],terrain_family_contribution=contributions['terrain_hydrology_pointcloud'],
            data_confidence=confidence,has_terrain=int(data_availability['terrain']),has_imagery=int(data_availability['imagery']),has_pointcloud=int(data_availability['pointcloud']),
            fieldwork_status='Not yet investigated',access_status=old.get('access_screen','Not screened; no route verified'),
            field_note_link=area['baseline_area_id']+':'+obj['baseline_object_id'] if legacy else '',
            baseline_prediction_sha256=sha(safe_path(area['baseline_candidate_csv'])) if legacy else '',
            model_version=cfg['version'],independently_blind=0,
            mean_slope_deg=metric('slope'),baseline_min_residual_m=float(old['min_residual_m']) if old.get('min_residual_m') else None,
            robust_residual_q10_m=metric('residual_11m','q10'),fault_distance_m=dist['faults'],contact_distance_m=dist['contacts'],orientation_distance_m=dist['orientations'],
            orientation_context=nearest_orientation[0] if nearest_orientation else None,
            measurements=measurements,evidence_components=families,data_availability=data_availability,
            contradictory_evidence=contradictions,uncertainty=uncertainty,alternatives=alternatives,
            explanation=f"{obj['kind']} footprint ({geom.GetArea():.0f} m²); geology={geo['geo_class']}; terrain-family support={contributions['terrain_hydrology_pointcloud']}; geology contribution={contributions['geology_structure']}. Ordinal strength {score:.4f}; unvalidated, not a cave probability.",
            source_references=[str(v.relative_to(ROOT)) for v in gridpaths.values() if v.exists()]+geo['geology_sources'])
        retained.append((obj,geom));
        if n%250==0:print(area_id,'measured',n,'/',len(entries),flush=True)
    retained.sort(key=lambda item:(-item[0]['score'],item[0]['object_id']))
    for rank,(obj,geom) in enumerate(retained,1):obj['rank']=rank
    write_outputs(out,native,retained,area,cfg,georecords)
    compare(out,retained,len(rows),rejected,area_id)
    report={'area':area_id,'version':cfg['version'],'baseline_count':len(rows),'retained_baseline_count':sum(bool(r['baseline_object_id']) for r,g in retained),'candidate_count':len(retained),'config_sha256':sha(ROOT/'configs/enhanced_v001.json'),
        'inputs':fingerprint([safe_path(area['baseline_candidate_csv']),baseline/'features.gpkg',safe_path(area['baseline_processed'])/'context.gpkg']+[p for p in gridpaths.values() if p.exists()]),
        'outputs':fingerprint(list(out.glob('*'))),'geology_acquisition_report':f'docs/enhanced_v001/{area_id}_geology_acquisition.json',
        'known_cave_inputs_used':False,'independently_blind':False}
    write_json(out/'run_manifest.json',report);write_json(ROOT/f'docs/enhanced_v001/{area_id}_registry_manifest.json',report)
    return report


def write_outputs(out,ref,retained,area,cfg,georecords):
    rows=[r for r,g in retained];assert len({r['object_id'] for r in rows})==len(rows)
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'registry.gpkg'))
    sample=rows[0];integer={'rank','baseline_rank','method_count','has_terrain','has_imagery','has_pointcloud','independently_blind'}
    real={k for r in rows for k,v in r.items() if isinstance(v,float)}
    layers=[ds.CreateLayer('lead_points',ref.GetSpatialRef(),ogr.wkbPoint),ds.CreateLayer('lead_footprints',ref.GetSpatialRef(),ogr.wkbUnknown)]
    for layer in layers:
        for k in sample:layer.CreateField(ogr.FieldDefn(k,ogr.OFTInteger if k in integer else ogr.OFTReal if k in real else ogr.OFTString))
    serialized=[]
    for row,geom in retained:
        values={k:serial(v) if isinstance(v,(dict,list)) else v for k,v in row.items()};serialized.append(values)
        pt=ogr.Geometry(ogr.wkbPoint);pt.AddPoint_2D(row['easting'],row['northing'])
        for layer,geometry in zip(layers,[pt,geom]):
            f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(geometry)
            for k,v in values.items():
                if v is not None:f[k]=v
            layer.CreateFeature(f)
    ds=None
    with (out/'candidates.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(sample));writer.writeheader();writer.writerows(serialized)
    write_json(out/'candidate_evidence.json',rows)
    ds=ogr.Open(str(out/'geology.gpkg'),1);zones=ds.GetLayerByName('zones')
    for f in zones:
        members=[r for r in rows if r['zone_id']==f['zone_id']];f['candidate_count']=len(members)
        if members:f['max_strength']=max(r['score'] for r in members)
        zones.SetFeature(f)
    ds=None


def compare(out,retained,baseline_count,rejected,area_id):
    rows=[r for r,g in retained];legacy=[r for r in rows if r['baseline_object_id']]
    assert len(legacy)==baseline_count
    def rho(x,y):
        pairs=[(r.get(x),r.get(y)) for r in legacy if r.get(x) is not None and r.get(y) is not None]
        if len(pairs)<3:return None
        result=stats.spearmanr(np.array(pairs)[:,0],np.array(pairs)[:,1]).statistic
        return float(result) if np.isfinite(result) else None
    top=lambda key:[r['object_id'] for r in sorted(rows,key=lambda r:(-(r.get(key) if r.get(key) is not None else -1),r['object_id']))[:20]]
    comparison={'area':area_id,'baseline_count':baseline_count,'retained_baseline_count':len(legacy),'new_leads':len(rows)-len(legacy),'total':len(rows),
        'by_kind':dict(Counter(r['kind'] for r in rows)),'by_geology':dict(Counter(r['geo_class'] for r in rows)),
        'single_detection_method_count':sum(r['method_count']==1 for r in rows),'score_range':[min(r['score'] for r in rows),max(r['score'] for r in rows)],
        'scores_below_025_retained':sum(r['score']<.25 for r in rows),'new_noise_suppression':dict(rejected),
        'spearman_on_identical_baseline_objects':{'baseline_score_vs_slope':rho('baseline_score','mean_slope_deg'),'enhanced_score_vs_slope':rho('score','mean_slope_deg'),'baseline_min_residual_vs_q10':rho('baseline_min_residual_m','robust_residual_q10_m')},
        'comparison_top20':{'enhanced':top('score'),'geology_only':top('geology_component'),'simple_slope':top('mean_slope_deg')},
        'interpretation':'Descriptive usefulness/coverage comparison only; no known cave data, cave accuracy or independent validation. New leads are unverified surface/setting hypotheses.',
        'slope_audit':'Original exposure, landscape slope and cliff morphology all encode steepness. Enhanced cliff support uses robust residual quantiles plus a fixed weak cliff-detection floor; slope is retained as measurement/threshold, not a second amplitude bonus.'}
    write_json(out/'comparison.json',comparison);write_json(ROOT/f'docs/enhanced_v001/{area_id}_comparison.json',comparison)
