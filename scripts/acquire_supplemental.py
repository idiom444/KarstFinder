#!/usr/bin/env python3
"""Optional imagery and acquisition QA, all free of cave-location labels."""
import json
from pathlib import Path
from acquire import fetch, records, ROOT

manifest_path=ROOT/'docs/acquisition_manifest.json'
manifest=json.loads(manifest_path.read_text())
base='https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/metadata/WA_KingCounty_2021_B21/WA_KingCo_3_2021/reports/'
for name in ['USGS_WA_KingCo_3_2021_FINAL_DEM_Report.txt','WA_KingCounty_2021_B21_Lidar_Delivery_2_Technical_Data_Report.pdf']:
    fetch(base+name,name,binary=True)
u='https://imagery-public.watech.wa.gov/arcgis/rest/services/NAIP/Statewide_NAIP_2017_3ft_4band_wsps_83h_img/ImageServer'
fetch(u,'naip_metadata.json',{'f':'json'})
response=fetch(u+'/exportImage','naip_export.json',{'f':'json','bbox':'617000,5253500,623000,5258500','bboxSR':26910,
    'imageSR':26910,'size':'3000,2500','format':'tiff','pixelType':'U8','bandIds':'0,1,2','interpolation':'RSP_BilinearInterpolation'})
fetch(json.loads(response.read_text())['href'],'naip2017_rgb_2m.tif',binary=True)
manifest=[r for r in manifest if r['path'] not in {x['path'] for x in records}]+records
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
