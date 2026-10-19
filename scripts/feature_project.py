#!/usr/bin/env python3
"""Add independently derived surface indicators to the standalone QGIS project."""
import json,os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from qgis.core import (QgsApplication,QgsProject,QgsVectorLayer,QgsRasterLayer,QgsFillSymbol,QgsMarkerSymbol,QgsSingleSymbolRenderer,
 QgsRasterShader,QgsColorRampShader,QgsSingleBandPseudoColorRenderer,QgsPalLayerSettings,QgsTextFormat,QgsVectorLayerSimpleLabeling,
 QgsPrintLayout,QgsLayoutItemPage,QgsLayoutItemMap,QgsLayoutItemLabel,QgsLayoutPoint,QgsLayoutSize,QgsLayoutExporter,QgsRectangle,
 QgsReferencedRectangle,Qgis)
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import QSize
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'results/blind_v002'
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance()
assert project.read(str(ROOT/'qgis/KarstFinder_Blind_v001.qgz'))
project.setTitle('KarstFinder | Blind v002 | Landscape and surface indicators')
root=project.layerTreeRoot();group=root.insertGroup(0,'Blind v002 — UNVERIFIED surface indicators')
context=root.insertGroup(1,'Native-resolution evidence and quality')
for node in root.findLayers():node.setItemVisibilityChecked(False)

def add(layer,parent,visible=False):
 assert layer.isValid(),layer.name();project.addMapLayer(layer,False);node=parent.addLayer(layer);node.setItemVisibilityChecked(visible);return layer


def vector(layername,title,color,where=None,visible=True):
 layer=QgsVectorLayer(f'{out/"features.gpkg"}|layername={layername}',title,'ogr')
 if where:layer.setSubsetString(where)
 if layername=='surface_indicators':symbol=QgsFillSymbol.createSimple({'color':color+',35','outline_color':color+',230','outline_width':'.25'})
 else:symbol=QgsMarkerSymbol.createSimple({'name':'circle','color':color+',200','outline_color':'255,255,255','outline_width':'.2','size':'2'})
 layer.setRenderer(QgsSingleSymbolRenderer(symbol));return add(layer,group,visible)


def raster(path,title,parent,stops=None,visible=False,opacity=1):
 layer=QgsRasterLayer(str(path),title,'gdal')
 if stops:
  ramp=QgsColorRampShader();ramp.setColorRampType(QgsColorRampShader.Interpolated)
  ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v,QColor(c),str(v)) for v,c in stops]);shader=QgsRasterShader();shader.setRasterShaderFunction(ramp)
  renderer=QgsSingleBandPseudoColorRenderer(layer.dataProvider(),1,shader);renderer.setClassificationMin(stops[0][0]);renderer.setClassificationMax(stops[-1][0]);layer.setRenderer(renderer)
 layer.setOpacity(opacity);return add(layer,parent,visible)
summary=json.loads((out/'summary.json').read_text())
depressions=vector('surface_indicators','Closed-depression cores • not confirmed sinkholes','0,103,190',"kind = 'depression'")
cliffs=vector('surface_indicators','Cliff/outcrop exposures • not openings','204,98,0',"kind = 'cliff'")
points=vector('ranked_indicators','All ranked indicators • inspect attributes','156,0,83',visible=False)
top=vector('ranked_indicators','Top 10 per method • separate method ranks','156,0,83','rank_within_kind <= 10')
label=QgsPalLayerSettings();label.fieldName='"kind" || \' \' || "rank_within_kind"';label.isExpression=True
fmt=QgsTextFormat();fmt.setSize(7);fmt.setColor(QColor('#790043'));label.setFormat(fmt);top.setLabeling(QgsVectorLayerSimpleLabeling(label));top.setLabelsEnabled(True)
raster(out/'combined_score_10m.tif','Combined index • ordinal, not probability',group,[(0,'#ffffff'),(.3,'#d9f0d3'),(.6,'#7fbf7b'),(1,'#006837')],True,.6)
raster(out/'geology_score_10m.tif','Geology + assumed contact buffer',group,[(0,'#eeeeee'),(.35,'#fee08b'),(.6,'#d8b365'),(1,'#8856a7')])
raster(out/'feature_score_10m.tif','Independent surface morphology index',group,[(0,'#ffffff'),(.5,'#9ecae1'),(1,'#08519c')])
raster(out/'terrain_clusters_10m.tif','Unsupervised terrain classes • no cave labels',group,[(1,'#e41a1c'),(2,'#377eb8'),(3,'#4daf4a'),(4,'#984ea3'),(5,'#ff7f00'),(6,'#ffff33')])
raster(out/'depression_depth_1m.tif','Closed depression depth • metres',context,[(0,'#ffffff'),(.5,'#bdd7e7'),(3,'#2171b5'),(15,'#08306b')])
raster(out/'slope_1m.tif','Native Horn slope • degrees',context,[(0,'#ffffff'),(45,'#fdae6b'),(80,'#a63603')])
raster(out/'residual_11m.tif','11 m elevation residual • metres',context,[(-3,'#2166ac'),(0,'#ffffff'),(3,'#b2182b')])
raster(out/'feature_quality_1m.tif','Feature quality mask • excludes epoch seams',context,[(0,'#f03b20'),(1,'#ffffff')])
raster(out/'source_epoch_1m.tif','Exact native acquisition • 2019 / 2021',context,[(2019,'#4575b4'),(2021,'#fdae61')])
raster(ROOT/'data/processed/features_v002/contributing_area_10m_buffered.tif','Modeled D8 contributing area • m², edge-limited',context)
raster(out/'hillshade_1m.tif','Native terrain hillshade • numerical DEM',context,visible=True)
rect=QgsRectangle(617000,5253500,623000,5258500);rect.scale(1.03);project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(rect,project.crs()))
visible=[n.layer() for n in root.findLayers() if n.isVisible()]
layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName('Blind v002 independent surface evidence');layout.pageCollection().pages()[0].setPageSize('A4',QgsLayoutItemPage.Landscape)

