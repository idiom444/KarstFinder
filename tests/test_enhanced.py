"""Independent invariants, synthetic geometry and established terrain checks."""
import json
import numpy as np
import pytest
from osgeo import ogr,gdal,osr
from karstfinder.enhanced.scoring import STOPS,color,combine,morphology
from karstfinder.enhanced.geology import classification,context_for
from karstfinder.enhanced.registry import Grid,components,geom_key
from karstfinder.gis import raster


def test_exact_continuous_colors():
    assert [color(v) for v,c in STOPS]==[c for v,c in STOPS]
    assert color(.125)=='#402a70'
    assert len({color(v) for v in np.linspace(0,1,1001)})>400
    for v in [-1,1.01,np.nan]:
        with pytest.raises(ValueError):color(v)


def test_missing_zero_and_correlated_support():
    score,parts,coverage=combine({'terrain_hydrology_pointcloud':{'cliff':.4,'same_dem_again':.4}})
    assert score==pytest.approx(.28)
    assert parts['geology_structure'] is None and not coverage['geology_structure']
    _,parts,cov=combine({'geology_structure':{'known_noncarbonate':0}})
    assert parts['geology_structure']==0 and cov['geology_structure']
    assert combine({})[0]==0
    with pytest.raises(ValueError):combine({'geology_structure':{'bad':float('nan')}})


def test_robust_residual_does_not_depend_on_one_extreme():
    values=np.zeros(100);values[0]=-100
    assert morphology('cliff',0,[float(np.quantile(values,.1))])==.2
    assert morphology('depression',1.5,[])==.5


def fixture_grid(tmp_path):
    p=tmp_path/'grid.tif';s=osr.SpatialReference();s.ImportFromEPSG(26910)
    d=gdal.GetDriverByName('MEM').Create('',10,10,1,gdal.GDT_Float32);d.SetGeoTransform([0,1,0,10,0,-1]);d.SetProjection(s.ExportToWkt())
    values=np.arange(100,dtype='float32').reshape(10,10);values[0,0]=np.nan;raster(p,values,d)
    return p,d


def test_exact_footprints_and_missing_data(tmp_path):
    p,d=fixture_grid(tmp_path);geom=ogr.CreateGeometryFromWkt('POLYGON((0 8,2 8,2 10,0 10,0 8))')
    summary=Grid(p).summary(geom)
    assert summary['valid_pixels']==3 and summary['mean']==pytest.approx(22/3)
    assert Grid(tmp_path/'missing.tif').summary(geom) is None
    outside=ogr.CreateGeometryFromWkt('POLYGON((20 20,22 20,22 22,20 22,20 20))')
    assert Grid(p).summary(outside) is None


def test_components_preserve_large_and_four_neighbor(tmp_path):
    p,d=fixture_grid(tmp_path);mask=np.zeros((10,10),bool);mask[:5,:5]=1;mask[5,5]=1
    geoms=components(mask,d,1)
    assert sorted(g.GetArea() for g in geoms)==[1,25]
    assert len(components(mask,d,2))==1
    assert geom_key('cliff',geoms[0])!=geom_key('depression',geoms[0])


def test_geology_unknown_not_unsuitable():
    assert classification('unmapped')==('unknown',None)
    assert classification('PMmb(e)')==('mapped_carbonate',1.)
    assert classification('Oit','granodiorite')[0]=='mapped_noncarbonate'
    geom=ogr.CreateGeometryFromWkt('POLYGON((0 0,1 0,1 1,0 1,0 0))')
    assert context_for(geom,[])['geology_component'] is None
    assert context_for(geom,[])['geo_class']=='unknown'


def test_whitebox_relative_position_on_flat_fixture(tmp_path):
    from whitebox.whitebox_tools import WhiteboxTools
    p,d=fixture_grid(tmp_path);raster(p,np.full((10,10),20,dtype='float32'),d)
    w=WhiteboxTools();w.set_verbose_mode(False)
    output=tmp_path/'relative.tif'
    assert w.relative_topographic_position(str(p),str(output),filterx=3,filtery=3,callback=lambda _:None)==0
    values=gdal.Open(str(output)).ReadAsArray()
    valid=values[values!=-32768]
    # Flat terrain has no relative position; Whitebox reports neutral zero.
    assert np.allclose(valid,0,equal_nan=False)


def test_zero_encoded_whitebox_mask_is_not_missing(tmp_path):
    p,d=fixture_grid(tmp_path);raster(p,np.zeros((10,10),dtype='float32'),d,nodata=0)
    geom=ogr.CreateGeometryFromWkt('POLYGON((0 8,2 8,2 10,0 10,0 8))')
    assert Grid(p).summary(geom) is None
    assert Grid(p,nodata=None).summary(geom)['mean']==0


def test_reversible_filters_quote_and_validate():
    from karstfinder.enhanced.filters import subset
    assert subset()==''
    assert "O''Brien" in subset(zone="O'Brien")
    assert 'LIKE' in subset(method='terrain_cliff')
    with pytest.raises(ValueError):subset(availability='unknown')
    with pytest.raises(ValueError):subset(method="x' OR 1=1")


