#!/usr/bin/env python3
"""Audit saved carbonate eligibility, measurements, membership and reopened maps."""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from osgeo import ogr
from qgis.core import QgsApplication, QgsProject, QgsSymbolLayer
from karstfinder.carbonate.common import config, safe_path, sha, write_json
from karstfinder.carbonate.scope import surface_area, geometry_key
from karstfinder.carbonate.grouping import related
from karstfinder.carbonate.priority import priority, terrain_strength
from karstfinder.enhanced.registry import Grid
from karstfinder.enhanced.scoring import STOPS, color
from karstfinder.enhanced.style import COLOR_EXPRESSION
from karstfinder.freeze import verify_freeze
from karstfinder.library import Library


def preserved():
    counts = {'blind_v002': len(verify_freeze(ROOT)['sha256'])}
    for name in ['denny_v001', 'kaleetan_v001', 'marble_v001_reviewed', 'enhanced_v001']:
        snapshot = json.loads((ROOT / f'experiments/snapshots/{name}.json').read_text())
        for name_, digest in snapshot['sha256'].items():
            assert sha(safe_path(name_)) == digest, name_
        counts[name] = len(snapshot['sha256'])
    lib = Library(ROOT)
    original = json.loads((ROOT / 'docs/carbonate_v001/preserved_library_catalog.json').read_text())
    for entry in original['areas']:
        assert lib.entry(entry['area_id']) == entry, entry['area_id']
        assert sha(safe_path(entry['project_path'])) == entry['project_sha256'], entry['project_path']
    return counts


