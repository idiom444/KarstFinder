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

## Blind-source record

Only the ridge's exact GNIS feature record was queried for geographic anchoring.
No local cave descriptions, inventories, photographs, entrance maps or entrance
coordinates were requested. DNR map-unit descriptions for marble and mixed
melange were screened automatically before display for sentences mentioning
caves/entrances. Only lithological text was used. Downloads for modelling use
an explicit attribute allowlist; arbitrary unit notes and generic point layers
are excluded. Labeled topographic maps were not inspected. No validation begun.