def test_qgis_exact_continuous_expression():
    import os
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from qgis.core import QgsApplication,QgsExpression,QgsExpressionContext,QgsExpressionContextScope,QgsSymbolLayerUtils
    from qgis.PyQt.QtGui import QColor
    from karstfinder.enhanced.style import ramp,COLOR_EXPRESSION
    app=QgsApplication.instance()
    if not app:app=QgsApplication([],False);app.initQgis()
    r=ramp()
    for value in [v for v,c in STOPS]+[.01,.125,.333,.678,.927]:
        expression=QgsExpression(COLOR_EXPRESSION.replace('"evidence_strength"',str(value)))
        result=expression.evaluate()
        q=QgsSymbolLayerUtils.decodeColor(result)
        assert not expression.hasEvalError() and q.isValid()
        assert q.name()==color(value)
        assert r.color(value).name()==color(value)


def test_plate_affine_gcps_and_provenance(tmp_path,monkeypatch):
    from karstfinder.enhanced import plates
    monkeypatch.setattr(plates,'safe_path',lambda p:tmp_path/p)
    p,d=fixture_grid(tmp_path)
    spec={'source':'grid.tif','citation':'Synthetic fixture only','scale_denominator':10000,'geological_uncertainty_m':5,
          'gcps':[[0,0,600000,5300000],[10,0,600010,5300000],[0,10,600000,5299990],[10,10,600010,5299990]]}
    report=plates.georeference(spec,'georef.tif')
    assert report['gcp_fit_rmse_m']<1e-6
    assert gdal.Open(str(tmp_path/'georef.tif')).GetSpatialRef().GetAuthorityCode(None)=='26910'
    with pytest.raises(FileExistsError):plates.georeference(spec,'georef.tif')


def test_pdal_plane_normals_vertical_units_and_bounded_crop(tmp_path,monkeypatch):
    import shutil
    if not shutil.which('pdal'):pytest.skip('Optional PDAL not installed')
    from karstfinder.enhanced import pointcloud
    monkeypatch.setattr(pointcloud,'ROOT',tmp_path)
    csvpath=tmp_path/'plane.csv'
    with csvpath.open('w') as stream:
        stream.write('X,Y,Z,Classification\n')
        for i in range(40):
            for j in range(40):stream.write(f'{1379100+3*i},{992560+3*j},{1000+.3*i},2\n')
    source=tmp_path/'plane.laz'
    pointcloud.run_pipeline(tmp_path/'fixture.json',[{'type':'readers.text','filename':str(csvpath),'separator':','},{'type':'writers.las','filename':str(source),'a_srs':'EPSG:2927+6360'}])
    s=osr.SpatialReference();s.ImportFromEPSG(2927);u=osr.SpatialReference();u.ImportFromEPSG(26910)
    tx=osr.CoordinateTransformation(s,u);x,y,_=tx.TransformPoint(1379158.5,992618.5)
    out=tmp_path/'products';out.mkdir()
    report=pointcloud.process(source,out,[x-30,y-30,x+30,y+30])
    assert report['ground_points']==1600
    assert report['vertical_conversion_to_m']==pytest.approx(1200/3937)
    ds=gdal.Open(str(out/'normal_z.tif'));values=ds.ReadAsArray();values=values[values!=-9999]
    assert np.median(values)==pytest.approx(1/np.sqrt(1.01),abs=.005)
    ds=gdal.Open(str(out/'ground_return_count.tif'));values=ds.ReadAsArray();assert values[values!=-9999].sum()==1600


def test_ground_return_bins_are_not_geometry_coverage(tmp_path):
    # Empty PDAL count bins are valid measured zeros, but contain no sampled
    # ground surface. They must not become normal/curvature evidence.
    p,d=fixture_grid(tmp_path);raster(p,np.zeros((10,10),dtype='float32'),d,nodata=-9999)
    geom=ogr.CreateGeometryFromWkt('POLYGON((0 8,2 8,2 10,0 10,0 8))')
    summary=Grid(p).summary(geom)
    assert summary is not None and not (summary['max'] or 0)>0


def test_geology_acquisition_gap_uses_preserved_polygons(tmp_path,monkeypatch):
    from karstfinder.enhanced import geology
    monkeypatch.setattr(geology,'ROOT',tmp_path)
    monkeypatch.setattr(geology,'safe_path',lambda p:tmp_path/p)
    processed=tmp_path/'baseline';processed.mkdir()
    ds=ogr.GetDriverByName('GPKG').CreateDataSource(str(processed/'context.gpkg'))
    s=osr.SpatialReference();s.ImportFromEPSG(26910);layer=ds.CreateLayer('bedrock',s,ogr.wkbPolygon)
    for name,kind in [('OBJECTID',ogr.OFTInteger),('MAP_UNIT_100K',ogr.OFTString),('MAP_UNIT_100K_ID_CONFIDENCE',ogr.OFTString)]:layer.CreateField(ogr.FieldDefn(name,kind))
    f=ogr.Feature(layer.GetLayerDefn());f.SetGeometry(ogr.CreateGeometryFromWkt('POLYGON((0 0,10 0,10 10,0 10,0 0))'));f['OBJECTID']=1;f['MAP_UNIT_100K']='PMmb(e)';f['MAP_UNIT_100K_ID_CONFIDENCE']='certain';layer.CreateFeature(f);ds=None
    records=geology.build('fixture',{'raw_dir':'missing','baseline_processed':'baseline','study_bounds':[0,0,10,10]},tmp_path/'new.gpkg')
    assert len(records)==1 and records[0][0]['geo_class']=='mapped_carbonate'
    assert records[0][0]['source_ref']=='baseline/context.gpkg#OBJECTID=1'
    assert records[0][0]['lithology_name']==''  # no invented unit description
