# Scientific reading — 2026-10-19

## Cuthbertson et al. (2021)

[Paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0245170),
DOI 10.1371/journal.pone.0245170, Methods §§3.2–3.6 and evaluation discussion.

The 2018 approach intersected carbonate units with unsupervised slope-position
classification. It used standardized TPI at 5, 10 and 50 km windows on a 35 m
ASTER DEM, counted mid-slope memberships between −0.5 and +0.5, and summarized
regional density. The 2019 minimum-distance classifier used 77 surveyed features,
200 m buffers, scaled terrain variables and a carbonate mask. The authors
explicitly acknowledge that evaluation reused most training observations.

Transfer decision: retain lithology-first reasoning and multiscale position,
but use 210, 610 and 2,010 m windows on 10 m averaged LiDAR for this small ridge.
These scales are exploratory assumptions. Broad regional windows and 200 m
entrance tolerances would obscure the local question. A mid-slope landscape is
not evidence of an individual opening. Model-guided survey also introduces
ascertainment bias; later evaluation must separate training and held-out data.

## Blitch, Sovie & Tobin (2023)

[Publisher](https://digitalcommons.usf.edu/ijs/vol52/iss2/2/),
DOI 10.5038/1827-806X.52.2.2455. Full methods read from the
[author-uploaded paper](https://www.researchgate.net/publication/372661234_Predictive_modeling_of_cave_entrance_locations_relationships_between_surface_and_subsurface_morphology)
when publisher PDF requests returned HTTP 403.

The study fit presence-only MaxEnt models in three Kentucky regions using cave
records and geology, elevation, slope, aspect and distances to karst/hydrologic
and structural features. Predictors were rasterized to a common elevation grid;
implementation used R/dismo. Model fit was assessed with AUC and predictor
importance/response curves. Sinkhole and spring proximity were prominent.
The methods text inspected does not establish an independently held-out spatial
validation design or fully specify background sampling and regularization.

Transfer decision: no MaxEnt in the blind baseline. Local presence labels are
withheld, and Kentucky's epigenic karst relationships need testing in glaciated,
metamorphosed, structurally disrupted alpine rock. Presence/background AUC and
correlation are insufficient evidence of entrance localization or calibrated
existence probability. Future training needs explicit backgrounds, spatial
blocks, regularization, exploration-bias controls and a separate validation set.

## GIS implementations

[GDAL DEMProcessing / gdaldem](https://gdal.org/en/stable/programs/gdaldem.html)
provides Horn slope, aspect and hillshade; slope is run in projected metres with
explicit unit ratio 1. WhiteboxTools
[DevFromMeanElev](https://jblindsay.github.io/wbt_book/available_tools/geomorphometric_analysis.html#DevFromMeanElev)
provides local elevation departure normalized by neighbourhood standard
deviation. Its square kernel width is in cells. We use this established tool
rather than substituting GDAL's fixed 3×3 raw TPI for multiscale standardized TPI.
The installed binary is 2.4.0, separately from Python wrapper 2.3.6.

## Next methods to investigate

Use established depression-fill/depth tools for a complementary surface-feature
approach on native 1 m elevation. Compare depression size/depth and cliff exposure,
review acquisition seams and DEM artifacts, and assess glacial/talus alternatives.
Do not equate a filled depression with a sinkhole or a sinkhole with an entrance.
Consider unsupervised terrain clustering only if it provides interpretable,
measurably different evidence; cluster labels have no intrinsic cave meaning.

## Pre-freeze source record

Only the ridge's exact GNIS feature record was queried for geographic anchoring.
No local cave descriptions, inventories, photographs, entrance maps or entrance
coordinates were requested. DNR map-unit descriptions for marble and mixed
melange were screened automatically before display for sentences mentioning
caves/entrances. Only lithological text was used. Downloads for modelling use
an explicit attribute allowlist; arbitrary unit notes and generic point layers
are excluded. Labeled topographic maps were not inspected. No validation had
begun at that stage. Validation sources were acquired only after the v002 freeze;
see docs/VALIDATION_REPORT.md for the later source-quality assessment.

## Complementary feature analysis and validation controls (v002)

Whitebox's [hydrology manual](https://jblindsay.github.io/wbt_book/available_tools/hydrological_analysis.html)
describes depression depth as filled minus original elevation. Synthetic
flat-bottom tests, rather than manual claims, selected the functioning Wang–Liu
implementation in the installed binary. Fixing drainage flats would create an
artificial gradient in measured pit depth, so those workflows are separate.

[Wall, Doctor & Terziotti (2015), USGS record](https://pubs.usgs.gov/publication/70175692)
identifies bridge/culvert barriers as a source of false filled depressions.
The [2024 USGS depression assessment](https://pubs.usgs.gov/publication/sir20245134/full)
also examines threshold-dependent false positives/negatives and numerical error
propagation. These support retaining thresholds and alternative origins as
uncertainties; their regional threshold/error estimates are not transferred here.

[SciPy kmeans2 documentation](https://scipy.github.io/devdocs/reference/generated/scipy.cluster.vq.kmeans2.html)
provides seeded k-means++ initialization. Six terrain clusters are descriptive,
without cave labels or a presumed favorable class. Reproducibility records the
seed, sampled training size, standardization and centroids.

## Denny Mountain prospecting and trail observations (2026-10-19)

This user-approved follow-up transfers the existing methods without claiming
independent validation. Public DNR 24K and 25–99K map-unit count queries return
zero processing-envelope coverage; the coarse 100K map remains the geological
constraint. Public USFS trail and basic ownership services provide geometry,
not legal boundary or safe-route certification. All geological/access acquisition
requests and hashes are retained separately for Denny.

[GDAL viewshed documentation](https://gdal.org/en/stable/programs/gdal_viewshed.html)
describes the established Wang et al. (2000) algorithm, projected-CRS requirement,
observer/target heights and curvature correction. We use it only to identify
possible observation positions on official trail geometry. Bare-earth terrain
visibility is not visibility through forest, a verified rock exposure or evidence
of cave presence. The lack of canopy/snow modeling is material in this setting.

Dated access checks and official source links are summarized in
[DENNY_RESULTS.md](docs/DENNY_RESULTS.md). Model-led cliff targets remain steep
and 382–560 m from mapped trails; a geological target is not automatically a
practical hiking destination. No source custodian was contacted.


## Kaleetan / Marble Peak public-source transfer — 2026-10-19

The user approved both carbonate proposals after the separately authorized
cave-specific public-literature screen. They are literature-informed prospecting
areas, not independently blind validation sites. Ordinary hiking/climbing reports
were not used as negative priority evidence; an unsuccessful cave-report search
is not proof that an area is unexplored. No further cave-location lookup or
private validation-archive access is part of the numerical analysis.

[The regional execution record](docs/APPROVED_AREAS_20261019.md) links the new
source manifests and scripts. DNR 1:100,000 geology is queried with whitelisted
rock/structural fields, and USFS trail/ownership geometries remain descriptive
context. The two approved 9 km² windows are retained without changing their
boundaries to improve model outcomes.

USGS 3DEP catalog rectangles overstated usable native elevation coverage at
Marble Peak: the initially selected standard 1 m inputs left the mapped marble
entirely unobserved. A Glacier Peak OPR crop was also entirely nodata. Those
coverage failures are preserved, rather than filled or interpreted as an absence
of terrain indicators. An older public [PSLC Tulalip 2013 survey](https://pugetsoundlidar.ess.washington.edu/lidardata/restricted/projects/2013tulalip.html)
provides another high-resolution source. Its [bare-earth metadata](https://pugetsoundlidar.ess.washington.edu/lidardata/metadata/2013tulalip_deliv2_be.html)
specifies 3 US survey foot cells, State Plane Washington North NAD83(HARN) and
NAVD88/Geoid03 elevations in US survey feet. GDAL OpenFileGDB/Warp handles reading
and horizontal resampling; the explicit height conversion is 1200/3937 metres
per US survey foot. No custom terrain, hydrology or TPI implementation is added.
Actual coverage and inter-survey overlap measurements govern acceptance.

Prior public cave-literature exposure is documented, and no model weight,
threshold or ranking rule is tuned using it. New-area reviews reconstruct the
saved-pixel arithmetic and retain complete original rankings; neither repeated
computation nor a visually plausible hillshade demonstrates cave-prediction skill.
