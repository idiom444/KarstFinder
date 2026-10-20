"""Simple carbonate-only QGIS map: every eligible site, no scale hiding."""
import os,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from qgis.core import (QgsApplication,QgsProject,QgsCoordinateReferenceSystem,Qgis,QgsVectorLayer,QgsRasterLayer,QgsSingleSymbolRenderer,QgsFillSymbol,QgsMarkerSymbol,QgsRasterShader,QgsColorRampShader,QgsSingleBandPseudoColorRenderer,QgsColorRampLegendNodeSettings,QgsMultiBandColorRenderer,QgsContrastEnhancement,QgsReferencedRectangle,QgsRectangle,QgsPalLayerSettings,QgsTextFormat,QgsVectorLayerSimpleLabeling,QgsPrintLayout,QgsLayoutItemPage,QgsLayoutItemMap,QgsLayoutItemLabel,QgsLayoutPoint,QgsLayoutSize,QgsLayoutItemLegend,QgsLayoutExporter,QgsLegendStyle,QgsRelation)
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import QSize
from osgeo import ogr
from karstfinder.enhanced.style import renderer,ramp
from karstfinder.enhanced.scoring import STOPS
from .common import ROOT,config,safe_path,write_json


_APP=None

def build(area_id):
    global _APP
    cfg,area=config(area_id);out=safe_path(area['result_dir']);gpkg=out/'prospecting.gpkg'
    destination=ROOT/f'qgis/KarstFinder_{area_id}_carbonate_v001.qgz'
    if destination.exists():raise FileExistsError(destination)
    gpkg.chmod(0o444)
    app=QgsApplication.instance()
    if app is None:app=QgsApplication([],False);app.initQgis()
    _APP=app
    project=QgsProject();project.setFileName(str(destination));project.setCrs(QgsCoordinateReferenceSystem('EPSG:26910'));project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setTitle('KarstFinder | '+area['name']+' | Carbonate prospecting v001')
    root=project.layerTreeRoot();main=root.addGroup('Cave prospecting • documented marble + flagged 25 m contact margin');review=root.addGroup('Eligible supporting observations • optional inspection');context=root.addGroup('Geology and local imagery / terrain')
    def add(layer,group,visible=False):
        if not layer.isValid():raise ValueError(layer.name())
        project.addMapLayer(layer,False);group.addLayer(layer).setItemVisibilityChecked(visible);return layer
    def vector(table,label,group,symbol=None,visible=False):
        layer=QgsVectorLayer(f'{gpkg}|layername={table}|option:IMMUTABLE=YES',label,'ogr');layer.setReadOnly(True)
        if symbol:layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        return add(layer,group,visible)
    points=vector('candidates','Prospecting sites • ALL eligible destinations',main,visible=True);points.setRenderer(renderer())
    points.setDisplayExpression("'S' || lpad(to_string(\"rank\"),2,'0') || ' | ' || \"evidence\"")
    settings=QgsPalLayerSettings();settings.fieldName="'S' || lpad(to_string(\"rank\"),2,'0')";settings.isExpression=True
    fmt=QgsTextFormat();fmt.setFont(QFont('DejaVu Sans',9));fmt.setSize(9);fmt.setColor(QColor('#202020'));buf=fmt.buffer();buf.setEnabled(True);buf.setColor(QColor('white'));buf.setSize(.7);fmt.setBuffer(buf);settings.setFormat(fmt);points.setLabeling(QgsVectorLayerSimpleLabeling(settings));points.setLabelsEnabled(True)
    footprints=vector('candidate_footprints','Site support footprints • related eligible observations',main,QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#5b6675','outline_width':'.22'}),True)
    observations=vector('observations','Individual observations • carbonate scope only',review);observations.setRenderer(renderer())
    vector('observation_footprints','Individual observation footprints • original scoped geometry',review,QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#ce7100','outline_width':'.3'}))
    membership=vector('membership','Site ↔ observation membership and evidence roles',review)
    formations=vector('formations','Documented marble • PMmb(e) / TRmb(e)',context,QgsFillSymbol.createSimple({'color':'160,75,170,12','outline_color':'#9b3d93','outline_width':'.65'}),True)
    vector('uncertainty_margins','25 m contact uncertainty • not mapped carbonate',context,QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#555555','outline_style':'dash','outline_width':'.3'}),True)
    for rid,parent,child,parent_field,child_field in [('site_observations',points,membership,'object_id','site_id'),('observation_membership',observations,membership,'object_id','observation_id'),('formation_sites',formations,points,'formation_id','formation_id')]:
        relation=QgsRelation();relation.setId(rid);relation.setName(rid.replace('_',' '));relation.setReferencedLayer(parent.id());relation.setReferencingLayer(child.id());relation.addFieldPair(child_field,parent_field);project.relationManager().addRelation(relation)
    def raster(path,label,group=context,visible=False):return add(QgsRasterLayer(str(path),label,'gdal'),group,visible)
    legend_layer=raster(out/'priority_display_10m.tif','Priority • absolute 0–1',main)
    colorfn=QgsColorRampShader(0,1);colorfn.setColorRampType(QgsColorRampShader.Interpolated);colorfn.setSourceColorRamp(ramp());colorfn.setColorRampItemList([QgsColorRampShader.ColorRampItem(v,QColor(c),str(v)) for v,c in STOPS])
    ls=QgsColorRampLegendNodeSettings();ls.setUseContinuousLegend(True);ls.setMinimumLabel('0 • weak');ls.setMaximumLabel('1 • strongest index');colorfn.setLegendSettings(ls)
    shader=QgsRasterShader();shader.setRasterShaderFunction(colorfn);render=QgsSingleBandPseudoColorRenderer(legend_layer.dataProvider(),1,shader);render.setClassificationMin(0);render.setClassificationMax(1);legend_layer.setRenderer(render)
    source=safe_path(area['source_enhanced_processed']);rgb=source/'imagery/rgbnir.tif'
    if rgb.exists():
        layer=raster(rgb,'2023 native RGB • 0.6 m; imagery cannot confirm an entrance')
        rgb_renderer=QgsMultiBandColorRenderer(layer.dataProvider(),1,2,3)
        for channel in ['Red','Green','Blue']:
            e=QgsContrastEnhancement(layer.dataProvider().dataType(1));e.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum);e.setMinimumValue(0);e.setMaximumValue(255);getattr(rgb_renderer,'set'+channel+'ContrastEnhancement')(e)
        layer.setRenderer(rgb_renderer)
    for name in ['slope_1m','depression_depth_1m']:raster(safe_path(area['baseline_features'])/(name+'.tif'),name.replace('_',' '))
    for directory in sorted(safe_path(area['processed_dir']).glob('formation_*')):raster(directory/'eligibility_1m.tif','Eligibility mask • '+directory.name+' (0 excluded, 1 marble, 2 contact)')
    raster(safe_path(area['baseline_features'])/'hillshade_1m.tif','Bare-earth hillshade • existing LiDAR terrain',visible=True)
    ds=ogr.Open(str(gpkg));geol=ds.GetLayerByName('formations');records=[(f['source_id'],f.GetGeometryRef().Clone()) for f in geol]
    if records:
        largest=max(records,key=lambda pair:pair[1].GetArea());extent=QgsRectangle(*[largest[1].GetEnvelope()[i] for i in [0,2,1,3]]);extent.scale(1.5)
        center=extent.center();half=max(300,extent.width()/2,extent.height()/2);detail=QgsRectangle(center.x()-half,center.y()-half,center.x()+half,center.y()+half)
    else:detail=QgsRectangle(*area['study_bounds'])
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(detail,project.crs()))
    summary=json.loads((out/'summary.json').read_text());overview=QgsRectangle(*area['study_bounds']);overview.scale(1.03)
    views=[('Study overview',overview)]
    for source_id,geom in records:
        env=geom.GetEnvelope();ext=QgsRectangle(env[0],env[2],env[1],env[3]);ext.scale(1.5);center=ext.center();half=max(250,ext.width()/2,ext.height()/2);views.append(('Marble detail '+source_id,QgsRectangle(center.x()-half,center.y()-half,center.x()+half,center.y()+half)))
    if not records:views.append(('No documented carbonate',overview))
    previews=[]
    for title,extent in views:
        layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName(title);layout.pageCollection().pages()[0].setPageSize('A4',QgsLayoutItemPage.Landscape)
        def text(value,x,y,w,h,size=9):
            label=QgsLayoutItemLabel(layout);label.setText(value);textfmt=QgsTextFormat();textfmt.setFont(QFont('DejaVu Sans',size));textfmt.setSize(size);label.setTextFormat(textfmt);layout.addLayoutItem(label);label.attemptMove(QgsLayoutPoint(x,y));label.attemptResize(QgsLayoutSize(w,h));return label
        text(area['name']+' | Carbonate prospecting',8,4,281,11,14)
        text(f"{summary['sites']} sites | Documented marble prerequisite | {title} | Unvalidated hypotheses",8,17,281,8)
        item=QgsLayoutItemMap(layout);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(8,29));item.attemptResize(QgsLayoutSize(210,159));item.setLayers([n.layer() for n in root.findLayers() if n.isVisible()]);item.setKeepLayerSet(True);item.setCrs(project.crs());item.zoomToExtent(extent)
        text('PROSPECTING PRIORITY',225,29,65,8,10)
        legend=QgsLayoutItemLegend(layout);layout.addLayoutItem(legend);legend.setTitle('');legend.setAutoUpdateModel(False);legend.model().rootGroup().clear();node=legend.model().rootGroup().addLayer(legend_layer);node.setName('Ordinal index');legend.setSymbolHeight(20);legend.setSymbolWidth(6);legend.setStyleFont(QgsLegendStyle.SymbolLabel,QFont('DejaVu Sans',8));legend.attemptMove(QgsLayoutPoint(225,39));legend.attemptResize(QgsLayoutSize(63,38))
        text('S#: candidate reference point\nGray patches: supporting terrain\nMagenta: documented marble\nDashed gray: 25 m uncertainty\n\nBoundary-only sites ≤0.35.\nMixed/unknown rock excluded.\n\nNo cave entrance identified.\nNo route/access verified.\n\nIdentify a site for measurements,\nmember IDs and alternatives.\nIndividual eligible observations\nremain available in their layer.\n\nNo markers hidden by scale.',225,81,66,108,8)
        text('DNR geology 1:100,000 | Existing USGS / PSLC terrain | EPSG:26910 | 25 m contact margin is an assumption, not measured accuracy',8,196,281,7,8)
        project.layoutManager().addLayout(layout)
        path=ROOT/f"docs/carbonate_v001/{area_id}_{title.lower().replace(' ','_')}.png";assert QgsLayoutExporter(layout).renderPageToImage(0,QSize(),140).save(str(path));previews.append(str(path.relative_to(ROOT)))
    assert project.write()
    report={'area':area_id,'project':str(destination.relative_to(ROOT)),'layers':len(project.mapLayers()),'default_site_count':points.featureCount(),'eligible_observations':observations.featureCount(),'candidate_subset':points.subsetString(),'scale_hiding':False,'default_visible':'All eligible sites and support footprints, carbonate geology, flagged margin and hillshade.','layouts':[name for name,extent in views],'previews':previews,'ramp_stops':STOPS,'default_focus':'Largest documented marble component; overview layout includes the full study.'}
    write_json(ROOT/f'docs/carbonate_v001/{area_id}_map.json',report);return report
