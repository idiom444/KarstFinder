"""Thin GDAL helpers for persistent standard rasters; no custom terrain algorithms."""
from pathlib import Path
import hashlib
import numpy as np
from osgeo import gdal, ogr

gdal.UseExceptions();ogr.UseExceptions()
CO=['COMPRESS=DEFLATE','TILED=YES','BIGTIFF=IF_SAFER']


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def array(path,dtype='float32'):
    ds=gdal.Open(str(path));arr=ds.ReadAsArray().astype(dtype)
    nd=ds.GetRasterBand(1).GetNoDataValue()
    if nd is not None and np.issubdtype(arr.dtype,np.floating):arr[arr==nd]=np.nan
    return arr


def raster(path,arr,ref,nodata=-9999,dtype=gdal.GDT_Float32):
    if isinstance(ref,(str,Path)):ref=gdal.Open(str(ref))
    ds=gdal.GetDriverByName('GTiff').Create(str(path),arr.shape[1],arr.shape[0],1,dtype,CO)
    ds.SetGeoTransform(ref.GetGeoTransform());ds.SetProjection(ref.GetProjection())
    band=ds.GetRasterBand(1);band.SetNoDataValue(nodata)
    band.WriteArray(np.where(np.isfinite(arr),arr,nodata));ds=None


def memory(arr,ref,dtype=gdal.GDT_Byte):
    ds=gdal.GetDriverByName('MEM').Create('',arr.shape[1],arr.shape[0],1,dtype)
    ds.SetGeoTransform(ref.GetGeoTransform());ds.SetProjection(ref.GetProjection());ds.GetRasterBand(1).WriteArray(arr)
    return ds


def polygon_layer(mask,ref):
    src=memory(mask.astype('uint8'),ref)
    ds=ogr.GetDriverByName('MEM').CreateDataSource('')
    layer=ds.CreateLayer('objects',ref.GetSpatialRef(),ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('present',ogr.OFTInteger))
    gdal.Polygonize(src.GetRasterBand(1),src.GetRasterBand(1),layer,0,[])
    return ds,layer
