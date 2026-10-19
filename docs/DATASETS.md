# Datasets acquired for the blind baseline

Acquired 2026-10-19. [acquisition_manifest.json](acquisition_manifest.json) records
exact requests, local paths, byte counts and SHA-256 hashes; source datasets
remain outside Git under ignored `data/raw/`. [data_quality.json](data_quality.json)
records observed coverage, raster grids and survey differences.

| Dataset | Source / acquisition | Resolution, CRS and dates | Limitations / use |
|---|---|---|---|
| USGS standard 1 m bare-earth LiDAR DEM: King County | [National Map API](https://tnmaccess.nationalmap.gov/api/v1/products); project `WA_KingCounty_2021_B21`, tiles `x61y526` and `x62y526`; exact S3 URLs in manifest | 1 m pixels, EPSG:26910, NAVD88 elevation metres; 2021 survey, published March 2023 | 2021 alone covered 70.85% of study at 10 m. Prefer newest valid data. 1 m spacing is not 1 m detection accuracy. |
| USGS standard 1 m bare-earth LiDAR DEM: Eastern Cascades | Same API; project `WA_EasternCascades_2019_B19`, tiles `x61y526` and `x62y526` | 1 m, EPSG:26910, NAVD88 metres; 2019 acquisition label, published September 2022 | Fills east side, yielding 100% valid study and processing buffer. Detailed 2019 acquisition/accuracy report not yet reviewed. |
| Geologic units | [DNR 100K WA GeMS service](https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer/11) | 1:100,000 compilation; service native EPSG:2927 (US survey feet), queried directly in EPSG:26910 | Marble PMmb(e) distinguished from mixed melange JTRmt(e). Small carbonate lenses and contact locations unresolved. 10 m rasterization does not improve map accuracy. Feature-specific unit-identification confidence retained. |
| Contacts, faults, orientations | Same service, layers 9, 7 and 1; field allowlist in acquisition script | Same compilation; exported/projected to EPSG:26910; agency location-confidence attributes retained | Context only in baseline, no distance bonus. Not a complete fracture inventory. Geometric detail and mapped traces cannot resolve entrance-scale structure. |
| NAIP 2017 RGB imagery | [Washington state public image service](https://imagery-public.watech.wa.gov/arcgis/rest/services/NAIP/Statewide_NAIP_2017_3ft_4band_wsps_83h_img/ImageServer) | Native 3 ft (0.9144 m), EPSG:2927; 2017 mosaic; local three-band export is **2 m**, EPSG:26910 | Older than DEMs; canopy, shadow, snow and orthorectification obscure faces/overhangs. Only visual context, no entrance detection. No site-specific horizontal accuracy established. |
| Ridge geographic anchor | [USGS GNIS landforms query](https://carto.nationalmap.gov/arcgis/rest/services/geonames/MapServer/5) | Exact `gaz_name='Cave Ridge'`, Washington; GNIS 1517515, class Ridge; WGS84 | Representative geographic point, not ridge boundary, elevation control or cave location. |
| King County technical report | USGS public S3 project metadata, exact URL in manifest | Delivery 2 report, 2022; QL1 lidar, acquired Apr 1–14 and Jun 24–Sep 7, 2021 | Acquisition-wide QA rather than ridge-specific accuracy. Native contractor grids are feet; downloaded USGS standard tiles are metres. |

All downloaded USGS 3DEP products state public-domain usage in their catalog
records. DNR's service credits Washington Geological Survey; retain attribution
and agency disclaimers. A separate redistribution license was not established
from the layer metadata; do not assume public-domain status for all state data.
NAIP is publicly served, but the export metadata did not supply complete
redistribution terms; retain USDA/NAIP and state service attribution and check
terms before redistribution. All raw data remain local. No licensed third-party
basemap or cave-location dataset has been added.

## Positional accuracy and completeness

The King County Delivery 2 report (§Results, pp.19–25) reports bare-earth DEM
nonvegetated vertical accuracy of 0.082 m at 95% confidence (25 checkpoints),
vegetated vertical accuracy 0.130 m at the 95th percentile (29 checkpoints), and
calculated horizontal accuracy 0.23 m at 95%. These are acquisition-level
statistics; they are **not measured entrance-localization accuracy on cliffs**.
Snow, forest classification, steep slopes, void interpolation and survey seams
can produce much larger local errors.

On the common 10 m grid, there are 28,812 overlap cells. Observed 2021 minus 2019
median residual is −0.3468 m; the 95th percentile absolute residual is 5.1423 m.
These observations are not an estimate of either survey's independent accuracy.
Steep slope resampling, partial-cell coverage, surface changes and registration
could contribute. Do not correct elevations by a single offset without further
investigation. Quantify seam proximity and native-resolution artifacts before
M3; source_epoch_10m.tif preserves survey identity.

The study and 1,100 m processing buffer have full valid 10 m DEM coverage after
mosaicking. Native 1 m voids still need separate feature-stage QA. A 10 m cell can
be valid if only some original pixels were valid, so this landscape coverage
statistic must not be used as proof of complete native point-cloud observation.
The source epochs and terrain products are available as separate QGIS layers.

## Remaining acquisition work

DNR's LiDAR portal returned HTTP 403, and its site3 Public_Lidar directory required
a token. Public USGS standard DEM downloads were a practical authoritative
alternative. The current DNR public geology directory exposed a 100K GeMS
service; finer 1:24,000 / intermediate-scale map coverage was not established
in this session. Evaluate their carbonate/contact detail without opening cave
annotations or cave-bearing historical publications. Do not claim that this
compilation is the highest-resolution geological source possible.

Hydrography and hydrologically conditioned derivatives were not acquired yet.
Next use an authoritative stream network or explicitly modeled drainage, while
keeping maps free of local cave labels and spring inventories that could leak
entrance information. No land-manager access analysis or fieldwork is proposed.
