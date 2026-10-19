import numpy as np
from osgeo import gdal,osr
from whitebox.whitebox_tools import WhiteboxTools

gdal.UseExceptions();osr.UseExceptions()


def test_closed_depression_depth_has_known_spill_level(tmp_path):
    # Flat 100 m exterior, enclosed 3x3 98 m basin; depth must be exactly 2 m.
    z=np.full((21,21),100,dtype='float32');z[9:12,9:12]=98
    p=tmp_path/'bowl.tif';ds=gdal.GetDriverByName('GTiff').Create(str(p),21,21,1,gdal.GDT_Float32)
    ds.SetGeoTransform((600000,1,0,5260000,0,-1));s=osr.SpatialReference();s.ImportFromEPSG(26910);ds.SetProjection(s.ExportToWkt());ds.GetRasterBand(1).WriteArray(z);ds=None
    w=WhiteboxTools();w.set_verbose_mode(False);out=tmp_path/'depth.tif'
    assert w.fill_depressions_wang_and_liu(str(p),str(out),fix_flats=False,callback=lambda _:None)==0
    a=gdal.Open(str(out)).ReadAsArray()-z;np.testing.assert_allclose(a[9:12,9:12],2,atol=1e-4)
    np.testing.assert_allclose(a[:5],0,atol=1e-4)


def test_open_notch_is_not_a_closed_depression(tmp_path):
    z=np.full((21,21),100,dtype='float32');z[9:12,9:12]=98;z[10,11:]=98
    p=tmp_path/'notch.tif';ds=gdal.GetDriverByName('GTiff').Create(str(p),21,21,1,gdal.GDT_Float32)
    ds.SetGeoTransform((600000,1,0,5260000,0,-1));s=osr.SpatialReference();s.ImportFromEPSG(26910);ds.SetProjection(s.ExportToWkt());ds.GetRasterBand(1).WriteArray(z);ds=None
    w=WhiteboxTools();w.set_verbose_mode(False);out=tmp_path/'depth.tif'
    assert w.fill_depressions_wang_and_liu(str(p),str(out),fix_flats=False,callback=lambda _:None)==0
    np.testing.assert_allclose((gdal.Open(str(out)).ReadAsArray()-z)[9:12,9:12],0,atol=1e-4)
