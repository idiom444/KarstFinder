#!/usr/bin/env python3
"""Build a persistent Denny prospecting project, with no entrance-reference layers."""
import csv
import json
import os
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from qgis.core import (QgsApplication,QgsProject,QgsCoordinateReferenceSystem,QgsVectorLayer,QgsRasterLayer,
    QgsFillSymbol,QgsMarkerSymbol,QgsLineSymbol,QgsSingleSymbolRenderer,QgsRasterShader,QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,QgsPalLayerSettings,QgsTextFormat,QgsVectorLayerSimpleLabeling,
    QgsReferencedRectangle,QgsRectangle,QgsPrintLayout,QgsLayoutItemPage,QgsLayoutItemMap,QgsLayoutItemLabel,
    QgsLayoutPoint,QgsLayoutSize,QgsLayoutExporter,QgsMapSettings,QgsMapRendererParallelJob,Qgis)
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import QSize

ROOT=Path(__file__).resolve().parents[1]
feature=ROOT/'results/denny_v001_features';access=ROOT/'results/denny_v001_access'
base=ROOT/'results/denny_v001_landscape';processed=ROOT/'data/processed/denny_v001'
out=ROOT/'results/denny_v001_review';out.mkdir(exist_ok=True)
summary=json.loads((feature/'summary.json').read_text())
rows=list(csv.DictReader((access/'screened_indicators.csv').open()))
marble_rows=[r for r in rows if float(r['mapped_marble_overlap_m2'])>0]
ids=','.join("'"+r['object_id']+"'" for r in marble_rows)
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance()
path=ROOT/'qgis/KarstFinder_Denny_v001.qgz';p.setFileName(str(path))
p.setCrs(QgsCoordinateReferenceSystem('EPSG:26910'));p.setFilePathStorage(Qgis.FilePathType.Relative)
p.setTitle('KarstFinder | Denny Mountain | UNVALIDATED prospecting')
root=p.layerTreeRoot()
field=root.addGroup('Trail observation • ground visibility only; no verified off-trail routes')
targets=root.addGroup('Scientific priorities • unverified surface indicators')
geology=root.addGroup('Geology • DNR 1:100,000 contact uncertainty')
terrain=root.addGroup('Terrain evidence and survey quality')
context=root.addGroup('Study and imagery context')


def add(layer,group,visible=False):
    assert layer.isValid(),layer.name();p.addMapLayer(layer,False)
    group.addLayer(layer).setItemVisibilityChecked(visible)
    return layer


def vector(path,layername,title,group,symbol,subset=None,visible=False):
    layer=QgsVectorLayer(f'{path}|layername={layername}|option:IMMUTABLE=YES',title,'ogr')
    layer.setReadOnly(True)
    if subset:assert layer.setSubsetString(subset)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol));return add(layer,group,visible)


def labels(layer,expression,color='#263445',size=8):
    settings=QgsPalLayerSettings();settings.fieldName=expression;settings.isExpression=True
    if layer.geometryType()==Qgis.GeometryType.Line:settings.placement=Qgis.LabelPlacement.Line
    fmt=QgsTextFormat();fmt.setFont(QFont('DejaVu Sans',size));fmt.setSize(size);fmt.setColor(QColor(color))
    buffer=fmt.buffer();buffer.setEnabled(True);buffer.setSize(.7);buffer.setColor(QColor('white'));fmt.setBuffer(buffer)
    settings.setFormat(fmt);layer.setLabeling(QgsVectorLayerSimpleLabeling(settings));layer.setLabelsEnabled(True)


def raster(path,title,group,stops=None,visible=False,opacity=1):
    layer=QgsRasterLayer(str(path),title,'gdal')
    if stops:
        ramp=QgsColorRampShader();ramp.setColorRampType(QgsColorRampShader.Interpolated)
        ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v,QColor(color),str(v)) for v,color in stops])
        shader=QgsRasterShader();shader.setRasterShaderFunction(ramp)
        renderer=QgsSingleBandPseudoColorRenderer(layer.dataProvider(),1,shader)
        renderer.setClassificationMin(stops[0][0]);renderer.setClassificationMax(stops[-1][0]);layer.setRenderer(renderer)
    layer.setOpacity(opacity);return add(layer,group,visible)


observations=vector(ROOT/'results/denny_v001_observation/observation.gpkg','trail_observation_points',
    'OBS triangles • ON mapped trail; canopy visibility unknown',field,
    QgsMarkerSymbol.createSimple({'name':'triangle','color':'#008b8b','outline_color':'white','size':'3.5'}),visible=True)
