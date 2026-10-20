# KarstFinder methodology and preserved Denny evidence

**Current scope correction (2026-10-20):**
[Carbonate v001 methodology](docs/carbonate_v001/METHODOLOGY.md) is the current
prospecting method: documented marble is required before terrain detection,
with a small flagged contact margin; broad mélange/unknown rock is excluded.
It preserves all prior science and uses a separately versioned priority model.
[Results and complete review measurements](docs/carbonate_v001/RESULTS.md) cover
all four reprocessed areas. The following original Denny methodology and evidence
remain an unchanged historical account, not the recommended current candidate scope.

Documentation review: 2026-10-19. This describes the **implemented methods and
saved measurements**, rather than a validated cave-entrance detector. The current
Denny rankings, configurations, terrain products and geometries are unchanged.

## 1. Scientific scope and information boundary

The workflow separates four claims:

| Claim | Current evidence |
|---|---|
| Favorable cave-forming landscape | Geological map plus explicit terrain hypotheses; implemented. |
| Potential cave-related surface form | DEM-derived depressions and steep patches; implemented, with unresolved alternative origins. |
| Individual cave entrance | No diagnostic opening detector or independently verified localization demonstrated. |
| Confirmed natural cave | No confirmation from the Denny analysis. |

All suitability scores are **ordinal, assumption-based indices**. No score is a
probability, measured discovery rate or confidence in cave existence. The
landscape and feature methods share geology and DEM inputs; agreement between
them is not independent observational confirmation.

The original Cave Ridge v001/v002 predictions were frozen before local reference
acquisition: [blind freeze](experiments/frozen/blind_v002.json), implementation
`243b7307fea8abccee7693ae4cec926fb09e6e0c`. Denny is the later user-approved
prospecting application, with prior Cave Ridge reference exposure and geographic
overlap. It must **not** be described as a fresh independent blind holdout.
The incidental unopened search snippet is already recorded in
[DENNY_PLAN.md](docs/DENNY_PLAN.md); no Denny inventory was used to tune the model.

This documentation review makes no network requests and reads no private cave
references, inventories, entrance photographs or exploration reports. Future
work must likewise exclude those sources while this investigation proceeds.
No one may be contacted. Previously archived cave-validation data stay outside
this analysis and outside the Denny project.

## 2. Experiment versions and spatial frame

| Run | Spatial scope | Preserved outputs |
|---|---|---|
| Cave Ridge landscape `blind_v001` | 6 × 5 km; EPSG:26910 bounds `[617000,5253500,623000,5258500]` | `results/blind_v001/`, included in the original v002 freeze |
| Cave Ridge features `blind_v002` | Same 30 km² study | `results/blind_v002/`, original blind freeze |
| Denny landscape `denny_v001_landscape` | 3 × 3 km; bounds `[615850,5252250,618850,5255250]` | `results/denny_v001_landscape/` |
| Denny features `denny_v001_features` | Same 9 km² Denny study | `results/denny_v001_features/` |

All use a 1,100 m computational buffer, NAD83 / UTM zone 10N horizontal metres
(EPSG:26910), and NAVD88 elevation metres. Denny's buffered grid is 5,200 × 5,200
native 1 m cells. Terrain derivatives are computed before cropping to the study.
No vertical-datum transformation or feet-to-metres conversion is applied to the
USGS standard tiles. Their catalog states metres even when band UnitType is empty.

The Denny location was approved before its analysis. Selection used the separate
mapped marble body `PMmb(e)`, DNR polygon `OBJECTID=29438`, on southern Denny
Mountain above Denny Creek. The scoping record gives approximately 3.846 km from
the Cave Ridge GNIS ridge anchor to its nearest edge, and 3.251 km between the
two mapped marble bodies' edges. These are projected map distances, not walks.
“Nearest” means the closest separate explicit marble body found in the examined
regional compilation, not proof that no closer unmapped carbonate exists.
The broad regional scoping query itself was not archived as a complete regional
comparison dataset; [DENNY_PLAN.md](docs/DENNY_PLAN.md) preserves the decision,
while the finalized acquisition preserves the approved study's inputs. The
current output alone cannot independently establish a statewide nearest ranking.

Executable parameters are [landscape config](configs/denny_v001_landscape.json)
and [feature config](configs/denny_v001_features.json). Numerical scales,
thresholds and weights were transferred from the original implementation without
fitting Denny cave labels. Denny outputs use separate paths. The code/configuration
and final artifacts are covered by the [144-file Denny snapshot](experiments/snapshots/denny_v001.json),
implementation `dfaf523` (full commit recorded in that manifest).