def text(txt,x,y,w,h,size=9,color='#263445'):
 item=QgsLayoutItemLabel(layout);item.setText(txt);fmt=QgsTextFormat();fmt.setFont(QFont('DejaVu Sans',size));fmt.setSize(size);fmt.setColor(QColor(color));item.setTextFormat(fmt);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(w,h))
text('KarstFinder | independent surface indicators',8,4,280,12,16)
text('Blind v002 • no cave records consulted • surface indicators are not detected openings',8,16,280,9,9)
mapitem=QgsLayoutItemMap(layout);layout.addLayoutItem(mapitem);mapitem.attemptMove(QgsLayoutPoint(8,29));mapitem.attemptResize(QgsLayoutSize(222,166));mapitem.setCrs(project.crs());mapitem.setLayers(visible);mapitem.setKeepLayerSet(True);mapitem.zoomToExtent(rect)
text('EVIDENCE',236,29,56,8,10)
text(f'Blue: {summary["by_kind"]["depression"]["ranked_quality_and_geology_components"]} depression cores\nOrange: {summary["by_kind"]["cliff"]["ranked_quality_and_geology_components"]} cliff exposures\nMagenta: top 10 per method\nGreen: combined ordinal index\n\n1 m bare-earth morphology\n10 m landscape context\n2019 / 2021 USGS LiDAR\nDNR 1:100,000 geology',236,39,56,59,8)
text('LIMITS',236,105,56,8,10)
text('Glacial hollows; talus; forest\nclassification; buried bedrock;\nunderhangs invisible from above.\n\n25 m survey-seam exclusion.\n100 m geological buffer is an\nassumption, not map accuracy.\n\nNo calibrated probabilities.\nNo entrance confirmation.\nN ↑',236,116,56,70,8)
text('blind_v002 | 30 km² | NAD83 / UTM 10N • NAVD88 metres | blind-stage evidence only',8,198,280,7,8)
project.layoutManager().addLayout(layout)
# Save native-scale reviews for the first five indicators per method; identical settings, no labels from external sources.
review=out/'reviews';review.mkdir(exist_ok=True)
for kind,color in [('depression','#0067be'),('cliff','#cc6200')]:
 layer=depressions if kind=='depression' else cliffs
 fs=sorted(layer.getFeatures(),key=lambda f:f['rank_within_kind'])[:5]
 for f in fs:
  local=QgsRectangle(f.geometry().boundingBox());local.grow(35)
  mapitem.zoomToExtent(local);image=QgsLayoutExporter(layout).renderPageToImage(0,QSize(),140)
  assert image.save(str(review/f'{kind}_{f["rank_within_kind"]:02d}.png'))
mapitem.zoomToExtent(rect)
path=ROOT/'qgis/KarstFinder.qgz';project.setFileName(str(path));assert project.write()
assert project.read(str(path));invalid=[l.name() for l in project.mapLayers().values() if not l.isValid()];assert not invalid,invalid
export=QgsLayoutExporter(project.layoutManager().layoutByName('Blind v002 independent surface evidence'))
assert export.renderPageToImage(0,QSize(),180).save(str(out/'map_preview.png'))
report={'project':str(path.relative_to(ROOT)),'layer_count':len(project.mapLayers()),'invalid_layers':invalid,'layouts':len(project.layoutManager().layouts()),'native_reviews':10}
(ROOT/'docs/qgis_v002_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
# The short-lived process releases its read-only providers at normal exit.
