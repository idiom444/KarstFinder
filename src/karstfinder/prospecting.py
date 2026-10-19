"""Explicit lithology adapter for the unchanged feature-scoring implementation."""
import numpy as np
from scipy import ndimage
from osgeo import gdal, ogr
from .gis import memory


def geology_codes(ref, context, marble_units, mixed_units=('JTRmt(e)',)):
    """Same category precedence and GDAL rasterization as the archived model.

    Only the map-unit vocabulary is parameterized: TRmb(e) at Marble Peak is
    mapped to the existing marble class instead of silently receiving zero.
    """
    source = ogr.Open(str(context)); layer = source.GetLayerByName('bedrock')
    dest = memory(np.zeros((ref.RasterYSize, ref.RasterXSize), dtype='uint8'), ref)
    classes = [(3, unit) for unit in mixed_units] + [(4, 'wtr'), (5, 'Qta'), (6, 'Qls')]
    classes += [(1, unit) for unit in marble_units]
    for code, unit in classes:
        layer.SetAttributeFilter("MAP_UNIT_100K = '" + unit.replace("'", "''") + "'")
        gdal.RasterizeLayer(dest, [1], layer, burn_values=[code])
    codes = dest.ReadAsArray()
    if not np.any(codes == 1):
        raise ValueError('No mapped marble pixels in study; do not invent a contact-distance field')
    return codes, ndimage.distance_transform_edt(codes != 1).astype('float32')
