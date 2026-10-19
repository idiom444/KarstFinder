#!/usr/bin/env python3
"""Persist a local-only validation project without changing any frozen prediction layer."""
import json,os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from osgeo import ogr,osr
from qgis.core import (QgsApplication,QgsProject,QgsVectorLayer,QgsMarkerSymbol,QgsFillSymbol,QgsSingleSymbolRenderer,
 QgsPalLayerSettings,QgsTextFormat,QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtGui import QColor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.freeze import verify_freeze
verify_freeze(ROOT);ogr.UseExceptions();osr.UseExceptions()
private=ROOT/'data/private/validation';gpkg=private/'validation.gpkg'
if gpkg.exists():gpkg.unlink()
s=osr.SpatialReference();s.ImportFromEPSG(4326);s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
t=osr.SpatialReference();t.ImportFromEPSG(26910);tx=osr.CoordinateTransformation(s,t)
d=ogr.GetDriverByName('GPKG').CreateDataSource(str(gpkg));points=d.CreateLayer('public_reference_points',t,ogr.wkbPoint);buffers=d.CreateLayer('assumed_uncertainty',t,ogr.wkbPolygon)
for layer in [points,buffers]:
 for name,typ in [('record_id',ogr.OFTString),('source_url',ogr.OFTString),('uncertainty_m',ogr.OFTReal),('accuracy_verified',ogr.OFTInteger),('interpretation',ogr.OFTString)]:layer.CreateField(ogr.FieldDefn(name,typ))
refs=json.loads((private/'references.geojson').read_text())
for feature in refs['features']:
 props=feature['properties'];geom=ogr.CreateGeometryFromJson(json.dumps(feature['geometry']));geom.Transform(tx)
 for layer,g in [(points,geom),(buffers,geom.Buffer(props['uncertainty_m'],48))]:
  f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(g)
  for k in ['record_id','source_url','uncertainty_m']:f[k]=props[k]
  f['accuracy_verified']=int(props['accuracy_verified']);f['interpretation']='Unverified crowd-map location; assumed radius is NOT measured accuracy';layer.CreateFeature(f)
region=d.CreateLayer('historical_regional_evidence',t,ogr.wkbMultiPolygon);region.CreateField(ogr.FieldDefn('interpretation',ogr.OFTString))
for f in json.loads((private/'historical_region.geojson').read_text())['features']:
 geom=ogr.CreateGeometryFromJson(json.dumps(f['geometry']));geom.Transform(tx);geom=ogr.ForceToMultiPolygon(geom)
 feat=ogr.Feature(region.GetLayerDefn());feat.SetGeometry(geom);feat['interpretation']='One section-level historical reference; no entrance point inferred';region.CreateFeature(feat)
d=None
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance();assert project.read(str(ROOT/'qgis/KarstFinder_Blind_v002.qgz'))
project.setTitle('KarstFinder | LOCAL PRIVATE validation | location accuracy unverified')
group=project.layerTreeRoot().insertGroup(0,'LOCAL PRIVATE validation — uncertain references')
for layername,title,symbol in [
 ('public_reference_points','Public mapped references • accuracy UNKNOWN',QgsMarkerSymbol.createSimple({'name':'cross2','color':'#e31a1c','size':'3','outline_width':'.4'})),
 ('assumed_uncertainty','100 m scenario • assumed, not confidence interval',QgsFillSymbol.createSimple({'color':'227,26,28,15','outline_color':'#e31a1c','outline_style':'dash','outline_width':'.4'})),
 ('historical_regional_evidence','Historical section-level evidence • one spatial unit',QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':'#6a3d9a','outline_width':'.5','outline_style':'dash'}))]:
 layer=QgsVectorLayer(f'{gpkg}|layername={layername}',title,'ogr');assert layer.isValid();layer.setRenderer(QgsSingleSymbolRenderer(symbol));project.addMapLayer(layer,False);group.addLayer(layer)
 if layername=='public_reference_points':
  labels=QgsPalLayerSettings();labels.fieldName='record_id';fmt=QgsTextFormat();fmt.setSize(8);fmt.setColor(QColor('#b00000'));labels.setFormat(fmt);layer.setLabeling(QgsVectorLayerSimpleLabeling(labels));layer.setLabelsEnabled(True)
path=private/'KarstFinder_Validation.qgz';project.setFileName(str(path));assert project.write();assert project.read(str(path))
invalid=[l.name() for l in project.mapLayers().values() if not l.isValid()];assert not invalid,invalid
report={'project':'data/private/validation/KarstFinder_Validation.qgz','persistent_local_layers':len(project.mapLayers()),'invalid_layers':invalid,
        'reference_count':len(refs['features']),'precise_entrance_references':0,'frozen_predictions_modified':False}
(ROOT/'docs/validation_qgis_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
