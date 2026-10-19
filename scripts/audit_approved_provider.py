#!/usr/bin/env python3
"""Audit a provider-side context container change without altering its records."""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from osgeo import gdal, ogr, osr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from karstfinder.gis import sha
from karstfinder.freeze import verify_freeze

def main():
    snapshot_path=ROOT/'experiments/snapshots/marble_v001.json'
    original=json.loads(snapshot_path.read_text())
    changed=[name for name,digest in original['sha256'].items() if sha(ROOT/name)!=digest]
    expected='data/processed/marble_v001/context.gpkg'
    assert changed==[expected],changed
    cfg=json.loads((ROOT/'configs/marble_v001_landscape.json').read_text())
    out=ROOT/'data/processed/marble_v001_context_provider_audit'
    if out.exists():raise RuntimeError(f'Refusing audit overwrite: {out}')
    out.mkdir()
    a,b,c,d=cfg['study_bounds'];pad=cfg['buffer_m'];bounds=[a-pad,b-pad,c+pad,d+pad]
    srs = osr.SpatialReference(); srs.ImportFromEPSG(26910)
    gpkg = out / 'context.gpkg'
    for ident, name, geometry in [(11, 'bedrock', ogr.wkbMultiPolygon), (7, 'faults', ogr.wkbMultiLineString),
                                   (9, 'contacts', ogr.wkbMultiLineString), (1, 'orientations', ogr.wkbMultiPoint)]:
        path = ROOT / cfg['raw_dir'] / f'dnr_{ident}.geojson'
        value = json.loads(path.read_text())
        if value['features']:
            source = ogr.Open(str(path))
            result = gdal.VectorTranslate(str(gpkg), source, format='GPKG', layerName=name,
                                          accessMode='update' if gpkg.exists() else None,
                                          geometryType='PROMOTE_TO_MULTI', srcSRS=cfg['crs'], dstSRS=cfg['crs'], clipDst=bounds)
            result = None; source = None
        else:
            dest = ogr.Open(str(gpkg), 1)
            dest.CreateLayer(name, srs, geometry); dest = None
    dest = ogr.Open(str(gpkg), 1); layer = dest.GetLayerByName('bedrock')
    layer.CreateField(ogr.FieldDefn('geo_score', ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn('evidence', ogr.OFTString))
    for feature in layer:
        unit = feature['MAP_UNIT_100K']; feature['geo_score'] = cfg['geology_scores'].get(unit, 0)
        feature['evidence'] = ('mapped marble; 1:100k contact uncertainty' if unit in cfg['marble_units'] else
                               'mixed melange may contain unmapped marble' if unit == 'JTRmt(e)' else
                               'no mapped carbonate evidence; not proof of absence')
        layer.SetFeature(feature)
    study = dest.CreateLayer('study_area', srs, ogr.wkbPolygon)
    study.CreateField(ogr.FieldDefn('name', ogr.OFTString))
    feature = ogr.Feature(study.GetLayerDefn()); feature['name'] = cfg['area_name'] + ' | approved 9 km2 | unvalidated'
    feature.SetGeometry(ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))'))
    study.CreateFeature(feature); dest = None

    # Compare all vector schemas, attributes and exact geometries to a fresh
    # reconstruction from the retained raw DNR files with the same GDAL code.
    current=ogr.Open(str(ROOT/expected));repeat=ogr.Open(str(out/'context.gpkg'))
    comparisons={}
    for layer in current:
        other=repeat.GetLayerByName(layer.GetName())
        assert [(f.GetName(),f.GetType()) for f in layer.schema]==[(f.GetName(),f.GetType()) for f in other.schema]
        records=lambda lyr:sorted((json.dumps(f.items(),sort_keys=True),bytes(f.GetGeometryRef().ExportToWkb())) for f in lyr)
        first,second=records(layer),records(other)
        assert first==second,layer.GetName()
        comparisons[layer.GetName()]={'features':len(first),'all_attributes_and_geometry_match_raw_source_reconstruction':True}
    current=None;repeat=None
    # Lock the prepared context as well as the already-protected results before
    # any further provider opening. Never alter its data to force an old hash.
    (ROOT/expected).chmod(0o444)
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'initial_snapshot':str(snapshot_path.relative_to(ROOT)),
        'initial_context_sha256':original['sha256'][expected],'post_provider_context_sha256':sha(ROOT/expected),
        'only_changed_initial_snapshot_file':expected,'unchanged_other_snapshot_entries':len(original['sha256'])-1,
        'comparisons':comparisons,'scores_ranks_raster_arrays_or_csvs_changed':False,
        'cave_reference_data_read':False,'explanation':'Context container bytes changed during QGIS provider review. Every layer schema, attribute and geometry matches a fresh reconstruction from the original raw geology/configuration. All other original snapshot hashes still match. The initial snapshot is retained as pre-review evidence; a distinct reviewed snapshot pins the final container. Exact original changed byte fields are not asserted because a byte copy of the earlier container was not retained.'}
    report_path=ROOT/'docs/experiments/marble_v001_provider_review.json'
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    # Preserve the original record; this is an additive finalization record.
    final={**original,'snapshot_id':'marble_v001_reviewed','status':'final_unvalidated_prospecting_snapshot_after_provider_review',
        'supersedes_for_current_context_container':str(snapshot_path.relative_to(ROOT)),
        'provider_review':str(report_path.relative_to(ROOT)),
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'sha256':{name:sha(ROOT/name) for name in original['sha256']}}
    final['sha256'][str(snapshot_path.relative_to(ROOT))]=sha(snapshot_path)
    final['sha256'][str(report_path.relative_to(ROOT))]=sha(report_path)
    final['sha256']['scripts/audit_approved_provider.py']=sha(Path(__file__))
    final_path=ROOT/'experiments/snapshots/marble_v001_reviewed.json'
    assert not final_path.exists()
    final_path.write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    gdal.UseExceptions();ogr.UseExceptions();osr.UseExceptions();main()