labels(observations,'"station_id"','#005c5c',9)
trails=vector(access/'access.gpkg','trails','Official USFS trails • current conditions still apply',field,
    QgsLineSymbol.createSimple({'line_color':'#007c82','line_width':'.55'}),visible=True)
labels(trails,'"trail_name" || \' #\' || "trail_no"','#005c5c',8)
nonfs=vector(access/'access.gpkg','ownership','NON-FS mapped land • access unresolved',field,
    QgsFillSymbol.createSimple({'color':'90,90,90,35','outline_color':'#555555','outline_style':'dash','outline_width':'.4'}),
    "ownerclassification <> 'USDA FOREST SERVICE'",True)
vector(access/'access.gpkg','ownership','USFS mapped ownership • not a legal boundary',field,
    QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#777777','outline_width':'.3'}),
    "ownerclassification = 'USDA FOREST SERVICE'")
for i in range(1,4):
    raster(ROOT/f'results/denny_v001_observation/OBS-{i:02d}_bare_earth_viewshed.tif',
           f'OBS-{i:02d} terrain viewshed • excludes canopy',field,[(0,'#ffffff'),(255,'#80cdc1')],opacity=.45)
top=vector(access/'access.gpkg','screened_indicators','Top 10 marble priorities • steep/off-trail; NOT destinations',targets,
    QgsMarkerSymbol.createSimple({'name':'circle','color':'#9c0053','outline_color':'white','size':'2.5'}),
    'mapped_marble_overlap_m2 > 0 AND rank_within_kind <= 10',True)
labels(top,"'C' || \"rank_within_kind\"",'#790043',8)
vector(access/'access.gpkg','screened_indicators','All indicators • geological rank + access flags',targets,
    QgsMarkerSymbol.createSimple({'name':'circle','color':'#888888','size':'1.5'}))
cliffs=vector(feature/'features.gpkg','surface_indicators',f'{len(marble_rows)} cliff patches overlapping mapped marble',targets,
    QgsFillSymbol.createSimple({'color':'204,98,0,35','outline_color':'#cc6200','outline_width':'.3'}),
    f"object_id IN ({ids})",True)
allcliffs=vector(feature/'features.gpkg','surface_indicators','All cliff indicators • includes uncertain melange/contact context',targets,
    QgsFillSymbol.createSimple({'color':'204,98,0,20','outline_color':'#cc6200','outline_width':'.2'}),"kind='cliff'")
depressions=vector(feature/'features.gpkg','surface_indicators','12 depression cores • none overlaps mapped marble',targets,
    QgsFillSymbol.createSimple({'color':'0,103,190,35','outline_color':'#0067be','outline_width':'.3'}),"kind='depression'")
raster(feature/'combined_score_10m.tif','Combined ordinal index • NOT cave probability',targets,
       [(0,'#ffffff'),(.3,'#d9f0d3'),(.6,'#7fbf7b'),(1,'#006837')],True,.45)
raster(base/'combined_score.tif','Original landscape index • whole marble lens selected',targets,
       [(0,'#ffffff'),(.5,'#fed976'),(1,'#bd0026')])
marble=vector(processed/'context.gpkg','bedrock','Mapped marble PMmb(e) • approximate contacts',geology,
    QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#6a3d9a','outline_width':'.65'}),
    "MAP_UNIT_100K='PMmb(e)' AND OBJECTID=29438",True)
vector(processed/'context.gpkg','bedrock','Mixed melange • carbonate occurrence uncertain',geology,
    QgsFillSymbol.createSimple({'color':'255,225,130,45','outline_color':'#d8b365','outline_width':'.3'}),"MAP_UNIT_100K='JTRmt(e)'")
vector(processed/'context.gpkg','faults','Mapped faults • context only',geology,QgsLineSymbol.createSimple({'line_color':'#555555','line_style':'dash'}))
vector(processed/'context.gpkg','contacts','Mapped contacts • uncertain',geology,QgsLineSymbol.createSimple({'line_color':'#666666','line_width':'.2'}))
for name,title,stops in [
    ('slope_1m','Native slope • degrees',[(0,'#ffffff'),(35,'#fdae6b'),(80,'#a63603')]),
    ('depression_depth_1m','Closed depression depth • metres',[(0,'#ffffff'),(.5,'#bdd7e7'),(3,'#2171b5')]),
    ('residual_11m','11 m elevation residual • metres',[(-3,'#2166ac'),(0,'#ffffff'),(3,'#b2182b')]),
    ('feature_quality_1m','Quality mask • survey seam excluded',[(0,'#f03b20'),(1,'#ffffff')]),
    ('source_epoch_1m','Native acquisition epoch • 2019/2021',[(2019,'#4575b4'),(2021,'#fdae61')]),
    ('terrain_clusters_10m','Six descriptive terrain classes • no cave labels',[(1,'#e41a1c'),(2,'#377eb8'),(3,'#4daf4a'),(4,'#984ea3'),(5,'#ff7f00'),(6,'#ffff33')])]:
    raster(feature/f'{name}.tif',title,terrain,stops)
