"""Optional reviewed map-plate georeferencing; no automatic lithology claims."""
import math
import numpy as np
from osgeo import gdal
from .common import safe_path,sha,write_json


def georeference(spec,output):
    """Affine GCP transform with inspectable residuals. Inputs stay untouched.

    GCP pairs are [pixel,line,UTM_easting,UTM_northing]. Publication citation,
    scale and independent geological uncertainty must be supplied by reviewer.
    This helper does not scrape reports or digitize an unreviewed plate.
    """
    for key in ['source','citation','scale_denominator','geological_uncertainty_m','gcps']:
        if key not in spec:raise ValueError('Missing plate provenance: '+key)
    source=safe_path(spec['source']);output=safe_path(output)
    if output.exists():raise FileExistsError(output)
    points=np.asarray(spec['gcps'],dtype=float)
    if points.ndim!=2 or points.shape[1]!=4 or len(points)<4 or not np.isfinite(points).all():raise ValueError('At least four finite control points required')
    matrix=np.column_stack([np.ones(len(points)),points[:,:2]])
    if np.linalg.matrix_rank(matrix)<3:raise ValueError('Collinear control points')
    coef=np.linalg.lstsq(matrix,points[:,2:],rcond=None)[0]
    errors=np.linalg.norm(matrix@coef-points[:,2:],axis=1)
    gcps=[gdal.GCP(float(x),float(y),0,float(px),float(py)) for px,py,x,y in points]
    src=gdal.Translate('',str(source),format='MEM',GCPs=gcps,outputSRS='EPSG:26910')
    output.parent.mkdir(parents=True,exist_ok=True)
    gdal.Warp(str(output),src,dstSRS='EPSG:26910',polynomialOrder=1,resampleAlg='near',creationOptions=['COMPRESS=DEFLATE','TILED=YES'])
    report={**spec,'source_sha256':sha(source),'output_sha256':sha(output),'gcp_fit_rmse_m':float(np.sqrt(np.mean(errors**2))),'gcp_max_residual_m':float(errors.max()),'note':'GCP fit residual is not map accuracy or independent georeferencing validation; geology remains reviewer interpreted.'}
    write_json(output.with_suffix('.provenance.json'),report);return report
