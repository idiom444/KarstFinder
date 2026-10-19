#!/usr/bin/env python3
"""Independent surface indicators, a combined ranking, and blind sensitivity checks."""
import argparse,csv,gc,json,sys,subprocess
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.cluster.vq import kmeans2,vq
from osgeo import gdal,ogr,osr
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,raster,sha,memory,CO

gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions()


def geology(ref,context):
    ds=ogr.Open(str(context));layer=ds.GetLayerByName('bedrock')
    codes=np.zeros((ref.RasterYSize,ref.RasterXSize),dtype='uint8')
    dest=memory(codes,ref)
    for code,unit in [(3,'JTRmt(e)'),(4,'wtr'),(5,'Qta'),(6,'Qls'),(1,'PMmb(e)')]:
        layer.SetAttributeFilter(f"MAP_UNIT_100K = '{unit}'");gdal.RasterizeLayer(dest,[1],layer,burn_values=[code])
    layer.SetAttributeFilter(None)
    codes=dest.ReadAsArray();distance=ndimage.distance_transform_edt(codes!=1).astype('float32')
    return codes,distance


def objects(binary,minarea,maxarea):
    labels,n=ndimage.label(binary)  # Explicit four-neighbour connectivity.
    counts=np.bincount(labels.ravel());keep=(counts>=minarea)&(counts<=maxarea);keep[0]=False
    ids=np.flatnonzero(keep)
    return labels,ids,counts


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default='configs/blind_v002.json');ap.add_argument('--output',default='results/blind_v002');args=ap.parse_args()
    cfgpath=ROOT/args.config;cfg=json.loads(cfgpath.read_text());out=ROOT/args.output
    if out.exists():raise SystemExit(f'Refusing overwrite: {out}')
    out.mkdir(parents=True);(out/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    pre=ROOT/cfg.get('feature_processed_dir','data/processed/features_v002');base=ROOT/cfg['landscape_run']
    processed=ROOT/cfg.get('processed_dir','data/processed')
    qa=json.loads((pre/'qa.json').read_text());assert qa['native_buffered_missing_pixels']==0
    derives=json.loads((pre/'derivatives_manifest.json').read_text())
    for file,digest in derives['products'].items():assert sha(pre/file)==digest,file
    assert derives['source_sha256']==sha(processed/'dem_1m_buffered.tif')
    a,b,c,d=cfg['study_bounds'];pad=cfg['buffer_m'];win=[a,d,c,b]
    ref=gdal.Translate('',str(processed/'dem_1m_buffered.tif'),format='MEM',projWin=win)
    shape=(ref.RasterYSize,ref.RasterXSize)
    for name,source in [('depression_depth_1m',pre/'depression_depth_1m_buffered.tif'),('slope_1m',pre/'slope_1m_buffered.tif'),
                         ('residual_11m',pre/'residual_11m_buffered.tif'),('feature_quality_1m',pre/'feature_quality_1m_buffered.tif'),
                         ('source_epoch_1m',pre/'source_epoch_1m_buffered.tif'),('hillshade_1m',pre/'hillshade_1m_buffered.tif')]:
        gdal.Translate(str(out/f'{name}.tif'),str(source),projWin=win,creationOptions=CO)
    depth=array(out/'depression_depth_1m.tif');slope=array(out/'slope_1m.tif');residual=array(out/'residual_11m.tif')
    quality=array(out/'feature_quality_1m.tif')==1;epoch=array(out/'source_epoch_1m.tif')
    codes,marble_dist=geology(ref,processed/'context.gpkg')
    geo=np.where(codes==3,cfg['geology_scores']['mixed_melange'],0).astype('float32')
    geo=np.where(marble_dist<=cfg['contact_buffer_primary_m'],cfg['geology_scores']['marble_contact_buffer'],geo)
    geo[codes==1]=1.;geo[codes==4]=0.  # Exclude mapped open water from entrance-feature targets.
    raster(out/'geological_evidence_1m.tif',geo,ref)
    raster(out/'marble_distance_1m.tif',marble_dist,ref)
    terrain10=array(base/'terrain_score.tif');terrain=np.repeat(np.repeat(terrain10,10,axis=0),10,axis=1)
    assert terrain.shape==shape
    # Preserve small-feature components without splitting at geology or QA boundaries.
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(out/'features.gpkg'))
    polygon=ds.CreateLayer('surface_indicators',ref.GetSpatialRef(),ogr.wkbPolygon)
    point=ds.CreateLayer('ranked_indicators',ref.GetSpatialRef(),ogr.wkbPoint)
    fields={'object_id':ogr.OFTString,'rank':ogr.OFTInteger,'kind':ogr.OFTString,'area_m2':ogr.OFTReal,
       'score':ogr.OFTReal,'geo_score':ogr.OFTReal,'terrain_score':ogr.OFTReal,'morphology_score':ogr.OFTReal,
       'carbonate_fraction':ogr.OFTReal,'rank_within_kind':ogr.OFTInteger,'max_depth_m':ogr.OFTReal,'mean_slope_deg':ogr.OFTReal,'min_residual_m':ogr.OFTReal,'distance_marble_m':ogr.OFTReal,
       'fraction_2021':ogr.OFTReal,'contact_only':ogr.OFTInteger,'talus_or_slide':ogr.OFTInteger,'boundary_clipped':ogr.OFTInteger,
       'easting':ogr.OFTReal,'northing':ogr.OFTReal,'longitude':ogr.OFTReal,'latitude':ogr.OFTReal,
       'evidence':ogr.OFTString,'alternatives':ogr.OFTString,'uncertainty':ogr.OFTString,'status':ogr.OFTString}
    for layer in [polygon,point]:
        for name,typ in fields.items():layer.CreateField(ogr.FieldDefn(name,typ))
    wgs=osr.SpatialReference();wgs.ImportFromEPSG(4326);wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    tx=osr.CoordinateTransformation(ref.GetSpatialRef(),wgs);rows=[];feature_strength=np.zeros(shape,dtype='float32');counts_report={}
    for kind,binary,minarea,maxarea in [('depression',depth>=cfg['depression_depth_m'],cfg['depression_min_area_m2'],cfg['depression_max_area_m2']),
      ('cliff',slope>=cfg['cliff_slope_degrees'],cfg['cliff_min_area_m2'],cfg['cliff_max_area_m2'])]:
        labels,ids,counts=objects(binary,minarea,maxarea)
        slices=ndimage.find_objects(labels);retained=[]
        for ident in ids:
            sl=slices[ident-1];mask=labels[sl]==ident
            if not quality[sl][mask].all():continue
            if not (geo[sl][mask]>0).any():continue
            if (codes[sl][mask]==4).any():continue
            retained.append(ident)
        keep=np.isin(labels,retained);labels[~keep]=0
        # Polygonize integer component IDs in one GIS operation, then evaluate local bounding boxes.
        mem=memory(labels,ref,gdal.GDT_Int32);polyds=ogr.GetDriverByName('MEM').CreateDataSource('')
        layer=polyds.CreateLayer('components',ref.GetSpatialRef(),ogr.wkbPolygon);layer.CreateField(ogr.FieldDefn('component',ogr.OFTInteger))
        gdal.Polygonize(mem.GetRasterBand(1),mem.GetRasterBand(1),layer,0,[])
        for f in layer:
            ident=f['component'];sl=slices[ident-1];mask=labels[sl]==ident;geom=f.GetGeometryRef().Clone();n=int(mask.sum())
            g=float(geo[sl][mask].mean());t=float(np.mean(terrain[sl][mask]));maxdepth=float(depth[sl][mask].max())
            meanslope=float(np.mean(slope[sl][mask]));minres=float(residual[sl][mask].min())
            morphology=float(min(1,maxdepth/3)) if kind=='depression' else float(.5*np.clip((meanslope-45)/30,0,1)+.5*np.clip(-minres/2,0,1))
            # Geology, landscape and morphology remain individually inspectable.
            weights=cfg['feature_weights'];score=weights['geology']*g+weights['landscape']*t+weights['morphology']*morphology
            clipped=sl[0].start==0 or sl[0].stop==shape[0] or sl[1].start==0 or sl[1].stop==shape[1]
            # Representative point must lie in the geologically supported part of the object.
            supported=mask&(geo[sl]>0)
            local_prior=np.where(supported,.4*geo[sl]+.3*terrain[sl],-1.)
            rr,cc=np.unravel_index(np.argmax(local_prior),local_prior.shape)
            gt=ref.GetGeoTransform();x=gt[0]+sl[1].start+cc+.5;y=gt[3]-sl[0].start-rr-.5
            pt=ogr.Geometry(ogr.wkbPoint);pt.AddPoint_2D(x,y);lon,lat,_=tx.TransformPoint(x,y)
            row={'object_id':f'{kind[:1].upper()}-{ident:06d}','kind':kind,'area_m2':float(n),'score':score,'geo_score':g,'terrain_score':t,
               'morphology_score':morphology,'carbonate_fraction':float((geo[sl][mask]>0).mean()),'max_depth_m':maxdepth,'mean_slope_deg':meanslope,'min_residual_m':minres,
               'distance_marble_m':float(marble_dist[sl][mask].min()),'fraction_2021':float((epoch[sl][mask]==2021).mean()),
               'contact_only':int(not (codes[sl][mask]==1).any() and (marble_dist[sl][mask]<=100).any()),
               'talus_or_slide':int(np.isin(codes[sl][mask],[5,6]).any()),'boundary_clipped':int(clipped),
               'easting':x,'northing':y,'longitude':lon,'latitude':lat,
               'evidence':'Closed topographic depression' if kind=='depression' else 'Steep surface exposure with local residual context',
               'alternatives':'Glacial hollow or tarn; talus/breakdown; vegetation/DEM artifact; excavation' if kind=='depression' else 'Glacial rock face; landslide scar; talus edge; nonkarst cliff',
               'uncertainty':'No mapped opening; 1:100k contacts; airborne overhead occlusion; survey/interpolation artifacts remain',
               'status':'Unverified surface indicator; NOT a confirmed cave or detected entrance'}
            if row['contact_only']:row['uncertainty']+='; carbonate inferred only within assumed 100 m contact buffer'
            if clipped:row['uncertainty']+='; component truncated at study boundary'
            if row['talus_or_slide']:row['uncertainty']+='; intersects mapped talus or landslide material'
            rows.append((row,geom,pt.Clone()))
            tile=feature_strength[sl];tile[mask]=np.maximum(tile[mask],morphology)
        counts_report[kind]={'size_eligible_components':int(len(ids)),'ranked_quality_and_geology_components':len(retained)}
        print(kind,counts_report[kind],flush=True)
        del labels,mem,polyds,keep,slices;gc.collect()
    rows.sort(key=lambda x:(-x[0]['score'],-x[0]['morphology_score'],x[0]['kind'],x[0]['easting'],x[0]['northing']))
    kind_ranks={}
    for rank,(row,geom,pt) in enumerate(rows,1):
        row['rank']=rank
        kind_ranks[row['kind']]=kind_ranks.get(row['kind'],0)+1;row['rank_within_kind']=kind_ranks[row['kind']]
        for layer,geometry in [(polygon,geom),(point,pt)]:
            f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(geometry)
            for k,v in row.items():f[k]=v
            layer.CreateFeature(f)
    ds=None
    with (out/'ranked_indicators.csv').open('w') as f:
        wr=csv.DictWriter(f,fieldnames=list(fields));wr.writeheader();wr.writerows(r for r,_,_ in rows)
    raster(out/'feature_morphology_1m.tif',feature_strength,ref)
    # Area-normalized comparison grid: scores represent 10 m cells, not point-localization probabilities.
    ref10=gdal.Open(str(base/'combined_score.tif'))
    geo10=geo.reshape(shape[0]//10,10,shape[1]//10,10).max(axis=(1,3))
    feat10=feature_strength.reshape(shape[0]//10,10,shape[1]//10,10).max(axis=(1,3))
    weights=cfg['feature_weights'];combined=np.where(geo10>0,weights['geology']*geo10+weights['landscape']*terrain10+weights['morphology']*feat10,0)
    for name,arr in [('combined_score_10m',combined),('feature_score_10m',feat10),('geology_score_10m',geo10)]:raster(out/f'{name}.tif',arr,ref10)
    # Seeded terrain clustering is descriptive only; no cluster is assigned a cave label.
    names=['slope','dev_210m','dev_610m','dev_2010m'];stack=np.stack([array(base/f'{n}.tif') for n in names],axis=-1)
    data=stack.reshape(-1,4);valid=np.isfinite(data).all(axis=1);mean=data[valid].mean(axis=0);sd=data[valid].std(axis=0);scaled=(data[valid]-mean)/sd
    rng=np.random.default_rng(cfg['clustering']['seed']);train=scaled[rng.choice(len(scaled),min(cfg['clustering']['sample_size'],len(scaled)),replace=False)]
    centers,_=kmeans2(train,cfg['clustering']['k'],iter=50,minit='++',rng=rng,missing='raise');classes,dist=vq(scaled,centers)
    clusters=np.full(len(data),-9999,dtype='float32');clusters[valid]=classes+1;raster(out/'terrain_clusters_10m.tif',clusters.reshape(terrain10.shape),ref10)
    cluster_info={'features':names,'mean':mean.tolist(),'sd':sd.tolist(),'centers_original_units':(centers*sd+mean).tolist(),
       'cluster_cells':np.bincount(classes,minlength=len(centers)).tolist(),'seed':cfg['clustering']['seed'],'interpretation':'Descriptive terrain classes only; no cave association inferred'}
    (out/'clustering.json').write_text(json.dumps(cluster_info,indent=2)+'\n')
    # Predeclared threshold and contact uncertainty sensitivity, never selected against cave labels.
    sensitivity=[]
    for thresh in cfg['depression_depth_sensitivity_m']:
        lab,ids,counts=objects(depth>=thresh,cfg['depression_min_area_m2'],cfg['depression_max_area_m2']);slcs=ndimage.find_objects(lab)
        for buf in cfg['contact_buffer_sensitivity_m']:
            n=0;area=0
            for ident in ids:
                sl=slcs[ident-1];mask=lab[sl]==ident
                if not quality[sl][mask].all() or (codes[sl][mask]==4).any():continue
                if not ((marble_dist[sl][mask]<=buf)|(codes[sl][mask]==3)).any():continue
                n+=1;area+=int(counts[ident])
            sensitivity.append({'min_depth_m':thresh,'marble_buffer_m':buf,'objects':n,'area_m2':area})
        del lab,slcs;gc.collect()
    (out/'sensitivity.json').write_text(json.dumps(sensitivity,indent=2)+'\n')
    summary={'experiment_id':cfg['experiment_id'],'stage':cfg.get('stage','blind_unfrozen'),'known_cave_sources_accessed':False,'study_area_km2':(c-a)*(d-b)/1e6,
       'surface_indicators':len(rows),'by_kind':counts_report,'native_qa':qa,'geological_context_area_km2':float((geo>0).sum()/1e6),
       'primary_feature_area_km2':float((feature_strength>0).sum()/1e6),'entrances_confirmed':0,'entrance_detector_claimed':False,
       'interpretation':'Complementary surface indicators and landscape ranking, not probabilities or confirmed openings'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    inputs=[cfgpath]+list(pre.glob('*'))+[processed/'context.gpkg']+list(base.glob('*.tif'))
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'frozen':False,'inputs':{str(p.relative_to(ROOT)):sha(p) for p in inputs if p.is_file()},
      'code':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'scripts').glob('*.py'))+sorted((ROOT/'src').rglob('*.py'))},
      'outputs':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