raster(processed/'features/contributing_area_10m_buffered.tif','Modeled D8 contributing area • m², context only',terrain)
raster(ROOT/'data/raw/naip2017_rgb_2m.tif','NAIP 2017 RGB • partial context coverage',context)
vector(processed/'context.gpkg','study_area','Approved study • 3 × 3 km',context,
    QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#333333','outline_style':'dash','outline_width':'.35'}),visible=True)
hillshade=raster(feature/'hillshade_1m.tif','1 m LiDAR terrain hillshade',context,visible=True)
rect=QgsRectangle(615850,5252250,618850,5255250);rect.scale(1.03)
p.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(rect,p.crs()))
layout=QgsPrintLayout(p);layout.initializeDefaults();layout.setName('Denny Mountain prospecting overview')
layout.pageCollection().pages()[0].setPageSize('A4',QgsLayoutItemPage.Landscape)


def text(value,x,y,w,h,size=9):
    item=QgsLayoutItemLabel(layout);item.setText(value);fmt=QgsTextFormat()
    fmt.setFont(QFont('DejaVu Sans',size));fmt.setSize(size);fmt.setColor(QColor('#263445'));item.setTextFormat(fmt)
    layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(w,h))


text('Denny Mountain | geological prospecting',8,4,282,11,16)
text('Unvalidated follow-up • surface indicators and trail observations • no entrance-reference data',8,16,282,8,9)
item=QgsLayoutItemMap(layout);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(8,29));item.attemptResize(QgsLayoutSize(216,162))
item.setCrs(p.crs());item.setLayers([n.layer() for n in root.findLayers() if n.isVisible()]);item.setKeepLayerSet(True);item.zoomToExtent(rect)
text('MAP KEY',232,29,58,8,10)
text('Purple outline: mapped marble\nOrange: marble cliff patches\nMagenta C#: top cliff ranks\nGreen: combined ordinal index\nTeal lines: official trails\nTeal triangles: OBS stations\nGray: mapped non-FS land\n\nN ↑',232,39,58,60,8)
text('RESULTS AND LIMITS',232,103,58,8,10)
text('9 km² study; 1 m terrain\n48 marble cliff patches\nNo marble depression cores\nNo hiking-ready target route\n\nOBS: possible terrain views\nfrom the mapped trail. Trees,\nsnow and weather omitted.\n\nNo cave detection or\nverified entrance prediction.',232,113,58,78,8)
text('USGS 3DEP • Washington DNR 1:100,000 • USFS trails / ownership | NAD83 UTM 10N, metres | 2026-10-19',8,196,282,8,8)
p.layoutManager().addLayout(layout)
review=out/'native_reviews';review.mkdir(exist_ok=True)
for row in marble_rows[:3]:
    x,y=float(row['easting']),float(row['northing']);settings=QgsMapSettings();settings.setDestinationCrs(p.crs())
    settings.setLayers([cliffs,hillshade]);settings.setExtent(QgsRectangle(x-60,y-60,x+60,y+60));settings.setOutputSize(QSize(1000,1000))
    job=QgsMapRendererParallelJob(settings);job.start();job.waitForFinished()
    assert job.renderedImage().save(str(review/f'cliff_rank_{int(row["rank_within_kind"]):02d}.png'))
assert p.write()
invalid=[l.name() for l in p.mapLayers().values() if not l.isValid()];assert not invalid,invalid
assert all('data/private' not in l.source() and 'validation.gpkg' not in l.source() for l in p.mapLayers().values())
assert QgsLayoutExporter(p.layoutManager().layouts()[0]).renderPageToImage(0,QSize(),180).save(str(out/'map_preview.png'))
report=dict(project=str(path.relative_to(ROOT)),layers=len(p.mapLayers()),invalid_layers=invalid,
            entrance_reference_layers=0,persistent_sources=True,native_reviews=3,layouts=len(p.layoutManager().layouts()))
(ROOT/'docs/experiments/denny_v001_qgis_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