## 3. Datasets and their actual roles

The [Denny acquisition manifest](docs/experiments/denny_v001_acquisition.json)
records exact URLs, requested attributes, local files, sizes and SHA-256 hashes.
The [dataset assessment](docs/DATASETS.md) and original
[acquisition manifest](docs/acquisition_manifest.json) retain supplier information.
Large source data stay local and ignored by Git.

| Dataset | Local source / preparation | Role and limitations |
|---|---|---|
| USGS standard 1 m bare-earth DEM, `WA_KingCounty_2021_B21` | `data/raw/USGS_1M_10_x61y526_WA_KingCounty_2021_B21.tif` and matching `x62y526` tile | Preferred elevation where valid; numeric terrain input. NAVD88 metres, EPSG:26910. |
| USGS standard 1 m DEM, `WA_EasternCascades_2019_B19` | Same two tile names with the 2019 project suffix | Fallback where 2021 is missing. Both acquisitions are retained, not silently blended. |
| DNR 1:100,000 bedrock units | `data/raw/denny_v001/dnr_11.geojson` → `data/processed/denny_v001/context.gpkg`, layer `bedrock` | Mapped lithology, including marble `PMmb(e)` and mixed melange `JTRmt(e)`. Small lenses and exact contacts are unresolved. |
| DNR contacts, faults, orientations | `dnr_9.geojson`, `dnr_7.geojson`, `dnr_1.geojson` → corresponding context GeoPackage layers | Geological context only. No fault-distance bonus, measured fracture alignment or structural predictor enters the ranking. |
| DNR 24K and 25–99K service coverage checks | `data/raw/denny_v001/*_coverage.json` | Both saved queries return zero map-unit coverage in the processing envelope. This does not prove that no finer published map exists elsewhere. |
| NAIP 2017 RGB imagery | `data/raw/naip2017_rgb_2m.tif`, originally exported from a native 3 ft state service at 2 m | Optional visual context, partial Denny-window coverage. No image classifier, spectral score, manual entrance identification or ranking adjustment uses it. |
| USGS GNIS ridge anchor | `data/raw/gnis_ridge.json`, geographic feature 1517515 | Initial Cave Ridge geographic anchor only; not a cave record or a predictor. |
| USFS official trails and basic ownership | `data/raw/denny_v001/usfs_trails.geojson`, `usfs_ownership.geojson` → `results/denny_v001_access/access.gpkg` | Separate access context. Neither dataset changes scientific scores; ownership geometry is not a legal access determination. |
| Dated land-manager/operator pages | Local HTML and [access-source manifest](docs/experiments/denny_v001_access_sources.json) | Dated field-planning context only. No terrain or cave-prediction input. |

DNR's native service CRS is EPSG:2927, but acquisition requests return the model's
projected EPSG:26910. Whitelisted geological attributes exclude arbitrary notes,
generic point layers and inventories. Source USGS catalog records state public
domain; retain DNR and USFS attribution/disclaimers. Public serving does not by
itself establish unrestricted redistribution rights for every state/imagery item.

### 3.1 Preparation and quality controls

[prepare.py](scripts/prepare.py), lines 19–88, uses GDAL BuildVRT/Warp: older
2019 tiles first, 2021 last for newest-valid precedence; nearest resampling onto
a common 1 m grid and arithmetic-average resampling to 10 m. It checks CRS and
catalog elevation-unit evidence, clips geological layers, and writes acquisition
identity and overlap diagnostics. Missing elevation is not invented or feathered.
The 10 m acquisition flag describes valid 2021 availability; seam cells can
average multiple native epochs and must not be read as pure native fractions.

[native_qa.py](scripts/native_qa.py) separately aligns each acquisition at 1 m,
constructs the actual newest-valid epoch mask, identifies adjacent changes of
survey year, and uses SciPy's Euclidean distance transform for seam distance.
A native cell must be valid and **more than 25 m from a seam**. A 10 m void
exclusion is configured if voids exist; none occur in this run.

Saved Denny [native QA](docs/experiments/denny_v001_native_quality.json) reports:

- All 27,040,000 buffered cells and all 9,000,000 study cells have valid elevation.
- Study epochs: 8,539,938 cells from 2021; 460,062 from the 2019 fallback.
- The seam mask excludes 72,840 m², leaving 8.92716 km² feature-eligible terrain.
- A fixed every-tenth-row/column overlap sample has 9,971 paired elevations;
  median 2021-minus-2019 difference −0.17035 m, p95 absolute difference 1.01654 m.

