"""Small independent analytical checks against the actual GIS executables."""
import numpy as np
from osgeo import gdal, osr
from whitebox.whitebox_tools import WhiteboxTools


def test_packaged_gdal_slope_units(tmp_path):
    s=osr.SpatialReference();s.ImportFromEPSG(26910)
    p=tmp_path/'plane.tif';ds=gdal.GetDriverByName('GTiff').Create(str(p),51,51,1,gdal.GDT_Float32)
    ds.SetGeoTransform((600000,10,0,5260000,0,-10));ds.SetProjection(s.ExportToWkt())
    # 10 m vertical per 10 m east: exact 45 degree plane.
    ds.GetRasterBand(1).WriteArray(np.tile(np.arange(51)*10.,(51,1)));ds=None
    out=gdal.DEMProcessing('',str(p),'slope',format='MEM',scale=1.)
    np.testing.assert_allclose(out.ReadAsArray()[2:-2,2:-2],45,atol=1e-4)
    # A symmetric neighbourhood on a plane has zero deviation from mean.
    w=WhiteboxTools();w.set_verbose_mode(False)
    target=tmp_path/'dev.tif';assert w.dev_from_mean_elev(str(p),str(target),filterx=21,filtery=21,callback=lambda _:None)==0
    arr=gdal.Open(str(target)).ReadAsArray()
    np.testing.assert_allclose(arr[15:-15,15:-15],0,atol=.05)
