#!/usr/bin/env python3
"""Persistent enhanced QGIS maps, exact continuous colors and review layouts."""
import argparse,json,os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from osgeo import gdal,ogr
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import QSize,Qt
from karstfinder.enhanced.common import config,safe_path,write_json,sha
from karstfinder.enhanced.scoring import STOPS
from karstfinder.enhanced.style import ramp,renderer,COLOR_EXPRESSION


def main(area_id):
    gdal.UseExceptions();ogr.UseExceptions()
    cfg,area=config(area_id);out=safe_path(area['result_dir']);pre=safe_path(area['processed_dir']);base=safe_path(area['baseline_features'])
    destination=ROOT/f'qgis/KarstFinder_{area_id}_enhanced_v001.qgz'
    if destination.exists():raise FileExistsError(destination)
    # A display aggregate only; candidate coordinates/geometries stay authoritative.
    strength=out/'display_strength_10m.tif'
    if not strength.exists():
        a,b,c,d=area['study_bounds'];ref=gdal.Open(str(pre/'terrain/slope_10m.tif'))
        ds=gdal.GetDriverByName('GTiff').Create(str(strength),ref.RasterXSize,ref.RasterYSize,1,gdal.GDT_Float32,['TILED=YES','COMPRESS=DEFLATE'])
        ds.SetGeoTransform(ref.GetGeoTransform());ds.SetProjection(ref.GetProjection());ds.GetRasterBand(1).SetNoDataValue(-9999);ds.GetRasterBand(1).Fill(-9999)
        gpkg=ogr.Open(str(out/'registry.gpkg'));layer=gpkg.ExecuteSQL('SELECT * FROM lead_footprints ORDER BY score ASC')
        gdal.RasterizeLayer(ds,[1],layer,options=['ATTRIBUTE=score','ALL_TOUCHED=TRUE']);ds=None;gpkg=None
    # Providers must not mutate analytical GPKGs during subsequent review/save.
    for p in out.glob('*.gpkg'):p.chmod(0o444)
    app=QgsApplication([],False);app.initQgis();project=QgsProject.instance();project.setFileName(str(destination))
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:26910'));project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setTitle('KarstFinder | '+area['name']+' | Enhanced v001 — UNVALIDATED')
    root=project.layerTreeRoot()
    leads=root.addGroup('Enhanced leads • ordinal strength; points are features, not entrances')
    methods=root.addGroup('Independent method views • same retained registry; no data deleted')
    geology=root.addGroup('Geological zones + structure • coarse mapping; no route verified')
    measures=root.addGroup('Measured components • expand; experimental proxies labeled')
    imagery=root.addGroup('2023 native RGB/NIR • imagery cannot confirm rock type or openings')
    backdrop=root.addGroup('Study / terrain context')
    def add(layer,group,visible=False):
        if not layer.isValid():raise ValueError(layer.name())
        project.addMapLayer(layer,False);group.addLayer(layer).setItemVisibilityChecked(visible);return layer
    def vector(path,table,label,group,symbol=None,subset=None,visible=False):
        layer=QgsVectorLayer(f'{path}|layername={table}|option:IMMUTABLE=YES',label,'ogr');layer.setReadOnly(True)
        if subset:assert layer.setSubsetString(subset)
        if symbol:layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        return add(layer,group,visible)
    point=vector(out/'registry.gpkg','lead_points','ALL leads • exact continuous strength; no minimum cutoff',leads,visible=True)
    point.setRenderer(renderer());point.setCustomProperty('karstfinder/enhanced_filter_target',True)
    point.setDisplayExpression('"candidate_id" || \' | strength \' || round("evidence_strength",4) || \' | \' || "geo_class"')
    point.setAbstract('Color = ordinal evidence strength, not cave probability. Shape = feature type. Thick dark outline = uncertain/unknown geological support. All retained features visible. No entrance or access claim.')
    footprint=vector(out/'registry.gpkg','lead_footprints','Lead footprints • original and enhanced geometries retained',leads,QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#555555','outline_width':'.25'}))
    footprint.setCustomProperty('karstfinder/enhanced_filter_target',True)
    for kind in ['cliff','depression','hydrology','structure']:
        layer=vector(out/'registry.gpkg','lead_points',kind+' • inspect complete method view',methods,subset=f'"kind"=\'{kind}\'');layer.setRenderer(renderer())
    for name,label,expression in [('baseline','Preserved baseline lead coordinates','"baseline_object_id" <> \'\''),('carbonate','Mapped-carbonate support','"geo_class"=\'mapped_carbonate\''),('single','Single detection method • explicitly retained','"method_count"=1')]:
        layer=vector(out/'registry.gpkg','lead_points',label,methods,subset=expression);layer.setRenderer(renderer())
    zones=vector(out/'geology.gpkg','zones','Geological zones • source-unit footprints; not proximity clusters',geology,QgsFillSymbol.createSimple({'color':'255,255,255,0','outline_color':'#9b3d93','outline_width':'.7'}),visible=True)
    vector(out/'geology.gpkg','geology','All geological units • unknown is not unsuitable',geology,QgsFillSymbol.createSimple({'color':'255,255,255,0','outline_color':'#888888','outline_width':'.2'}))
    for table in ['faults','contacts']:
        vector(out/'geology.gpkg',table,'Mapped '+table+' • neutral context',geology,QgsLineSymbol.createSimple({'line_color':'#555555','line_style':'dash','line_width':'.3'}))
    vector(out/'geology.gpkg','orientations','Mapped bedding/structure observations • source attributes',geology,QgsMarkerSymbol.createSimple({'name':'cross','color':'#333333','size':'2'}))
    def raster(path,label,group,visible=False,colors=None):
        layer=QgsRasterLayer(str(path),label,'gdal')
        if colors:
            shaderfn=QgsColorRampShader(colors[0][0],colors[-1][0]);shaderfn.setColorRampType(QgsColorRampShader.Interpolated)
            shaderfn.setColorRampItemList([QgsColorRampShader.ColorRampItem(v,QColor(c),str(v)) for v,c in colors])
            if colors==list(STOPS):
                shaderfn.setSourceColorRamp(ramp());settings=QgsColorRampLegendNodeSettings();settings.setUseContinuousLegend(True);settings.setMinimumLabel('0 • weak');settings.setMaximumLabel('1 • strongest index');shaderfn.setLegendSettings(settings)
            shader=QgsRasterShader();shader.setRasterShaderFunction(shaderfn);render=QgsSingleBandPseudoColorRenderer(layer.dataProvider(),1,shader);render.setClassificationMin(colors[0][0]);render.setClassificationMax(colors[-1][0]);layer.setRenderer(render)
        return add(layer,group,visible)
    legend_layer=raster(strength,'Evidence strength • continuous 0–1 (display aggregate)',leads,colors=list(STOPS))
    legend_layer.setAbstract('10 m display raster uses maximum overlapping retained lead strength, all touched cells. Legend matches exact marker ramp; source footprint/points are authoritative.')
    for p in sorted((pre/'terrain').glob('*.tif')):
        if p.stem.endswith('_buffered'):continue
        label=p.stem.replace('_',' ')
        if label.startswith('line filter'):label='EXPERIMENTAL texture • '+label
        if 'modeled' in label or 'drainage' in label or 'divide' in label:label='MODELED terrain proxy • '+label
        raster(p,label,measures,colors=[(0,'#ffffff'),(1,'#de2d26')] if p.stem=='hydrologic_edge_contamination' else None)
    for p in sorted((pre/'pointcloud').glob('*.tif')):raster(p,'EXPERIMENTAL partial LPC • '+p.stem,measures)
    raster(out/'hydrological_setting_mask_10m.tif','Hydrological setting mask • not a spring/sink observation',measures)
    for name in ['depression_depth_1m','slope_1m','feature_quality_1m','source_epoch_1m']:
        raster(base/(name+'.tif'),name.replace('_',' '),measures)
    for name in ['ndvi','vegetation_mask','possible_exposed_surface_mask']:
        p=pre/'imagery'/(name+'.tif')
        if p.exists():raster(p,name.replace('_',' ')+' • screening proxy',imagery)
    rgb=pre/'imagery/rgbnir.tif'
    if rgb.exists():
        layer=raster(rgb,'RGB • native 0.6 m; NIR retained as band 4',imagery)
        render=QgsMultiBandColorRenderer(layer.dataProvider(),1,2,3)
        for channel in ['Red','Green','Blue']:
            enhancement=QgsContrastEnhancement(layer.dataProvider().dataType(1));enhancement.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum);enhancement.setMinimumValue(0);enhancement.setMaximumValue(255);getattr(render,'set'+channel+'ContrastEnhancement')(enhancement)
        layer.setRenderer(render)
    vector(out/'geology.gpkg','study_area','Approved study extent',backdrop,QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#333333','outline_style':'dash'}),visible=True)
    raster(base/'hillshade_1m.tif','Bare-earth hillshade • DEM cannot see overhangs',backdrop,True)
    overview=QgsRectangle(*area['study_bounds']);overview.scale(1.03)
    project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(overview,project.crs()))
    # Geologically selected detail, no outcome-based choice.
    carbonate=ogr.Open(str(out/'geology.gpkg'));ly=carbonate.GetLayerByName('geology');ly.SetAttributeFilter("geo_class='mapped_carbonate'");extents=[f.GetGeometryRef().GetEnvelope() for f in ly]
    if extents:
        detail=QgsRectangle(min(e[0] for e in extents),min(e[2] for e in extents),max(e[1] for e in extents),max(e[3] for e in extents));detail.scale(1.4)
        if detail.width()<500 or detail.height()<500:
            center=detail.center();half=max(250,detail.width()/2,detail.height()/2);detail=QgsRectangle(center.x()-half,center.y()-half,center.x()+half,center.y()+half)
    else:detail=overview
    previews=[]
    for name,extent in [('overview',overview),('carbonate_detail',detail)]:
        layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName('Enhanced '+name)
        layout.pageCollection().pages()[0].setPageSize('A4',QgsLayoutItemPage.Landscape)
        def text(value,x,y,w,h,size=9):
            item=QgsLayoutItemLabel(layout);item.setText(value);fmt=QgsTextFormat();fmt.setFont(QFont('DejaVu Sans',size));fmt.setSize(size);item.setTextFormat(fmt);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(w,h));return item
        text(area['name']+' | Enhanced v001',8,4,281,10,14)
        text('Unvalidated prospecting | All retained leads | Color = ordinal evidence strength, never cave probability',8,16,281,8,9)
        item=QgsLayoutItemMap(layout);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(8,28));item.attemptResize(QgsLayoutSize(210,161));item.setCrs(project.crs());item.setLayers([n.layer() for n in root.findLayers() if n.isVisible()]);item.setKeepLayerSet(True);item.zoomToExtent(extent)
        text('CONTINUOUS STRENGTH',225,28,65,8,10)
        legend=QgsLayoutItemLegend(layout);layout.addLayoutItem(legend);legend.setTitle('');legend.setAutoUpdateModel(False);legend.model().rootGroup().clear();legend_node=legend.model().rootGroup().addLayer(legend_layer);legend_node.setName('Strength index');legend.setSymbolHeight(20);legend.setSymbolWidth(6);legend.setLinkedMap(item);legend.setStyleFont(QgsLegendStyle.SymbolLabel,QFont('DejaVu Sans',8));legend.attemptMove(QgsLayoutPoint(225,39));legend.attemptResize(QgsLayoutSize(63,38))
        text('Triangle: cliff patch\nDiamond: depression\nCircle: drainage setting\nSquare: mapped intersection\n\nDark thick outline: uncertain\ngeology (separate from strength).\nMagenta: geological zone.\n\nNo entrance confirmed.\nNo route or access verified.\nUnknown geology is retained.\n\nUse Identify Features to read\nmeasurements and alternatives.\nLayer filters are reversible.',225,81,66,107,8)
        text('DNR geology 1:100,000 | USGS / PSLC terrain | NAD83 UTM 10N, metres | See registry manifests and Enhanced methodology',8,196,281,7,8)
        project.layoutManager().addLayout(layout)
        png=ROOT/f'docs/enhanced_v001/{area_id}_{name}.png';image=QgsLayoutExporter(layout).renderPageToImage(0,QSize(),140);assert image.save(str(png));previews.append(str(png.relative_to(ROOT)))
    assert project.write()
    point.saveNamedStyle(str(out/'exact_strength.qml'))
    report={'area':area_id,'project':str(destination.relative_to(ROOT)),'layer_count':len(project.mapLayers()),'lead_count':point.featureCount(),'all_leads_default_visible':True,'default_subset':point.subsetString(),'ramp_stops':STOPS,'color_expression':COLOR_EXPRESSION,'previews':previews,'layouts':['Enhanced overview','Enhanced carbonate_detail'],'private_layers':0}
    write_json(ROOT/f'docs/enhanced_v001/{area_id}_map.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('area',choices=config()['areas']);main(p.parse_args().area)