These are **raster coverage and survey-disagreement measurements**, not local
entrance accuracy, registration certification or proof that ground returns exist
under every forest/cliff cell. Interpolation, vegetation classification, snow,
vertical faces and overhangs remain material limitations. The separate 10 m
averaged-overlap statistic in the preparation report uses different sampling and
aggregation; neither residual distribution is an independently measured error bar.

## 4. Geological assumptions

**Observation from the source map:** the compilation distinguishes `PMmb(e)`
marble from surrounding units. Polygon 29438 has vector area about
66,428.585 m² (6.643 ha). Its 1 m raster representation has 66,434 marble cells;
its 10 m center-cell representation has 667 cells (66,700 m²). These small area
differences follow rasterization and do not represent improved map accuracy.
The source's “certain” unit-identification field does not make its boundary
entrance-accurate.

**Hypothesis:** mapped marble is more favorable for carbonate dissolution and
natural cave development than the surrounding mapped noncarbonate rock. That
prioritization does not establish purity, exposed marble, connected voids,
water pathways, speleogenesis or an accessible opening at any target.

Landscape geology `G_L` is 1 for mapped marble, 0.35 for `JTRmt(e)` mixed melange,
and 0 for other units. Mixed melange may contain marble; 0.35 is an assumed
relative weight, not a measured carbonate fraction or occurrence probability.
A zero means lack of mapped support rather than confirmed carbonate absence.

For feature extraction, [run_features.py](scripts/run_features.py), lines 16–24
and 54–59, rasterizes units at 1 m and sets feature evidence `G(x)` in this order:

1. Mixed melange: 0.35; other nonwater units initially 0.
2. Within 100 m Euclidean pixel-center distance of mapped marble: 0.6,
   overriding mixed melange or other nonwater units.
3. Mapped marble: 1.0, overriding the buffer.
4. Mapped water: 0, regardless of the buffer.

The distance-transform cell spacing is implicitly 1 m, valid for this configured
native grid. The **100 m buffer is a hypothesis/sensitivity choice, not measured
contact accuracy or a confidence interval**. It can admit noncarbonate ground
and should not be interpreted as actual marble exposure.

## 5. Landscape algorithm and candidate areas

[run_baseline.py](scripts/run_baseline.py), [score_landscape](src/karstfinder/model.py)
and the landscape configuration implement the following chain:

1. GDAL DEMProcessing produces Horn slope (degrees), aspect (clockwise from
   north; flats NoData) and hillshade from the 10 m averaged DEM. Hillshade is
   visual relief only; aspect is retained but is not used in scoring.
2. WhiteboxTools `DevFromMeanElev` computes standardized local elevation
   departure `DEV = (z − neighborhood mean) / neighborhood standard deviation`
   in 21, 61 and 201 cell square windows: 210, 610 and 2,010 m at 10 m resolution.
   This adapts the multiscale-position reasoning summarized in [RESEARCH.md](RESEARCH.md)
   from Cuthbertson et al.; it does not reproduce their full classifier.
3. Each scale with `abs(DEV) <= 0.5` contributes one mid-slope vote. Let
   `M = number_of_votes / 3`.
4. Define a slope-based exposure proxy `E = clip((slope_deg − 15)/30, 0, 1)`.
   It measures a selected slope range, not observed bare rock.
5. Compute `T = 0.6*M + 0.4*E` and landscape score `L = G_L*T`.
6. Require a fully valid 201 × 201 elevation neighborhood using SciPy
   `minimum_filter`; crop after buffered processing. Invalid cells stay NoData.
7. GDAL polygonizes `L >= 0.5` with four-neighbor connectivity; discard components
   below 1,000 m². Rank by descending mean L, descending area, then ascending
   representative-point easting/northing. OGR PointOnSurface supplies an inside
   reference point, not a proposed entrance coordinate.

Because mixed melange has `G_L=0.35` and `T<=1`, it cannot pass the 0.5 landscape
area threshold. This makes the area selection strongly dependent on mapped marble.
The selected scales, cutoffs and weights are hypotheses, not learned parameters.

