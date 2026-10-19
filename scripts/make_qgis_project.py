#!/usr/bin/env python3
"""Create and reopen a standalone local QGIS project, with a rendered preview."""
import argparse
import json
import os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from qgis.core import (QgsApplication,QgsProject,QgsRasterLayer,QgsVectorLayer,QgsColorRampShader,
    QgsRasterShader,QgsSingleBandPseudoColorRenderer,QgsFillSymbol,QgsLineSymbol,QgsMarkerSymbol,
    QgsSingleSymbolRenderer,QgsCoordinateReferenceSystem,QgsRectangle,QgsMapSettings,
    QgsPrintLayout,QgsLayoutItemPage,QgsLayoutItemMap,QgsLayoutItemLabel,QgsLayoutPoint,QgsLayoutSize,QgsLayoutExporter,QgsLayoutItemScaleBar,
    QgsMapRendererParallelJob,Qgis,QgsPalLayerSettings,QgsTextFormat,QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import QSize

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',default='results/blind_v001');args=ap.parse_args()
    result=ROOT/args.results
    summary=json.loads((result/'summary.json').read_text())
    app=QgsApplication([],False);app.initQgis()
    project=QgsProject.instance();project.setCrs(QgsCoordinateReferenceSystem('EPSG:26910'))
    project.setTitle('KarstFinder | Cave Ridge | BLIND exploratory baseline')
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    meta=project.metadata();meta.setTitle(project.title());meta.setAuthor('KarstFinder');meta.setAbstract('Exploratory blind landscape hypotheses. No known local cave locations consulted; not an entrance detector or calibrated probability.');project.setMetadata(meta)
    groups={name:project.layerTreeRoot().addGroup(name) for name in [
        'Study boundary','Preliminary landscape areas — NOT entrances','Landscape hypotheses',
        'Geological evidence — DNR 1:100,000','Terrain measurements — 10 m','Elevation and imagery','Basemaps']}
    layers=[]
    def add(layer,group,visible=True):
        if not layer.isValid():raise RuntimeError(f'Invalid layer: {layer.name()}: {layer.source()}')
        project.addMapLayer(layer,False);node=groups[group].addLayer(layer);node.setItemVisibilityChecked(visible);layers.append(layer)
        return layer
    def raster(path,title,group,visible=False,ramp=None,opacity=1):
        layer=QgsRasterLayer(str(path),title,'gdal')
        if ramp:
            sh=QgsColorRampShader();sh.setColorRampType(QgsColorRampShader.Interpolated)
            sh.setColorRampItemList([QgsColorRampShader.ColorRampItem(v,QColor(color),str(v)) for v,color in ramp])
            rs=QgsRasterShader();rs.setRasterShaderFunction(sh)
            renderer=QgsSingleBandPseudoColorRenderer(layer.dataProvider(),1,rs);renderer.setClassificationMin(ramp[0][0]);renderer.setClassificationMax(ramp[-1][0]);layer.setRenderer(renderer)
        layer.setOpacity(opacity);return add(layer,group,visible)
    def vector(name,title,group,style=None,visible=False,gpkg=None):
        path=gpkg or ROOT/'data/processed/context.gpkg';layer=QgsVectorLayer(f'{path}|layername={name}',title,'ogr')
        if style:layer.setRenderer(QgsSingleSymbolRenderer(style))
        return add(layer,group,visible)
    boundary=vector('study_area','Study envelope • 30 km²','Study boundary',
        QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'35,49,62,255','outline_width':'0.45','outline_style':'dash'}),True)
    candidate=vector('candidate_areas','Ranked landscape areas • unverified','Preliminary landscape areas — NOT entrances',
        QgsFillSymbol.createSimple({'color':'255,0,90,20','outline_color':'220,0,70,255','outline_width':'0.65'}),True,result/'candidates.gpkg')
    labeling=QgsPalLayerSettings();labeling.fieldName='candidate_id';fmt=QgsTextFormat();fmt.setSize(9);fmt.setColor(QColor('#9c003b'));labeling.setFormat(fmt)
    candidate.setLabeling(QgsVectorLayerSimpleLabeling(labeling));candidate.setLabelsEnabled(True)
    ramp=[(0,'#f7fcf5'),(.25,'#c7e9c0'),(.5,'#74c476'),(.75,'#238b45'),(1,'#00441b')]
    raster(result/'combined_score.tif','Lithology × terrain index • NOT probability','Landscape hypotheses',True,ramp,.7)
    raster(result/'terrain_score.tif','Terrain index • 0–1 hypothesis','Landscape hypotheses',False,ramp)
    raster(result/'mid_slope_votes.tif','Mid-slope votes • 0–3','Landscape hypotheses',False,[(0,'#eeeeee'),(1,'#fee08b'),(2,'#91cf60'),(3,'#1a9850')])
    raster(result/'geological_score.tif','Mapped lithology evidence index','Geological evidence — DNR 1:100,000',False,[(0,'#eeeeee'),(.35,'#fee08b'),(1,'#8856a7')])
    geo=vector('bedrock','Geological units (PMmb(e) = marble)','Geological evidence — DNR 1:100,000',
        QgsFillSymbol.createSimple({'color':'160,130,190,20','outline_color':'96,60,110,255','outline_width':'.25'}),False)
    geo.setDisplayExpression('"MAP_UNIT_100K"')
    vector('contacts','Geological contacts • uncertain','Geological evidence — DNR 1:100,000',QgsLineSymbol.createSimple({'line_color':'#79618a','line_width':'.3'}),False)
    vector('faults','Mapped faults','Geological evidence — DNR 1:100,000',QgsLineSymbol.createSimple({'line_color':'#c52b2b','line_width':'.6'}),False)
    vector('orientations','Structural measurements','Geological evidence — DNR 1:100,000',QgsMarkerSymbol.createSimple({'name':'cross','color':'#244f8f','size':'2'}),False)
    for scale in [210,610,2010]:
        raster(result/f'dev_{scale}m.tif',f'Standardized topographic position • {scale} m window','Terrain measurements — 10 m',False,[(-2,'#2166ac'),(0,'#f7f7f7'),(2,'#b2182b')])
    raster(result/'slope.tif','Slope • degrees (Horn)','Terrain measurements — 10 m',False,[(0,'#fff7ec'),(30,'#fdbb84'),(60,'#d7301f'),(90,'#7f0000')])
    raster(result/'aspect.tif','Aspect • degrees clockwise from north','Terrain measurements — 10 m')
    raster(result/'analysis_valid.tif','Complete neighbourhood support • 1 = valid','Terrain measurements — 10 m')
    raster(ROOT/'data/processed/source_epoch_10m.tif','LiDAR acquisition • 2019 / 2021','Elevation and imagery',False,[(2019,'#4c78a8'),(2021,'#f58518')])
    raster(ROOT/'data/processed/dem_1m_buffered.tif','USGS bare-earth elevation • 1 m / NAVD88 m','Elevation and imagery')
    raster(ROOT/'data/processed/dem_10m_buffered.tif','Averaged elevation • 10 m / NAVD88 m','Elevation and imagery')
    raster(ROOT/'data/raw/naip2017_rgb_2m.tif','NAIP 2017 RGB • exported at 2 m','Elevation and imagery')
    hill=raster(result/'hillshade.tif','Local terrain hillshade (10 m DEM)','Basemaps',True)
    rect=boundary.extent();rect.scale(1.03)
    project.viewSettings().setDefaultViewExtent(__import__('qgis.core',fromlist=['QgsReferencedRectangle']).QgsReferencedRectangle(rect,project.crs()))
    visible=[node.layer() for node in project.layerTreeRoot().findLayers() if node.isVisible()]
    layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName('Blind landscape baseline')
    layout.pageCollection().pages()[0].setPageSize('A4',QgsLayoutItemPage.Landscape)
    def label(text,x,y,width,height,size=9,color='#263445'):
        item=QgsLayoutItemLabel(layout);item.setText(text);item.setFont(QFont('DejaVu Sans',size));item.setFontColor(QColor(color))
        layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(width,height));return item
    label('KarstFinder | Cave Ridge',8,5,210,10,17)
    label('Blind landscape baseline • exploratory and unfrozen • no confirmed entrances',8,16,280,9,9)
    mapitem=QgsLayoutItemMap(layout);layout.addLayoutItem(mapitem);mapitem.attemptMove(QgsLayoutPoint(8,28))
    mapitem.attemptResize(QgsLayoutSize(222,168));mapitem.setCrs(project.crs());mapitem.setLayers(visible);mapitem.setKeepLayerSet(True);mapitem.zoomToExtent(rect)
    label('LANDSCAPE INDEX',236,29,58,7,10)
    label('Green shading: ordinal\nlithology × terrain score.\nDarker = stronger hypothesis.\nValues 0–1 are not probabilities.',236,38,56,26,8)
    label(f'Magenta outlines + KF IDs:\nranked landscape areas.\n{summary["candidate_area_count"]} areas • {summary["candidate_area_km2"]:.4f} km² total.\nRepresentative points in CSV\nare not entrance locations.',236,70,56,32,8,'#9c003b')
    label('EVIDENCE / LIMITS',236,109,58,7,10)
    label('USGS 2019 / 2021 LiDAR\nWA DNR 1:100,000 geology\n10 m landscape grid\n210 / 610 / 2,010 m windows\n\nCoarse contacts; glacial terrain;\nforest and overhang occlusion.\nBoundary clips KF-001.\n\nNo known local cave records\nwere consulted.',236,118,57,64,8)
    label('N ↑',273,185,20,10,12)
    scale=QgsLayoutItemScaleBar(layout);scale.setStyle('Single Box');scale.setLinkedMap(mapitem);scale.setUnits(Qgis.DistanceUnit.Meters)
    scale.setUnitsPerSegment(500);scale.setNumberOfSegments(2);scale.setNumberOfSegmentsLeft(0);scale.setUnitLabel('m');scale.setHeight(1.7)
    layout.addLayoutItem(scale);scale.attemptMove(QgsLayoutPoint(13,181))
    label('blind_v001 | NAD83 / UTM 10N • NAVD88 metres | 2026-10-19 | landscape hypotheses only',8,198,280,7,8)
    project.layoutManager().addLayout(layout)
    path=ROOT/'qgis/KarstFinder.qgz';project.setFileName(str(path));assert project.write()
    # Reopening is a required deliverable, not just a successful write call.
    assert project.read(str(path));invalid=[l.name() for l in project.mapLayers().values() if not l.isValid()]
    assert not invalid,invalid
    export=QgsLayoutExporter(project.layoutManager().layoutByName('Blind landscape baseline'))
    options=QgsLayoutExporter.ImageExportSettings();options.dpi=180
    assert export.exportToImage(str(result/'map_preview.png'),options)==QgsLayoutExporter.Success
    report={'project':str(path.relative_to(ROOT)),'qgis_version':Qgis.QGIS_VERSION,'layer_count':len(project.mapLayers()),
            'invalid_layers_after_reopen':invalid,'paths':'relative','preview':str((result/'map_preview.png').relative_to(ROOT))}
    (ROOT/'docs/qgis_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    project.clear();app.exitQgis()


if __name__=='__main__':main()
