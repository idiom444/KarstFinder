#!/usr/bin/env python3
"""Keep geological priority separate from descriptive trail/ownership screening."""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import array, sha

gdal.UseExceptions(); ogr.UseExceptions()
cfg = json.loads((ROOT / 'configs/denny_v001_features.json').read_text())
ap=argparse.ArgumentParser();ap.add_argument('--output',default='results/denny_v001_access');ap.add_argument('--report',default='docs/experiments/denny_v001_access_summary.json');args=ap.parse_args()
raw = ROOT / 'data/raw/denny_v001'
features = ROOT / 'results/denny_v001_features'
out = ROOT / args.output
if out.exists():
    raise SystemExit(f'Refusing overwrite: {out}')
out.mkdir(parents=True)
a, b, c, d = cfg['study_bounds']; pad = cfg['buffer_m']
clip = ogr.CreateGeometryFromWkt(f'POLYGON(({a-pad} {b-pad},{c+pad} {b-pad},'
                                f'{c+pad} {d+pad},{a-pad} {d+pad},{a-pad} {b-pad}))')
gpkg = out / 'access.gpkg'
for name in ['trails', 'ownership']:
    src = ogr.Open(str(raw / f'usfs_{name}.geojson'))
    assert src.GetLayer(0).GetSpatialRef().GetAuthorityCode(None) == '26910'
    result = gdal.VectorTranslate(str(gpkg), src, format='GPKG', layerName=name,
                                  accessMode='update' if gpkg.exists() else None,
                                  geometryType='PROMOTE_TO_MULTI', clipDst=[a-pad,b-pad,c+pad,d+pad])
    result = None
context = ogr.Open(str(gpkg))
trails = [(f['trail_name'], f['trail_no'], f.GetGeometryRef().Clone())
          for f in context.GetLayerByName('trails')]
owners = [(f['ownerclassification'], f.GetGeometryRef().Clone())
          for f in context.GetLayerByName('ownership')]
bedrock_ds = ogr.Open(str(ROOT / cfg['processed_dir'] / 'context.gpkg'))
bedrock = bedrock_ds.GetLayerByName('bedrock')
bedrock.SetAttributeFilter("MAP_UNIT_100K='PMmb(e)'")
marble = ogr.Geometry(ogr.wkbMultiPolygon)
for f in bedrock:
    g = f.GetGeometryRef()
    if ogr.GT_Flatten(g.GetGeometryType()) == ogr.wkbPolygon:
        marble.AddGeometry(g)
    else:
        for part in g:
            marble.AddGeometry(part)
marble = marble.UnionCascaded()
src = ogr.Open(str(features / 'features.gpkg'))
polygons = {f['object_id']: f.GetGeometryRef().Clone()
            for f in src.GetLayerByName('surface_indicators')}
ref = gdal.Open(str(features / 'slope_1m.tif')); gt = ref.GetGeoTransform()
slope = array(features / 'slope_1m.tif')
rows = []
for f in src.GetLayerByName('ranked_indicators'):
    point = f.GetGeometryRef(); geom = polygons[f['object_id']]
    row = {key: f[key] for key in f.keys()}
    nearest = min(trails, key=lambda t: t[2].Distance(point))
    owner_names = sorted({name for name, g in owners if g.Intersects(point)})
    nonfs_area = sum(g.Intersection(geom).GetArea() for name, g in owners if name != 'USDA FOREST SERVICE')
    fs_area = sum(g.Intersection(geom).GetArea() for name, g in owners if name == 'USDA FOREST SERVICE')
    r = int((gt[3]-point.GetY())/-gt[5]); col = int((point.GetX()-gt[0])/gt[1])
    rr, cc = np.ogrid[max(0,r-25):min(slope.shape[0],r+26), max(0,col-25):min(slope.shape[1],col+26)]
    values = slope[max(0,r-25):min(slope.shape[0],r+26), max(0,col-25):min(slope.shape[1],col+26)]
    values = values[(rr-r)**2+(cc-col)**2 <= 25**2]
    distance = nearest[2].Distance(point)
    flags = []
    if distance > 50:
        flags.append('more than 50 m straight-line from mapped trail')
    if np.nanmax(values) >= 35:
        flags.append('35+ degree terrain within 25 m')
    if nonfs_area > .01 or owner_names != ['USDA FOREST SERVICE']:
        flags.append('non-FS or unresolved mapped ownership')
    if row['kind'] == 'cliff':
        flags.append('cliff feature; no direct approach suggested')
    if row['talus_or_slide']:
        flags.append('mapped talus/slide material')
    row.update(nearest_trail=f'{nearest[0]} #{nearest[1]}', trail_distance_m=distance,
               object_trail_gap_m=min(t[2].Distance(geom) for t in trails),
               ownership_at_point='; '.join(owner_names) or 'UNRESOLVED',
               object_nonfs_area_m2=nonfs_area, object_fs_fraction=min(1,fs_area/geom.GetArea()),
               mapped_marble_overlap_m2=geom.Intersection(marble).GetArea(),
               max_slope_within_25m_deg=float(np.nanmax(values)),
               fraction_35deg_within_25m=float(np.mean(values>=35)),
               access_screen='OFF-TRAIL / STEEP / UNRESOLVED' if flags else 'NEAR-TRAIL REVIEW ONLY',
               access_flags='; '.join(flags) or 'No coarse flags; route still unverified',
               route_verified=0, hiking_ready=0,
               access_note='Map screening only; straight-line distance is not a route. Ownership map is not a legal boundary/access determination. No cave or mine entry suggested.')
    rows.append((row, point.Clone()))
context = None
dest = ogr.Open(str(gpkg), 1)
layer = dest.CreateLayer('screened_indicators', ref.GetSpatialRef(), ogr.wkbPoint)
integer = {'rank', 'rank_within_kind', 'contact_only', 'talus_or_slide', 'boundary_clipped', 'route_verified', 'hiking_ready'}
for key, value in rows[0][0].items() if rows else []:
    typ = ogr.OFTInteger if key in integer else ogr.OFTReal if isinstance(value,(int,float)) else ogr.OFTString
    layer.CreateField(ogr.FieldDefn(key, typ))
for row, point in rows:
    f = ogr.Feature(layer.GetLayerDefn()); f.SetGeometry(point)
    for key, value in row.items():
        f[key] = value
    layer.CreateFeature(f)
dest = None
if rows:
    with (out / 'screened_indicators.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0][0])); writer.writeheader()
        writer.writerows(r for r, _ in rows)
summary = dict(surface_objects=len(rows), route_verified_count=0, hiking_ready_count=0,
               screening_counts=dict(Counter(r['access_screen'] for r, _ in rows)),
               ownership_at_points=dict(Counter(r['ownership_at_point'] for r, _ in rows)),
               minimum_point_trail_distance_m=min((r['trail_distance_m'] for r, _ in rows), default=None),
               direct_mapped_marble_objects=sum(r['mapped_marble_overlap_m2']>0 for r, _ in rows),
               scientific_ranks_changed=False,
               interpretation='Access flags are descriptive, not safe/legal route certification. No off-trail route generated.')
(out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
manifest = dict(inputs={str(p.relative_to(ROOT)):sha(p) for p in [features/'features.gpkg',features/'slope_1m.tif',raw/'usfs_trails.geojson',raw/'usfs_ownership.geojson']},
                outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()})
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(ROOT / args.report).write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2))