**Denny result:** one untruncated polygon `KF-001`, area 66,700 m², is selected.
Its mean `G_L=1`, mean T/mean L = **0.9648526426484025**, mean mid-slope votes
2.9970014993, mean E = 0.9136308570 and mean slope 43.403451°. The selection covers
100% of the rasterized marble lens and 0.7411% of the study. Consequently the
landscape baseline does **not** demonstrate additional spatial discrimination
within this lens. See [original candidate CSV](results/denny_v001_landscape/candidates.csv)
and its byte-identical [review copy](docs/reviews/denny_v001_methodology/landscape_candidates.csv).

## 6. Native surface-feature algorithms

[derive_features.py](scripts/derive_features.py) uses established GDAL/Whitebox
implementations on the buffered elevation, not screenshots or custom hydrology:

| Derivative | Implementation and use |
|---|---|
| 1 m slope / hillshade | GDAL Horn slope with unit ratio 1; hillshade for review. |
| Closed-depression depth | Whitebox `FillDepressionsWangAndLiu(fix_flats=False)` minus original DEM, clipped below at zero. |
| Local elevation residual | Whitebox `DiffFromMeanElev`, 11 × 11 native cells; a signed local elevation departure in metres. |
| Modeled drainage | Separate Wang–Liu fill at 10 m with `fix_flats=True`, then Whitebox D8 catchment area; context only, not a measured stream or sinking-water anomaly. |

The installed Whitebox binary is 2.4.0 (wrapper 2.3.6), GDAL 3.13.3. Binary hashes
and product hashes are in the saved derivative/run manifests. The original
flat-bottom synthetic test found that the installed default depth/fill workflow
could miss a basin; Wang–Liu reproduced a known 2 m basin and did not invent a
closed pit at an open outlet. [tests/test_features.py](tests/test_features.py)
preserves those analytical tests. Artificial flat-routing gradients are excluded
from measured pit depth by separating the two fill workflows.

[run_features.py](scripts/run_features.py), lines 27–31 and 76–120, extracts:

| Type | Pixel criterion | Four-connected component size |
|---|---|---|
| Depression core | Filled-minus-original depth >=0.5 m | 4–2,500 m² |
| Cliff/exposure patch | Native slope >=45° | 25–10,000 m² |

These are thresholded **surface objects**. A depression core is not necessarily
an entire basin or sinkhole; a cliff patch is not an opening. Components are
labeled before geological filtering so an object is not split at a contact.
A retained object must have complete native quality support, at least one
positive-G pixel, and no mapped water pixel. Size-ineligible objects are not
ranked, but their underlying rasters remain available. Study-edge truncation is
flagged rather than silently removed. GDAL Polygonize stores the components.

For each retained object, calculate:

- area from native mask cell count; mean G and T across the **entire object**;
- mean slope, maximum depression depth, and minimum 11 m residual;
- minimum raster marble distance; native 2021 fraction;
- positive-geological-support fraction, contact-only, mapped talus/slide and
  study-boundary flags; plus evidence, alternatives and uncertainty text.

T is the 10 m terrain score repeated onto the 1 m grid. This does not create
new 1 m landscape information. A partly supported object can extend outside
marble or the assumed buffer. The stored field `carbonate_fraction` is actually
`mean(G>0)` across the object: **it includes mixed melange and assumed contact
support and is not a measured fraction of carbonate rock**. Vector overlap with
mapped marble is added separately in the access dataset.

Talus/slide flags recognize the implemented `Qta`/`Qls` codes only. Their absence
is not evidence that there is no talus, landslide or other hazard. Six Denny
objects are boundary-clipped, 64 are contact-only and none receives that mapped
Qta/Qls flag. Zero missing cells does not eliminate DEM artifacts.

### 6.1 Object scores and deterministic ranking

For a depression, `F_D = min(1, maximum_depth_m / 3)`.

For a cliff, with clip bounded to [0,1]:

```
F_C = 0.5*clip((mean_slope_deg − 45)/30)
    + 0.5*clip(−minimum_11m_residual_m/2)
S   = 0.4*mean_G + 0.3*mean_T + 0.3*F
```

All weights and saturation scales are declared assumptions. Negative local
residual is hypothesized to indicate hollow/recess context within a steep patch;
it is not a detected portal, undercut or subterranean void. A single extreme
residual pixel can influence F; object area and DEM artifacts can affect such
extrema. Slope also occurs in T, so the components are correlated rather than
independent evidence terms. Cliff/depression F values are not calibrated to a
shared empirical cave rate.

