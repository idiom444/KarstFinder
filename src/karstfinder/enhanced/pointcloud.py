"""Optional bounded LAS workflow. Normals/curvature are geometry, never openings."""
import json,subprocess
from pathlib import Path
from .common import ROOT,write_json,sha


def run_pipeline(path,stages):
    write_json(path,{'pipeline':stages})
    run=subprocess.run(['pdal','pipeline',str(path)],capture_output=True,text=True,timeout=600)
    path.with_suffix('.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('PDAL failed; inspect '+str(path.with_suffix('.log')))


def process(source,out,bounds,knn=16,resolution=2,ground_classes=(2,)):
    """Require LAS header CRS, convert vertical units explicitly, then crop.

    Horizontal reprojection is deliberately 2D; vertical datum stays NAVD88.
    Unknown vertical units are rejected rather than inferred from XY.
    """
    info=json.loads(subprocess.check_output(['pdal','info','--summary',str(source)],text=True))
    write_json(out/'source_header.json',info)
    srs=info['summary']['metadata']['srs'];units=srs['units']['vertical']
    if units=='US survey foot':factor=1200/3937
    elif units in ('metre','meter','metres','meters'):factor=1.
    else:raise ValueError('Unsupported or missing explicit vertical units: '+units)
    if 'NAVD88' not in srs.get('vertical',''):raise ValueError('Unsupported vertical datum; no silent vertical conversion')
    a,b,c,d=bounds;crop=out/'ground_crop.laz'
    common=[{'type':'readers.las','filename':str(source)},
        {'type':'filters.reprojection','in_srs':srs['wkt'],'out_srs':'EPSG:26910'},
        {'type':'filters.assign','value':f'Z = Z * {factor:.17g}'},
        {'type':'filters.crop','bounds':f'([{a},{c}],[{b},{d}])'}]
    run_pipeline(out/'crop_pipeline.json',common+[
        {'type':'writers.gdal','filename':str(out/'all_return_count.tif'),'resolution':resolution,'dimension':'Z','output_type':'count','binmode':True,'origin_x':a,'origin_y':b,'width':int((c-a)/resolution),'height':int((d-b)/resolution),'nodata':-9999,'allow_empty':True},
        {'type':'filters.expression','expression':'('+' || '.join(f'Classification == {int(cls)}' for cls in ground_classes)+') && Withheld == 0'},
        {'type':'writers.las','filename':str(crop),'a_srs':'EPSG:26910+5703','extra_dims':'all'}])
    header=json.loads(subprocess.check_output(['pdal','info','--summary',str(crop)],text=True))
    count=header['summary']['num_points'] if 'num_points' in header['summary'] else header['summary']['metadata']['count']
    if count<16:raise ValueError('Too few classified ground returns for stable neighborhoods')
    stages=[{'type':'readers.las','filename':str(crop)}, {'type':'filters.normal','knn':knn}]
    for name,dimension,kind in [('ground_return_count','Z','count'),('ground_z_stdev','Z','stdev'),('normal_z','NormalZ','mean'),('surface_curvature','Curvature','mean')]:
        stages.append({'type':'writers.gdal','filename':str(out/(name+'.tif')),'dimension':dimension,'resolution':resolution,'output_type':kind,'binmode':True,'origin_x':a,'origin_y':b,'width':int((c-a)/resolution),'height':int((d-b)/resolution),'nodata':-9999,'allow_empty':True})
    stages.append({'type':'writers.las','filename':str(out/'ground_normals.laz'),'a_srs':'EPSG:26910+5703','extra_dims':'all'})
    run_pipeline(out/'normals_pipeline.json',stages)
    return {'ground_points':count,'vertical_source_units':units,'vertical_conversion_to_m':factor,
        'vertical_datum':'NAVD88 retained, no fitted datum offset','bounds_utm':bounds,
        'products':{str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.suffix in ('.tif','.laz','.json')},
        'limitations':['Only a partial 500 m geology-centered window is sampled; blank cells mean absent coverage, not openings.',
        'Classified ground only. Vertical/overhanging surfaces may be absent or misclassified.',
        'KNN normals and covariance curvature mix scan geometry, sampling and real surface shape; experimental context only.',
        'Z standard deviation in 2 m bins includes slope and is not detrended rock-face roughness.',
        'Normals near crop boundary have truncated neighborhoods; no point-cloud score bonus is assigned.',
        'Recess/entrance recognition is not implemented or claimed. DEM fallback remains active.']}