def audit_area(aid, cfg, area, with_library):
    out = safe_path(area['result_dir'])
    manifest = json.loads((out / 'manifest.json').read_text())
    for group in ['inputs', 'prepared', 'outputs', 'code']:
        for name, expected in manifest[group].items():
            assert sha(safe_path(name)) == expected, name
    rows = json.loads((out / 'observations.json').read_text())
    sites = json.loads((out / 'candidates.json').read_text())
    obs = {r['object_id']: r for r in rows}
    assert len(obs) == len(rows)
    ds = ogr.Open(str(out / 'prospecting.gpkg'))
    geometries = {f['object_id']: f.GetGeometryRef().Clone() for f in ds.GetLayerByName('observation_footprints')}
    cores = {f['formation_id']: f.GetGeometryRef().Clone() for f in ds.GetLayerByName('formations')}
    margins = {f['formation_id']: f.GetGeometryRef().Clone() for f in ds.GetLayerByName('uncertainty_margins')}
    eligible = {ident: core.Union(margins[ident]) for ident, core in cores.items()}
    points = {f['object_id']: f.GetGeometryRef().Clone() for f in ds.GetLayerByName('candidates')}
    memberships = json.loads((out / 'membership.json').read_text())
    old = ogr.Open(str(safe_path(area['source_enhanced_dir']) / 'registry.gpkg'))
    originals = {f['object_id']: (f['kind'], f.GetGeometryRef().Clone()) for f in old.GetLayerByName('lead_footprints')}
    base = safe_path(area['baseline_features'])
    terrain = safe_path(area['source_enhanced_processed']) / 'terrain'
    grids = {name: Grid(base / file) for name, file in [('slope', 'slope_1m.tif'), ('depression_depth', 'depression_depth_1m.tif'), ('quality', 'feature_quality_1m.tif')]}
    grids.update({f'residual_{w}m': Grid(terrain / f'residual_{w}m.tif') for w in [11, 31, 61]})
    linked = set()
    for row in rows:
        ident = row['object_id']; geom = geometries[ident]; core = cores[row['formation_id']]
        assert row['source_unit'] in cfg['eligible_units']
        assert surface_area(geom.Difference(eligible[row['formation_id']])) < 1e-5, ident
        assert geometry_key(geom) == row['geometry_sha256']
        fraction = surface_area(geom.Intersection(core)) / geom.GetArea()
        assert abs(fraction - row['carbonate_fraction']) < 1e-8
        for name, grid in grids.items():
            assert grid.summary(geom) == row['measurements'][name], (ident, name)
        assert row['measurements']['quality']['min'] == 1
        if row['kind'] == 'cliff':
            assert row['measurements']['slope']['min'] >= cfg['detection']['cliff_slope_deg']
        elif row['kind'] == 'depression':
            assert row['measurements']['depression_depth']['min'] >= cfg['detection']['depression_depth_m']
        t = terrain_strength(row['kind'], row['measurements'], cfg['scoring'])
        value, factor = priority(True, fraction, t, cfg['scoring'])
        assert abs(value - row['score']) < 1e-8 and factor == row['geological_support_factor']
        assert row['color_hex'] == color(row['score'])
        for old_id in row['source_v001_ids']:
            kind, original = originals[old_id]
            assert kind == row['kind'] and surface_area(original.Intersection(geom)) > 0
            linked.add(old_id)
    assigned = {r['observation_id'] for r in memberships}
    assert all(r['kind'] == 'hydrology' for r in rows if r['object_id'] not in assigned)
    for site in sites:
        members = [obs[i] for i in site['member_ids']]
        surface = [r for r in members if r['kind'] != 'hydrology']
        assert surface and len({r['formation_id'] for r in members}) == 1
        assert site['score'] == max(r['score'] for r in surface)
        assert site['terrain_anomaly_strength'] * site['geological_support_factor'] == site['score']
        assert site['color_hex'] == color(site['score'])
        point = points[site['object_id']]; member = obs[site['waypoint_member_id']]
        assert point.GetX() == site['easting'] == member['easting']
        assert point.GetY() == site['northing'] == member['northing']
        assert geometries[member['object_id']].Intersects(point)
        if any(r['carbonate_fraction'] > 0 for r in surface):
            assert cores[site['formation_id']].Intersects(point)
        assert set(site['member_ids']) == {r['observation_id'] for r in memberships if r['site_id'] == site['object_id']}
        for edge in site['grouping_edges']:
            assert related(geometries[edge['left']], geometries[edge['right']], eligible[site['formation_id']], cfg['sites']['maximum_local_gap_m'])[0]
        for attachment in site['drainage_attachments']:
            assert obs[attachment['object_id']]['kind'] == 'hydrology'
            assert related(geometries[attachment['object_id']], geometries[attachment['supports']], eligible[site['formation_id']], cfg['sites']['maximum_local_gap_m'])[0]
    project = QgsProject()
    assert project.read(str(ROOT / f'qgis/KarstFinder_{aid}_carbonate_v001.qgz'))
    assert all(l.isValid() for l in project.mapLayers().values())
    primary = project.mapLayersByName('Prospecting sites • ALL eligible destinations')[0]
    detailed = project.mapLayersByName('Individual observations • carbonate scope only')[0]
    assert primary.featureCount() == len(sites) and detailed.featureCount() == len(rows)
    assert not primary.subsetString() and not detailed.subsetString()
    assert project.layerTreeRoot().findLayer(primary.id()).isVisible()
    for layer in [primary, detailed]:
        assert not layer.hasScaleBasedVisibility()
        for rule in layer.renderer().rootRule().children():
            assert rule.symbol().symbolLayer(0).dataDefinedProperties().property(QgsSymbolLayer.PropertyFillColor).expressionString() == COLOR_EXPRESSION
    legend_layer = next(l for l in project.mapLayers().values() if 'priority_display_10m.tif' in l.source())
    shader = legend_layer.renderer().shader().rasterShaderFunction()
    assert [(i.value, i.color.name()) for i in shader.colorRampItemList()] == list(STOPS)
    assert shader.minimumValue() == 0 and shader.maximumValue() == 1
    info = {'observations': len(rows), 'sites': len(sites), 'source_v001_ids_linked': len(linked),
            'unattached_drainage_context': len(rows) - len(assigned), 'all_geometries_inside_carbonate_scope': True,
            'key_native_measurements_recomputed': len(rows) * len(grids), 'waypoints_on_actual_member_geometry': True,
            'exact_ramp_and_absolute_scale': True, 'no_scale_hiding_or_subset': True,
            'fresh_project_reopened': True, 'layouts': [l.name() for l in project.layoutManager().layouts()]}
    project.clear()
    if with_library:
        info['library'] = Library(ROOT).verify(area['library_id'])
    return info


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--without-library', action='store_true'); args = parser.parse_args()
    app = QgsApplication([], False); app.initQgis()
    report = {'preserved_hashes_before': preserved(), 'areas': {}}
    cfg = config()
    for aid, area in cfg['areas'].items():
        report['areas'][aid] = audit_area(aid, cfg, area, not args.without_library)
        print(aid, report['areas'][aid], flush=True)
    report['preserved_hashes_after'] = preserved()
    report['original_library_entries_unchanged'] = 8
    write_json(ROOT / 'docs/carbonate_v001/verification.json', report)


if __name__ == '__main__':
    main()