Sort by descending S, descending F, then ascending kind string, easting and
northing ([run_features.py](scripts/run_features.py), line 123). Store both overall
`rank` and consecutive `rank_within_kind`. The representative point is the first
row-major maximum of `0.4*G + 0.3*T` within positive-G object pixels; its coordinate
marks supported terrain, not an identified opening or safe approach point.
Coordinates are retained at computational precision without claiming that accuracy.

The original [ranked_indicators.csv](results/denny_v001_features/ranked_indicators.csv)
contains all 489 objects, and `features.gpkg` retains `surface_indicators` polygons
and `ranked_indicators` points. An exact CSV copy and per-object score-contribution
audit are in the [review record](docs/reviews/denny_v001_methodology/README.md).

### 6.2 Regional grid, clustering and sensitivity

The 10 m combined raster is a different aggregation from object S. Within each
10 × 10 native block take maximum G and maximum retained-object morphology F,
then compute `0.4*G_max + 0.3*T_10m + 0.3*F_max` where G_max>0; elsewhere zero.
The maxima can come from different native pixels. These cells rank regional
area, not the position of an opening; do not infer object S from the cell color.

Native positive geological support covers 1.494981 km²; the maximum-aggregated
10 m footprint covers 1.5338 km². The positive native morphology raster covers
83,120 m². The sum of all 489 polygon areas is 83,149 m²: component-area sum and
positive-score raster footprint have different definitions and can include
cross-method overlap/zero-strength pixels. These quantities are not cave areas.

SciPy `kmeans2` supplies six descriptive classes from standardized slope and
210/610/2010 m DEV: seed 42, up to 10,000 sampled cells, k-means++ initialization,
50 iterations, then `vq` assignment. The centroids and cell counts are saved in
`clustering.json`. Classes have no cave labels and contribute nothing to S.
No supervised, MaxEnt, self-supervised image model or deep network is fitted.

Depression sensitivities at 0.3/0.5/1/2 m retain 14/12/9/7 objects with mapped
marble **or mixed melange** support. Buffers 0/50/100/250 m give the same counts
in this run ([saved sensitivity](docs/experiments/denny_v001_sensitivity.json)).
This tests count response, not entrance accuracy, independence, ranking stability
or true contact uncertainty. It does not validate the cliff threshold, window
sizes or weights; those were not systematically optimized or validated here.

## 7. Specific evidence behind Denny Creek cliff priority

The evidence chain is geographic lithology selection → landscape index → native
steep-patch measurements → fixed scoring → separate geological overlap display.
It did not include known entrances, cave-looking photographs, manual promotion
of a dark hillshade patch, field observations or actual successful discoveries.

| Saved observation / computation | Reason it affected priority | Unverified hypothesis or limitation |
|---|---|---|
| DNR maps a separate ~6.64 ha marble lens above Denny Creek | Establishes a stronger mapped carbonate prior than mixed units | Real exposure, composition and contacts remain unverified at entrance scale. |
| All rasterized marble passes the landscape threshold; mean T ~0.965 | Supplies a high shared terrain contribution | The baseline adds little localization within this lens. |
| 48 retained cliff polygons have positive **vector intersection area** with marble; no retained depression does | Focuses review on the model's cliff/exposure approach within mapped carbonate | 48 fragmented threshold objects are not 48 independent caves or entrances. |
| The original top ten all have mean G=1 and high T | Their fixed 40% geology and 30% terrain terms are large | These terms encode our assumptions and share input data. |
| Top cliff slopes are ~48–51° with negative local residual minima | The cliff F formula rewards these properties | Glacial rills/faces, ordinary bedrock and DEM artifacts can produce the same signature. |
| Top ten have native 2021 fraction 1, complete quality support, no contact-only or edge-clipping flag | Reduces the specific seam/boundary concerns represented by these flags | It does not verify ground returns, rock exposure, a void or map accuracy. |
| Native hillshade review shows relief | Confirms that the displayed polygons correspond to computed surface relief | No recognizable entrance was established; darkness is lighting. |

The 48 overlapping cliff polygons total 6,185 m² of object area; their vector
marble intersection sums to 5,346.325 m². Some objects therefore extend beyond
the mapped unit. Membership in the 48 is calculated by OGR polygon intersection
area >0 in [screen_denny_access.py](scripts/screen_denny_access.py), lines 42–53
and 87, not by a confirmed lithology measurement. The map's C labels preserve
original cliff ranks; they are not a new ranking fitted to the 48-object subset.

### 7.1 Existing top-ten measurements

