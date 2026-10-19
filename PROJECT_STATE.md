# Project state — 2026-10-19

Repository: /home/Idiom/Repos/MyRepos/KarstFinder (the open VS Code workspace).

**The approved southern Denny Mountain follow-up is complete and loaded in QGIS.**
It applies the existing methods to 9 km² as unvalidated prospecting. The user
approved the location on 2026-10-19 and asked to remove known-entrance overlays.
No X marks, red uncertainty circles or historical reference boundaries are in
the active map. No one has been contacted; outreach is permanently prohibited.

Initial Cave Ridge M1–M3 remain delivered and frozen. M4's public-source
comparison is exploratory; the user asks us to assume reliable reference data
is unavailable and proceed with practical prospecting without cave records.

## Current Denny Mountain deliverables

- Configs: configs/denny_v001_landscape.json and denny_v001_features.json.
  Study EPSG:26910 [615850,5252250,618850,5255250], 1,100 m processing buffer.
- Separate raw geology/access, prepared DEMs and results; original freeze intact.
- One landscape area selects the entire mapped marble lens (~6.64 ha).
  489 surface indicators: 477 cliffs and 12 depressions across geological context.
  **48 cliff patches overlap mapped marble; no depression does.**
- All 48 marble-cliff points are 382–560 m straight-line from the mapped trail
  in steep terrain. No hiking-ready target route or direct cliff approach is
  established. Scientific rank and access flags remain separate.
- Three possible OBS stations lie on official Denny Creek trail geometry.
  GDAL ground-only viewsheds omit trees/snow; stations are not verified viewpoints
  or entrances. Waypoint-only GPX: results/denny_v001_observation/.
- Working map qgis/KarstFinder.qgz; named project qgis/KarstFinder_Denny_v001.qgz.
  Both use 28 valid persistent layers and no private validation sources.
- All 31 numerical raster arrays and both ranking CSVs reproduce exactly.
- Final unvalidated prospecting snapshot: experiments/snapshots/denny_v001.json,
  144 file hashes; implementation commit dfaf523. Final numerical
  result directories are write-protected. Active QGIS review remains editable.
  All 489 geometries/support checks and trail-station containment checks pass.
  Fifteen tests pass and all 163 original Cave Ridge hashes verify.
- Access pages/alerts checked 2026-10-19; source HTML and hashes saved locally.
  Denny Creek Trailhead listed open; consult docs/DENNY_RESULTS.md for dated
  permit/parking rules, on-trail observation options and limits.

The user authorized this unvalidated geographic follow-up despite the earlier
prerequisite for expansion as a *demonstrated* method. It is not an independent
blind holdout: it overlaps the old study edge and prior reference exposure is
recorded in docs/DENNY_PLAN.md. No Denny cave inventory was used to tune it.

## Frozen experiment

experiments/frozen/blind_v002.json records 163 file hashes and implementation Git
243b7307fea8abccee7693ae4cec926fb09e6e0c. No cave source was acquired before the
freeze. Both numerical result directories are write-protected. All recorded
hashes verify; archived source code is read from the frozen Git commit. A verifier
bookkeeping correction for ignored package metadata is documented in
docs/FREEZE_AUDIT.md. No prediction/ranking was changed after validation began.

## Implemented and verified

- Isolated Arch-compatible environment with packaged QGIS/GDAL/NumPy/SciPy and
  WhiteboxTools. Live QGIS MCP plugin transport works on 127.0.0.1:9876.
- Four 1 m USGS LiDAR tiles (2019/2021), DNR geological units/structures, NAIP
  imagery and complete provenance. 30 km² study plus 1,100 m processing buffer.
- v001 landscape suitability with six preliminary areas; v002 independent
  depression/cliff analysis with 76 depression cores and 520 cliff patches.
  Each of 596 surface objects has evidence, components, rank, coordinates and
  uncertainty. None is labeled a confirmed cave or a detected entrance.
- Native 1 m coverage/seam QA, functioning Wang–Liu depression filling, modeled
  drainage context, six seeded descriptive terrain classes and sensitivities.
- Independent runs reproduce 18 v001 and 13 v002 raster arrays plus their rankings.
- Fifteen tests pass, including analytical GIS checks, uncertainty/area budgets,
  and frozen-artifact audit regression. All 596 feature polygons and supported
  representative points pass artifact checks.
- Frozen QGIS review project: qgis/KarstFinder_Blind_v002.qgz (36 layers).
  Baseline archive retained separately; active review is now Denny Mountain.
- Local-only validation project: data/private/validation/KarstFinder_Validation.qgz
  (39 valid persistent layers), retained as a local archive and not loaded.

## Validation findings

DNR's historical survey supplies one section-level cave-bearing region, not
accurate entrance coordinates. Four public OSM entrance nodes share one mapper
and state no survey accuracy. A 100 m assumed-radius scenario is exploratory,
not a confidence interval. Zero references qualify for the predeclared ≤25 m
entrance-localization test. Detailed sources and coordinates stay ignored/local.

At 10% of the 1.6684 km² comparable-geology support on the 10 m grid, the combined frozen index selects 3/4
public map points, morphology 4/4, original landscape 1/4 and geology 1/4 in the
predeclared tie ordering. A tie-average audit and 303 geology-matched rigid
translations are documented, without inferential p-values. The apparent surface-
feature signal is worth testing, but location quality, spatial clustering and
selection bias prevent claims of established entrance-prediction skill.

See docs/VALIDATION_REPORT.md, validation_summary.json and validation_audit.json.
The historical regional overlap alone is no stronger than geology-only support.

## Remaining dependency and next step

No accuracy-qualified reference dataset is currently available. The user reports
no local dataset and permanently prohibits contacting anyone. The unsent draft
was withdrawn; do not send messages or ask again about outreach. Continue only
with public sources and local analysis.

The available-data Cave Ridge comparison is complete. More credible entrance-localization
evidence requires independently verified reference observations becoming legally
available without outreach. This is an empirical evidence limit, not a software
implementation step that additional model fitting can resolve.

M5 supervised refinement and M6 expansion presented as validated are not justified with the
current few unverified records. Their prerequisites and prospective holdout
protocol are in docs/NEXT_EXPERIMENT.md. Do not tune the frozen model against
public references or claim future Cave Ridge revisions are independently blind.

## Methodology review preserved

METHODOLOGY.md now traces input datasets, geological assumptions, each implemented
algorithm, score arithmetic and the specific Denny cliff priority evidence.
The additive docs/reviews/denny_v001_methodology/ record retains byte-identical
CSV rankings/configurations and a per-object pixel-summary/score audit.
No original model, candidate rank, measurement, geometry or snapshot was changed.
The audit makes no network requests and reads no cave reference data. The user
explicitly prohibits known-cave lookups while this investigation continues.
