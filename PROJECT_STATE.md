# Project state — 2026-10-19

Repository: /home/Idiom/Repos/MyRepos/KarstFinder (the open VS Code workspace).

**M1–M3 delivered. Initial predictions are frozen. M4 has an exploratory public-
reference comparison; credible entrance-localization validation needs independent
survey-quality reference data.** The user reports no local dataset is available.

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
  Active review copy: qgis/KarstFinder.qgz. Baseline archive retained separately.
- Local-only validation project: data/private/validation/KarstFinder_Validation.qgz
  (39 valid persistent layers), currently loaded in the live QGIS application.

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

The available-data comparison is complete. More credible entrance-localization
evidence requires independently verified reference observations becoming legally
available without outreach. This is an empirical evidence limit, not a software
implementation step that additional model fitting can resolve.

M5 supervised refinement and M6 validated expansion are not justified with the
current few unverified records. Their prerequisites and prospective holdout
protocol are in docs/NEXT_EXPERIMENT.md. Do not tune the frozen model against
public references or claim future Cave Ridge revisions are independently blind.