Values below are rounded for reading. Byte-identical full-precision records,
coordinates, flags, supporting measurements and all lower-ranked objects are
preserved in [screened_indicators.csv](docs/reviews/denny_v001_methodology/screened_indicators.csv).
G, T and F below are object means/derived morphology as defined above; “trail gap”
is a straight-line distance from the representative point, unrelated to S.

| Map rank | Object ID | Area m² | Mean slope ° | Min residual m | G | T | F | Combined | Trail gap m |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 | C-007851 | 253 | 50.560 | -2.208 | 1.000 | 0.945808 | 0.592666 | 0.861542 | 560.5 |
| C2 | C-007828 | 570 | 48.749 | -2.432 | 1.000 | 0.955940 | 0.562485 | 0.855528 | 490.2 |
| C3 | C-007722 | 247 | 49.192 | -2.072 | 1.000 | 0.945110 | 0.569872 | 0.854495 | 542.2 |
| C4 | C-007983 | 654 | 48.816 | -2.018 | 1.000 | 0.948241 | 0.563598 | 0.853552 | 492.8 |
| C5 | C-007707 | 63 | 49.122 | -1.468 | 1.000 | 0.971372 | 0.435710 | 0.822125 | 513.5 |
| C6 | C-007841 | 97 | 49.320 | -1.562 | 1.000 | 0.934964 | 0.462511 | 0.819242 | 516.8 |
| C7 | C-008008 | 440 | 49.333 | -1.375 | 1.000 | 0.978432 | 0.415990 | 0.818327 | 480.3 |
| C8 | C-008453 | 59 | 50.167 | -1.276 | 1.000 | 0.945221 | 0.405147 | 0.805110 | 474.1 |
| C9 | C-008180 | 111 | 47.780 | -1.396 | 1.000 | 0.932274 | 0.395380 | 0.798296 | 480.8 |
| C10 | C-008379 | 135 | 47.663 | -1.350 | 1.000 | 0.917203 | 0.381992 | 0.789759 | 480.6 |

For **C1 / C-007851**, the stored 253 m² object is entirely within mapped marble:
G=1, T=0.9458077549934387, mean slope=50.559959411621094° and minimum residual
=−2.2084298133850098 m. Hence:

```
slope half of F  = 0.5*((50.559959411621094 − 45)/30) = 0.0926659901936849
residual half    = 0.5*clip(2.2084298133850098/2)    = 0.5
F               = 0.5926659901936849
geology term    = 0.4
terrain term    = 0.2837423264980316
morphology term = 0.17779979705810547
S               = 0.861542123556137
```

Its maximum closed-depression depth is **0 m**. Its high rank comes from the
cliff model, not independent depression evidence. The point is 560.456 m from
the mapped trail and has a DEM maximum slope of 83.184° within 25 m; those are
access concerns and do not add to the scientific score. C1 remains rank one
because of the declared formula, not because an entrance was seen there.

Across the full study, size-eligible components number 2,070 cliffs and 65
part-depth depressions; quality/geological/water filtering retains 477 cliffs
and 12 depressions. The highest depression is `D-000032`, overall rank 43,
S=0.7047213, mean G≈0.35, maximum depth 3.474365 m. It does not intersect mapped
marble. The absence of a retained marble depression is an algorithm result, not
proof of absent sinkholes or caves.

## 8. Access and observation stations are separate results

[screen_denny_access.py](scripts/screen_denny_access.py) copies the existing
scientific rank and adds OGR nearest-trail distances, ownership intersections,
vector marble overlap, local native-slope statistics and descriptive flags.
A >50 m trail gap, >=35° slope within a 25 m disk, unresolved/non-FS mapped
ownership, cliff type or recognized talus/slide material triggers a flag. These
thresholds are coarse screening choices, not safe-access thresholds.
`route_verified=0` and `hiking_ready=0` are explicit unset verification statuses,
not the output of a route-finding or complete safety assessment.

All 48 marble-cliff representative points are 381.574–560.456 m from a mapped
trail and have steep nearby terrain. All representative points fall within USFS
mapped ownership, but no hiking-ready approach to a cliff is established.
Neither trail distance nor ownership contributed to S or reordered candidates.

[denny_observation_points.py](scripts/denny_observation_points.py) is an additional
field-planning calculation after ranking. It samples the official Denny Creek
trail geometry every 100 m, keeps in-study samples within 1 km of target marble
polygon 29438 and rejects near-duplicate samples within 50 m. GDAL
ViewshedGenerate uses the projected 10 m bare-earth DEM, observer height 1.7 m,
ground target, GVM_Edge, 1,500 m range and curvature coefficient 0.85714.

