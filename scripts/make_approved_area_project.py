#!/usr/bin/env python3
"""Separate persistent maps for the two approved literature-informed studies."""
import argparse
import csv
import json
import os
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qgis.core import (QgsApplication, QgsProject, QgsCoordinateReferenceSystem,
    QgsVectorLayer, QgsRasterLayer, QgsFillSymbol, QgsMarkerSymbol, QgsLineSymbol,
    QgsSingleSymbolRenderer, QgsRasterShader, QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer, QgsPalLayerSettings, QgsTextFormat,
    QgsVectorLayerSimpleLabeling, QgsReferencedRectangle, QgsRectangle,
    QgsPrintLayout, QgsLayoutItemPage, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutPoint, QgsLayoutSize, QgsLayoutExporter, QgsLayoutItemScaleBar, Qgis)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QSize

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('area', choices=['kaleetan', 'marble'])
    args = parser.parse_args()
    area = args.area + '_v001'
    cfg = json.loads((ROOT / f'configs/{area}_landscape.json').read_text())
    title = cfg['area_name']
    processed = ROOT / cfg['processed_dir']
    base = ROOT / f'results/{area}_landscape'
    features = ROOT / f'results/{area}_features'
    access = ROOT / f'results/{area}_access'
    rows = list(csv.DictReader((access / 'screened_indicators.csv').open()))
    direct = [r for r in rows if float(r['mapped_marble_overlap_m2']) > 0]
    dep = sum(r['kind'] == 'depression' for r in rows)
    direct_dep = sum(r['kind'] == 'depression' for r in direct)
    qa = json.loads((processed / 'features/qa.json').read_text())
    app = QgsApplication([], False); app.initQgis()
    project = QgsProject.instance()
    destination = ROOT / f'qgis/KarstFinder_{args.area.title()}_v001.qgz'
    if destination.exists():
        raise RuntimeError(f'Refusing map overwrite: {destination}')
    project.setFileName(str(destination))
    project.setCrs(QgsCoordinateReferenceSystem(cfg['crs']))
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setTitle(f'KarstFinder | {title} | UNVALIDATED prospecting')
    root = project.layerTreeRoot()
    targets = root.addGroup('Prospecting hypotheses • points represent patches, not entrances')
    geology = root.addGroup('Geology • DNR 1:100,000 approximate contacts')
    terrain = root.addGroup('Terrain components and data quality • expand to inspect')
    context = root.addGroup('Study and public access context • no route verified')

    def add(layer, group, visible=False):
        assert layer.isValid(), layer.name()
        project.addMapLayer(layer, False)
        group.addLayer(layer).setItemVisibilityChecked(visible)
        return layer

    def vector(path, name, label, group, symbol, subset=None, visible=False):
        layer = QgsVectorLayer(f'{path}|layername={name}|option:IMMUTABLE=YES', label, 'ogr')
        layer.setReadOnly(True)
        if subset:
            assert layer.setSubsetString(subset)
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        return add(layer, group, visible)

    def labels(layer, expression, color, size=8):
        settings = QgsPalLayerSettings(); settings.fieldName = expression; settings.isExpression = True
        fmt = QgsTextFormat(); fmt.setFont(QFont('DejaVu Sans', size)); fmt.setSize(size); fmt.setColor(QColor(color))
        buf = fmt.buffer(); buf.setEnabled(True); buf.setColor(QColor('white')); buf.setSize(.7); fmt.setBuffer(buf)
        settings.setFormat(fmt); layer.setLabeling(QgsVectorLayerSimpleLabeling(settings)); layer.setLabelsEnabled(True)

    def raster(path, label, stops=None, visible=False, group=terrain, opacity=1):
        layer = QgsRasterLayer(str(path), label, 'gdal')
        if stops:
            ramp = QgsColorRampShader(); ramp.setColorRampType(QgsColorRampShader.Interpolated)
            ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), str(v)) for v, c in stops])
            shader = QgsRasterShader(); shader.setRasterShaderFunction(ramp)
            renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
            renderer.setClassificationMin(stops[0][0]); renderer.setClassificationMax(stops[-1][0])
            layer.setRenderer(renderer)
        layer.setOpacity(opacity)
        return add(layer, group, visible)

    point = vector(access / 'access.gpkg', 'screened_indicators',
        f'{len(direct)} mapped-marble indicators • purple dots are patch representatives', targets,
        QgsMarkerSymbol.createSimple({'name': 'circle', 'color': '#9c0053', 'outline_color': 'white', 'size': '3'}),
        'mapped_marble_overlap_m2 > 0', True)
    labels(point, "upper(left(\"kind\",1)) || \"rank_within_kind\"", '#790043')
    vector(access / 'access.gpkg', 'screened_indicators', f'All {len(rows)} ranked indicators • includes uncertain surrounding geology', targets,
        QgsMarkerSymbol.createSimple({'name': 'circle', 'color': '#777777', 'size': '1.5'}))
    ids = ','.join("'" + r['object_id'] + "'" for r in direct)
    vector(features / 'features.gpkg', 'surface_indicators', 'Orange patches • overlap mapped marble; unverified', targets,
        QgsFillSymbol.createSimple({'color': '204,98,0,40', 'outline_color': '#cc6200', 'outline_width': '.4'}),
        f'object_id IN ({ids})' if ids else '1=0', True)
    vector(features / 'features.gpkg', 'surface_indicators', f'All cliff patches • {len(rows)-dep}; geological support varies', targets,
        QgsFillSymbol.createSimple({'color': '204,98,0,20', 'outline_color': '#cc6200', 'outline_width': '.2'}), "kind='cliff'")
    vector(features / 'features.gpkg', 'surface_indicators', f'Closed depression cores • {dep}; {direct_dep} overlap mapped marble', targets,
        QgsFillSymbol.createSimple({'color': '0,103,190,40', 'outline_color': '#0067be', 'outline_width': '.3'}), "kind='depression'")
    vector(base / 'candidates.gpkg', 'candidate_areas', 'Gold outline • landscape hypothesis areas', targets,
        QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': '#d6a000', 'outline_style': 'dash', 'outline_width': '.45'}))
    raster(features / 'combined_score_10m.tif', 'Combined ordinal index • not a cave probability',
        [(0, '#ffffff'), (.3, '#d9f0d3'), (.6, '#7fbf7b'), (1, '#006837')], group=targets, opacity=.45)
    raster(base / 'combined_score.tif', 'Landscape index • 10 m; not an entrance model',
        [(0, '#ffffff'), (.5, '#fed976'), (1, '#bd0026')], group=targets, opacity=.45)
    units = ','.join("'" + u + "'" for u in cfg['marble_units'])
    marble = vector(processed / 'context.gpkg', 'bedrock', 'Mapped marble ' + '/'.join(cfg['marble_units']) + ' • purple outline', geology,
        QgsFillSymbol.createSimple({'color': '106,61,154,18', 'outline_color': '#6a3d9a', 'outline_width': '.7'}),
        f'MAP_UNIT_100K IN ({units})', True)
    vector(processed / 'context.gpkg', 'bedrock', 'Mixed melange • possible carbonate, uncertain distribution', geology,
        QgsFillSymbol.createSimple({'color': '255,225,130,40', 'outline_color': '#d8b365', 'outline_width': '.25'}), "MAP_UNIT_100K='JTRmt(e)'")
    vector(processed / 'context.gpkg', 'faults', 'Mapped faults • context only', geology,
        QgsLineSymbol.createSimple({'line_color': '#555555', 'line_style': 'dash'}))
    vector(processed / 'context.gpkg', 'contacts', 'Mapped contacts • positional uncertainty', geology,
        QgsLineSymbol.createSimple({'line_color': '#666666', 'line_width': '.2'}))
    for name, label, stops in [
        ('slope_1m', 'Slope • degrees', [(0, '#ffffff'), (35, '#fdae6b'), (80, '#a63603')]),
        ('depression_depth_1m', 'Closed depression depth • metres', [(0, '#ffffff'), (.5, '#bdd7e7'), (3, '#2171b5')]),
        ('residual_11m', '11 m elevation residual • metres', [(-3, '#2166ac'), (0, '#ffffff'), (3, '#b2182b')]),
        ('feature_quality_1m', 'Eligible terrain mask • seams excluded', [(0, '#f03b20'), (1, '#ffffff')]),
        ('terrain_clusters_10m', 'Six descriptive terrain classes • no cave labels', [(1, '#e41a1c'), (2, '#377eb8'), (3, '#4daf4a'), (4, '#984ea3'), (5, '#ff7f00'), (6, '#ffff33')])]:
        raster(features / (name + '.tif'), label, stops)
    years = sorted(int(y) for y, n in qa['native_year_counts'].items() if int(y) and n)
    raster(features / 'source_epoch_1m.tif', 'Source project year • ' + '/'.join(map(str, years)),
        [(years[0], '#4575b4'), (years[-1]+.01, '#fdae61')])
    raster(processed / 'features/contributing_area_10m_buffered.tif', 'Modeled D8 contributing area • m², context only')
    for name in ['terrain_score', 'geological_score', 'mid_slope_votes', 'exposure', 'analysis_valid', 'dev_210m', 'dev_610m', 'dev_2010m']:
        raster(base / (name + '.tif'), 'Landscape component • ' + name)
    vector(access / 'access.gpkg', 'trails', 'Official USFS trails • query context; no route approval', context,
        QgsLineSymbol.createSimple({'line_color': '#007c82', 'line_width': '.5'}), visible=True)
    vector(access / 'access.gpkg', 'ownership', 'Mapped ownership • access still unresolved', context,
        QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': '#777777', 'outline_width': '.3'}))
    vector(processed / 'context.gpkg', 'study_area', 'Approved study • 3 × 3 km', context,
        QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': '#333333', 'outline_style': 'dash', 'outline_width': '.35'}), visible=True)
    raster(features / 'hillshade_1m.tif', '1 m terrain grid • bare-earth hillshade', visible=True, group=context)
    overview = QgsRectangle(*cfg['study_bounds']); overview.scale(1.03)
    detail = QgsRectangle(marble.extent()); detail.scale(1.6)
    if detail.width() < 500 or detail.height() < 500:
        center = detail.center(); half = max(250, detail.width()/2, detail.height()/2)
        detail = QgsRectangle(center.x()-half, center.y()-half, center.x()+half, center.y()+half)
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(detail, project.crs()))
    previews = []
    for name, extent in [('overview', overview), ('marble_detail', detail)]:
        layout = QgsPrintLayout(project); layout.initializeDefaults(); layout.setName(name)
        layout.pageCollection().pages()[0].setPageSize('A4', QgsLayoutItemPage.Landscape)

        def text(value, x, y, w, h, size=9):
            label = QgsLayoutItemLabel(layout); label.setText(value)
            fmt = QgsTextFormat(); fmt.setFont(QFont('DejaVu Sans', size)); fmt.setSize(size); fmt.setColor(QColor('#263445'))
            label.setTextFormat(fmt); layout.addLayoutItem(label)
            label.attemptMove(QgsLayoutPoint(x, y)); label.attemptResize(QgsLayoutSize(w, h))

        text(title + ' | ' + name.replace('_', ' '), 8, 4, 282, 11, 15)
        text('Unvalidated prospecting • literature-informed area selection • no entrance predictions', 8, 16, 282, 8)
        item = QgsLayoutItemMap(layout); layout.addLayoutItem(item)
        item.attemptMove(QgsLayoutPoint(8, 29)); item.attemptResize(QgsLayoutSize(216, 162))
        item.setCrs(project.crs()); item.setLayers([n.layer() for n in root.findLayers() if n.isVisible()])
        item.setKeepLayerSet(True); item.zoomToExtent(extent)
        bar = QgsLayoutItemScaleBar(layout); bar.setStyle('Single Box'); bar.setLinkedMap(item)
        bar.setUnits(Qgis.DistanceUnit.Meters); bar.setUnitsPerSegment(100 if name == 'marble_detail' else 500)
        bar.setNumberOfSegments(2); bar.setNumberOfSegmentsLeft(0); bar.setUnitLabel('m'); bar.applyDefaultSize()
        layout.addLayoutItem(bar); bar.attemptMove(QgsLayoutPoint(12, 180))
        text('MAP KEY', 232, 29, 58, 8, 10)
        text('Purple outline: mapped marble\nPurple dots: representative\npoints of marble indicators\nOrange: indicator footprints\nTeal lines: USFS trails\nDashed: 3 × 3 km boundary\n\nC#: original cliff rank\nD#: depression rank\n\nN ↑', 232, 40, 58, 65, 8)
        text('RESULTS AND LIMITS', 232, 107, 58, 8, 10)
        text(f'9 km² study; 1 m terrain grid\n{len(rows)} surface indicators\n{len(direct)} overlap mapped marble\n{direct_dep} marble depression cores\n\nMost indicators may reflect\nglacial or slope processes.\nNo cave confirmed.\nNo route verified.\n\nExpand hidden map layers\nfor all ranks and components.', 232, 117, 58, 74, 8)
        text('USGS / PSLC terrain • Washington DNR geology 1:100,000 • USFS | NAD83 UTM 10N, metres | 2026-10-19', 8, 196, 282, 8, 8)
        project.layoutManager().addLayout(layout)
        path = ROOT / f'docs/experiments/{area}_{name}.png'
        assert QgsLayoutExporter(layout).renderPageToImage(0, QSize(), 150).save(str(path))
        previews.append(str(path.relative_to(ROOT)))
    assert project.write()
    assert all('data/private' not in l.source() and 'validation.gpkg' not in l.source() for l in project.mapLayers().values())
    report = {'project': str(destination.relative_to(ROOT)), 'layers': len(project.mapLayers()),
        'invalid_layers': [], 'entrance_reference_layers': 0, 'layouts': ['overview', 'marble_detail'],
        'previews': previews, 'surface_indicators': len(rows), 'mapped_marble_indicators': len(direct),
        'default_extent': 'mapped marble detail; overview print layout retains entire approved area'}
    (ROOT / f'docs/experiments/{area}_qgis_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
