#!/usr/bin/env python3
"""Independent pixel/geometry/rank audit and repeat comparison; no cave data."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
import numpy as np
from osgeo import gdal, ogr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import array,sha

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('area',choices=['kaleetan','marble'])
    args=parser.parse_args();area=args.area+'_v001'
    out=ROOT/f'docs/reviews/{area}_methodology'
    if out.exists():raise RuntimeError(f'Refusing review overwrite: {out}')
    out.mkdir(parents=True)
    preserve={'landscape_candidates.csv':f'results/{area}_landscape/candidates.csv',
        'ranked_indicators.csv':f'results/{area}_features/ranked_indicators.csv',
        'screened_indicators.csv':f'results/{area}_access/screened_indicators.csv',
        'landscape_config.json':f'configs/{area}_landscape.json',
        'feature_config.json':f'configs/{area}_features.json'}
    for name,source in preserve.items():shutil.copyfile(ROOT/source,out/name)
    cfg=json.loads((out/'feature_config.json').read_text())
    feature=ROOT/f'results/{area}_features'
    rasters={name:array(feature/f'{name}.tif') for name in
             ['geological_evidence_1m','slope_1m','residual_11m','depression_depth_1m','feature_quality_1m','source_epoch_1m']}
    terrain=np.repeat(np.repeat(array(ROOT/f'results/{area}_landscape/terrain_score.tif'),10,axis=0),10,axis=1)
    ref=gdal.Open(str(feature/'slope_1m.tif'));gt=ref.GetGeoTransform()
    source=ogr.Open(str(feature/'features.gpkg'))
    polygons={f['object_id']:f.GetGeometryRef().Clone() for f in source.GetLayerByName('surface_indicators')}
    rows=list(csv.DictReader((out/'ranked_indicators.csv').open()))
    access=list(csv.DictReader((out/'screened_indicators.csv').open()))
    assert [(r['object_id'],r['rank']) for r in rows]==[(r['object_id'],r['rank']) for r in access]
    audited=[];max_error=0.
    for row in rows:
        geom=polygons[row['object_id']];xmin,xmax,ymin,ymax=geom.GetEnvelope()
        col=int(round((xmin-gt[0])/gt[1]));r=int(round((gt[3]-ymax)/-gt[5]))
        width=int(round((xmax-xmin)/gt[1]));height=int(round((ymax-ymin)/-gt[5]))
        mask=gdal.GetDriverByName('MEM').Create('',width,height,1,gdal.GDT_Byte)
        mask.SetProjection(ref.GetProjection());mask.SetGeoTransform((xmin,gt[1],0,ymax,0,gt[5]))
        vector=ogr.GetDriverByName('MEM').CreateDataSource('')
        layer=vector.CreateLayer('object',ref.GetSpatialRef(),ogr.wkbPolygon)
        f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(geom);layer.CreateFeature(f)
        gdal.RasterizeLayer(mask,[1],layer,burn_values=[1]);valid=mask.ReadAsArray().astype(bool)
        sl=np.s_[r:r+height,col:col+width]
        g=float(rasters['geological_evidence_1m'][sl][valid].mean())
        t=float(terrain[sl][valid].mean())
        slope=float(rasters['slope_1m'][sl][valid].mean())
        residual=float(rasters['residual_11m'][sl][valid].min())
        depth=float(rasters['depression_depth_1m'][sl][valid].max())
        f_score=min(1,depth/3) if row['kind']=='depression' else .5*np.clip((slope-45)/30,0,1)+.5*np.clip(-residual/2,0,1)
        weights=cfg['feature_weights']
        contribution=[weights['geology']*g,weights['landscape']*t,weights['morphology']*f_score]
        score=sum(contribution)
        measured={'area_m2':float(valid.sum()),'geo_score':g,'terrain_score':t,
                  'mean_slope_deg':slope,'min_residual_m':residual,'max_depth_m':depth,
                  'morphology_score':float(f_score),'score':float(score),
                  'carbonate_fraction':float((rasters['geological_evidence_1m'][sl][valid]>0).mean()),
                  'fraction_2021':float((rasters['source_epoch_1m'][sl][valid]==2021).mean())}
        errors=[abs(value-float(row[key])) for key,value in measured.items()]
        max_error=max(max_error,*errors)
        assert max(errors)<1e-6,(row['object_id'],measured)
        assert (rasters['feature_quality_1m'][sl][valid]==1).all(),row['object_id']
        audited.append({'object_id':row['object_id'],'rank':int(row['rank']),'kind':row['kind'],
                        'rank_within_kind':int(row['rank_within_kind']),
                        'geology_contribution':contribution[0],'terrain_contribution':contribution[1],
                        'morphology_contribution':contribution[2],'recomputed_score':float(score),
                        'stored_score':float(row['score']),'maximum_measurement_difference':max(errors)})
    assert [int(r['rank']) for r in rows]==list(range(1,len(rows)+1))
    expected=sorted(rows,key=lambda r:(-float(r['score']),-float(r['morphology_score']),r['kind'],float(r['easting']),float(r['northing'])))
    assert [r['object_id'] for r in rows]==[r['object_id'] for r in expected]
    for kind in ['cliff','depression']:
        assert [int(r['rank_within_kind']) for r in rows if r['kind']==kind]==list(range(1,sum(r['kind']==kind for r in rows)+1))
    with (out/'score_audit.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(audited[0]));writer.writeheader();writer.writerows(audited)

    marble=[r for r in access if float(r['mapped_marble_overlap_m2'])>0]
    assert [{k:r[k] for k in rows[0]} for r in access]==rows
    for row in rows:
        point=ogr.Geometry(ogr.wkbPoint);point.AddPoint_2D(float(row['easting']),float(row['northing']))
        assert polygons[row['object_id']].Contains(point),row['object_id']
    repeat={'rasters':0,'csvs':0,'geopackage_layers':0}
    for kind in ['landscape','features']:
        first=ROOT/f'results/{area}_{kind}';second=ROOT/f'results/{area}_{kind}_repeat'
        for path in first.glob('*.tif'):
            a,b=gdal.Open(str(path)),gdal.Open(str(second/path.name))
            assert a.GetGeoTransform()==b.GetGeoTransform(),path
            assert a.GetProjection()==b.GetProjection(),path
            np.testing.assert_array_equal(a.ReadAsArray(),b.ReadAsArray(),err_msg=str(path))
            repeat['rasters']+=1
        for path in first.glob('*.csv'):
            assert path.read_bytes()==(second/path.name).read_bytes(),path
            repeat['csvs']+=1
        for path in first.glob('*.gpkg'):
            a,b=ogr.Open(str(path)),ogr.Open(str(second/path.name))
            for layer in a:
                other=b.GetLayerByName(layer.GetName())
                records=lambda lyr: sorted((json.dumps(f.items(),sort_keys=True),bytes(f.GetGeometryRef().ExportToWkb())) for f in lyr)
                assert records(layer)==records(other),(path,layer.GetName())
                repeat['geopackage_layers']+=1
    report={'area':area,'ranked_objects':len(rows),'cliffs':sum(r['kind']=='cliff' for r in rows),
        'depressions':sum(r['kind']=='depression' for r in rows),'mapped_marble_overlap_objects':len(marble),
        'mapped_marble_overlap_depressions':sum(r['kind']=='depression' for r in marble),
        'maximum_measurement_difference':max_error,'deterministic_ranking_verified':True,
        'all_representative_points_inside_original_patches':True,'all_ranked_objects_quality_eligible':True,
        'access_screen_preserves_all_original_candidate_fields':True,'repeat_comparison':repeat,
        'audited_measurement_fields':list(measured),'cave_reference_data_read':False,
        'meaning':'Arithmetic and reproducibility checks; not validation of cave-prediction skill.'}
    (out/'audit_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    table=['# Direct mapped-marble indicator evidence','',
        'These are surface patches, not detected openings. Original ranks remain unchanged. Full precision is in the CSVs.','',
        '| ID | Kind | Global rank | Kind rank | Area m² | Overlap m² | Slope ° | G | T | F | Score |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in marble:
        table.append(f"| {row['object_id']} | {row['kind']} | {row['rank']} | {row['rank_within_kind']} | {float(row['area_m2']):.0f} | {float(row['mapped_marble_overlap_m2']):.2f} | {float(row['mean_slope_deg']):.3f} | {float(row['geo_score']):.6f} | {float(row['terrain_score']):.6f} | {float(row['morphology_score']):.6f} | {float(row['score']):.6f} |")
    (out/'direct_marble_evidence.md').write_text('\n'.join(table)+'\n')
    manifest={'preserved_sources_sha256':{source:sha(ROOT/source) for source in preserve.values()},
        'review_files_sha256':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
    (out/'review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    gdal.UseExceptions();ogr.UseExceptions();main()