Count visible cells within the 667-cell rasterized **Denny target**. Sort by
visible target cell count descending and marble distance ascending; retain up to
three positive-visibility stations at least 200 m apart. Thirty-four samples
were evaluated. OBS-01/02/03 have 606/601/586 modeled visible target cells,
respectively. These are 90.85%/90.10%/87.86% bare-earth terrain visibility, not
visible entrances, visible rock through canopy, observation-success rates or
cave probabilities. Viewsheds exclude forest, snow, weather and actual tread
alignment; the stations are unverified viewpoints on source trail geometry.
They do not move or promote any candidate and the GPX supplies no off-trail route.
The earlier buffered-target development calculation and its scope correction
are recorded in [EXPERIMENTS.md](EXPERIMENTS.md); only polygon 29438 is used here.

## 9. Preserved review record and verification

The current documentation review preserves, without editing originals:

| Review artifact | Purpose |
|---|---|
| [landscape_candidates.csv](docs/reviews/denny_v001_methodology/landscape_candidates.csv) | Byte-identical original one-area landscape ranking and measurements. |
| [ranked_indicators.csv](docs/reviews/denny_v001_methodology/ranked_indicators.csv) | Byte-identical original 489-object ranking with all component/uncertainty fields. |
| [screened_indicators.csv](docs/reviews/denny_v001_methodology/screened_indicators.csv) | Byte-identical 489-object ranking plus separate geological intersection/access measurements. |
| [score_audit.csv](docs/reviews/denny_v001_methodology/score_audit.csv) | Recomputed G/T/F contributions and score, preserving the original IDs/order. |
| Feature and landscape config copies | Exact executable parameter versions, not revised settings. |
| [audit_summary.json](docs/reviews/denny_v001_methodology/audit_summary.json) | Pixel-summary/ranking consistency checks and interpretation limits. |
| [review_manifest.json](docs/reviews/denny_v001_methodology/review_manifest.json) | Original-source and review-file SHA-256 hashes. |

The original GeoPackages retain the actual object polygons and supported points;
original GeoTIFFs retain measurements at every pixel. They remain local,
write-protected and referenced by the Denny snapshot. No geometry is reduced to
just this document's rounded table. The original ranking CSV SHA-256 is
`909077203a81f148c4f0a4e35ec96b4a7e10805a19969e7d27eb47addad081ac`;
the access CSV SHA-256 is
`11901ef5c3c44e358b5257890529bbc20b84087c0fc12a1a1d0851e827b20609`.

[audit_denny_methodology.py](scripts/audit_denny_methodology.py) reads saved object
polygons, rasterizes each local object mask with GDAL, and recomputes area,
mean G/T/slope, minimum residual, maximum depth, F, S, positive-support fraction
and native 2021 fraction from the saved pixels. It checks complete quality support,
the declared tie order and consecutive overall/method ranks for every object.
This is a traceability check of recorded calculations, not independent evidence
that those calculations predict caves. It makes no acquisitions and never reads
private cave references. Verify the review without rerunning or changing models:

```bash
.venv/bin/python scripts/audit_denny_methodology.py --verify
```

The review verified all **144 Denny snapshot entries and 163 original Cave Ridge
freeze entries before and after** creating the review record. Earlier independent
computational repeats matched 18 landscape and 13 feature raster arrays and both
ranking CSVs. Feature/support checks cover all 489 geometries; the saved
[reproducibility report](docs/experiments/denny_v001_reproducibility.json) also
checks GeoPackage rows and the 28-layer persistent QGIS project.

Initial mutable QGIS provider access changed two Denny GeoPackage byte hashes
before finalization. [The provider audit](docs/experiments/denny_v001_provider_audit.json)
retains original and post-review hashes; SQLite rows match independent repeats
apart from expected creation timestamps. The final Denny snapshot records the
post-review bytes. Current projects use immutable read-only providers. This
review does not rewrite run manifests, the final snapshot or either GeoPackage.

## 10. Interpretive limits and work not implemented

The system currently prioritizes mapped carbonate plus selected surface forms.
It has not established independent predictive skill or confirmed a Denny cave.
Glacial erosion, normal rock faces, talus/breakdown, landslides, excavations,
vegetation/ground-classification errors, survey registration, snow, and DEM
interpolation can produce similar signatures. Overhead DEMs can omit entrances
beneath overhangs, boulder accumulations and near-vertical faces.

