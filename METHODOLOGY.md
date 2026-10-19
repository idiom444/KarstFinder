# Implemented baseline: blind_v001

Stage: **exploratory blind, unfrozen**. This implements a landscape baseline,
not the full initial experiment. No training labels, supervised learning,
entrance detector, cave confirmation or validation is implemented yet.

## Geographic frame and data preparation

GNIS ridge record 1517515 anchors the study independently of cave information.
The 6 km × 5 km rectangular envelope is EPSG:26910 bounds
`617000,5253500,623000,5258500`, with a 1,100 m processing buffer. This covers
the ridge and adjacent slopes without tracing any known cave-bearing area.
All horizontal distances and areas use NAD83 / UTM zone 10N metres.
USGS standard 1 m elevation is NAVD88 metres, despite an empty raster-band unit
field. Supplier-native technical reports describe feet; do not apply that unit
to the standardized USGS tiles. No vertical datum transformation is applied.

GDAL mosaics 2019 Eastern Cascades then 2021 King County, giving the newest valid
pixel priority. Original tiles have 6 m margins; the output has a common 1 m
grid. A 10 m arithmetic-average DEM supports landscape derivatives. An epoch
raster records 2021 availability in each 10 m cell, with 2019 as fallback.
Cells on a seam may average native pixels from both surveys; this categorical
layer does not measure their native pixel proportions. Overlap elevation residuals
are measured, not corrected/feathered. Remaining missing data stay NoData.
Geology, contacts, faults and orientations are clipped with OGR and persisted
in GeoPackage. Faults/contacts are contextual only in this baseline; no causal
benefit from proximity is assumed without evidence.

## Terrain and lithology indices

GDAL Horn slope is in degrees; aspect is azimuth, clockwise from north, with
flat cells NoData. Hillshade is visualization only. WhiteboxTools
DevFromMeanElev uses square widths of 21, 61 and 201 cells at 10 m, corresponding
to 210, 610 and 2,010 m footprints. DEV is `(z − local_mean) / local_sd`.
The paper's particular standardization and this local DEV implementation are
related, but this is an adaptation, not an exact reproduction of its classifier.

For each scale, `abs(DEV) <= 0.5` contributes one mid-slope vote. Define
`M = votes / 3`, `E = clip((slope_deg − 15) / 30, 0, 1)` and
`T = 0.6 M + 0.4 E`. Exposure E is only a slope proxy, not observed bare rock.
The geological evidence index G is 1 for mapped marble PMmb(e), 0.35 for mixed
melange JTRmt(e), and 0 for other mapped units. Mixed melange is known to include
some marble but its distribution is unresolved. A zero means no mapped
carbonate evidence, not carbonate absence. `C = G × T` is an **ordinal
hypothesis index**; its decimals are not probabilities. All weights/thresholds
are untrained assumptions in configs/blind_v001.json.

To avoid invalid neighbourhood statistics, a cell is scored only when its entire
201×201 elevation neighbourhood is valid; SciPy minimum filtering checks this
binary mask. Cropping occurs after buffered derivatives. Individual DEV, slope,
aspect, geology, mid-slope votes, exposure, terrain and combined maps are retained.

## Preliminary landscape areas and ranking

GDAL polygonizes cells with `C >= 0.5`, with four-neighbour connectivity and a
minimum component area of 1,000 m². This threshold means mixed melange remains
visible in C but cannot generate a ranked area in this first baseline. The
candidate layer is therefore deliberately conservative about mapped carbonate,
with substantial omission risk outside marble polygons.

Rank polygons by descending mean C, then descending area, then representative
point easting/northing for deterministic ties. Each area records mean/max C,
terrain/geology components, slope, exposure and vote means, area, representative
point coordinates in projected/WGS84 systems, evidence, uncertainty and
alternative explanations. Representative points are inside polygons and **are
not proposed entrance coordinates**. The CSV and GeoPackage preserve full scores.
Glacial landforms, talus, landslide scars and non-karst exposures remain plausible.

## Required later experiment and validation

M3 must add a complementary native-resolution surface-feature detector, evaluate
scale/threshold sensitivity without cave labels, and finalize the blind ranking.
Archive every input/configuration/component/output with hashes plus a clean
implementation Git commit before marking a freeze. The current run manifest
explicitly says `frozen: false`. Do not acquire local cave validation yet.

After freezing, use independently sourced, permitted local validation records
with uncertainty geometry and provenance. Pre-register recall at 1/5/10/20% area,
recall/area prediction gain, and Kvamme gain `1 − area_fraction/recall` where
recall > 0. Report recall-zero cases explicitly. Compare against uniform sampling
within comparable mapped carbonate and a geology-only baseline; use spatial
blocks and location-uncertainty sensitivity. Entrance distance tolerances must
follow source accuracy and cannot be enlarged post hoc. Historical inventory
incompleteness and exploration bias preclude treating unlisted areas as absences.