There is no implemented diagnostic collapse classifier, linear-trench detector,
fracture-alignment score, measured losing-stream detector, underground-connectivity
model, learned entrance detector, calibrated probability model or verified access
route. Aspect, faults, contacts, orientations, drainage and terrain classes are
retained context, not extra scoring terms. Reliable entrance references are
assumed unavailable for this phase; no new lookup or validation is performed.

A future methodological revision requires a new experiment name/configuration
and output tree. Preserve current hypotheses, scores and failures for comparison.
Any later claim of improvement needs appropriate independent evidence; do not
select thresholds on discovered entrances and then call the same locations an
independent test. The current investigation continues using geology, terrain and
unlabeled imagery only, with no cave-record searches or third-party contact.

## Approved regional transfers — 2026-10-19

The user subsequently authorized a public cave-specific literature screen for
selecting additional areas, then approved both proposed 3 × 3 km Kaleetan Peak
vicinity and Marble Peak / upper Marble Gulch windows. This is a separate,
literature-informed prospecting phase; it does not alter the preserved Denny
review or constitute independent blind cave validation. No entrance records,
private archive or known-cave overlays are used as model inputs. No one is
contacted. [The regional execution record](docs/APPROVED_AREAS_20261019.md)
documents the approved extents, sources, adapters, map interpretation and audits.

The numerical terrain methods, hypothesis weights, thresholds, component size
limits, four-neighbour connectivity and deterministic ranking rules above are
retained. `scripts/run_approved_area.py` calls the unchanged archived numerical
implementations. `src/karstfinder/prospecting.py` parameterizes their lithology
vocabulary: PMmb(e) at Kaleetan and TRmb(e) at Marble Peak both map to the existing
marble class, while JTRmt(e) retains the existing uncertain mixed-melange support.
The adapter preserves category precedence and contact-distance calculation;
synthetic GIS tests compare it to the archived PMmb(e) implementation.

`scripts/prepare_approved_area.py` verifies actual valid-cell coverage before
derivatives and preserves source-project years and the existing 25 m seam
exclusion. A catalog rectangle is not a coverage measurement. Marble Peak's
initial USGS 1 m inputs were rejected because the marble lens lacked valid cells;
the coverage-screening record preserves this failure. The public PSLC Tulalip
2013 bare-earth source provides native 3 US survey foot data. GDAL performs the
horizontal transformation from EPSG:2926 to EPSG:26910 and nearest-neighbour
sampling onto a 1 m working grid; valid heights are converted from US survey feet
to metres using 1200/3937. It is not a coarse DEM enlarged to imply native detail.
Source metadata, checksums, unit conversion and overlap checks are recorded
separately. No fitted vertical offset or threshold adjustment is introduced.

The new review bundles retain original full-precision rankings, measurements and
configuration copies. `scripts/audit_approved_area.py` reconstructs each score
from the saved object pixels, checks point/polygon consistency and deterministic
ranks, and compares separate repeat runs. Scientific raster arrays, CSV bytes,
and GeoPackage geometries/attributes are compared separately from SQLite container
metadata. These establish traceability and reproducibility, not cave-detection
skill. Different terrain epochs and source sampling also limit comparison of
ordinal scores between areas.


## Additive enhanced_v001 methodology

The implemented enhanced workflow is documented separately in
[Enhanced methodology](docs/enhanced_v001/METHODOLOGY.md), with
[geological source discovery](docs/enhanced_v001/GEOLOGY_SOURCES.md),
[matched-object comparisons](docs/enhanced_v001/COMPARISON.md) and
[reproduction / QGIS instructions](docs/enhanced_v001/WORKFLOW.md).
The text above describes the preserved baseline. Its pre-upgrade copy and
original library/hash audit are retained under `docs/enhanced_v001/`.

The upgrade unions every original lead with new connected terrain and drainage
setting features, removes the carbonate gate and maximum-area caps for new
terrain hypotheses, uses three-scale residual q10 rather than a single cliff
minimum pixel, and groups correlated observations by family. Continuous exact
strength colors remain separate from geological/data confidence. New code lives
in `src/karstfinder/enhanced/` and `scripts/enhanced_*.py`; archived analytical
code is unchanged. These are unvalidated prospecting analyses, not independently
blind cave validation, entrance localization or verified hiking routes.
