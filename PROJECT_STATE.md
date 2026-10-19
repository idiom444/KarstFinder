# Project state — 2026-10-19

Canonical repository: `/home/Idiom/Repos/MyRepos/KarstFinder`, selected by the
user's correction to use the open VS Code workspace.

**Blind stage is active. No known Cave Ridge cave locations were consulted.
Initial predictions are exploratory and NOT finalized or frozen.**

## Completed and verified

- Git repository, isolated system-site-packages venv, repeatable acquisition,
  preparation, baseline, tests and persistent QGIS project generation.
- Live QGIS MCP plugin transport verified at 127.0.0.1:9876; QGIS 4.2.2. No QGIS
  MCP tool namespace was exposed to Codex, so its installed socket interface was
  used directly. Saved live providers and 772-algorithm inventory. GRASS provider
  advertises algorithms, but standalone GRASS/SAGA executables are unavailable.
- Acquired four numeric 1 m USGS LiDAR DEM tiles (2019/2021), DNR map units,
  faults/contacts/orientations, NAIP 2017 RGB, GNIS ridge-only geographic anchor,
  and a LiDAR acquisition/accuracy report. All raw files remain ignored locally.
- Full 10 m DEM coverage over 30 km² plus processing buffer after two-epoch
  mosaic. Per-epoch identity and empirical overlap residuals retained.
- Implemented landscape baseline: GDAL slope/aspect/hillshade, Whitebox multiscale
  standardized elevation deviation, lithology evidence and explicit indices.
- Six preliminary landscape areas, 0.1241 km² total (0.414% of study envelope).
  No entrance-like feature detector, cave confirmation, validation or fitted
  probability. Top-ranked southwestern area is truncated by the study boundary.
- `qgis/KarstFinder.qgz`: 21 persistent layers, relative paths; saved, reopened
  with no invalid layers, and map rendered for review.
- Seven analytical tests passed, including independent known-plane checks.

## Milestones

M1 foundation delivered, with remaining data-quality refinements explicitly
recorded. M2 exploratory landscape baseline delivered. M3 feature analysis and
final blind freeze remain open. M4 validation, M5 improvement and M6 expansion
have not started. Geology and imagery acquisition limitations are in
`docs/DATASETS.md`; no blocker prevents continued local development.

## Important limitations and decisions

- 1:100,000 mapped marble is useful evidence, but cannot locate metre-scale
  contacts; mixed melange may hide unmapped carbonate. Only mapped marble can
  meet the first baseline's candidate threshold. Consider omission sensitivity.
- Two surveys differ locally: median −0.35 m and p95 absolute 5.14 m over their
  overlap. Investigate before entrance-scale depression/discontinuity analysis.
- All weights, windows and thresholds are hypotheses. No predictive skill has
  been measured. Candidate polygons/representative points are landscape areas.
- No hydrography, depression detection, unsupervised clustering or supervised
  model is implemented. No surface-only method can see occluded entrances.
- The early CLI version concern was a misreading of the `QGIS (3D)` provider
  heading. Packaged CLI/PyQGIS and the live application use 4.2.2; measured
  package versions are in docs/system_packages.txt.

## Next task

Implement an independent native 1 m surface-feature detector with an established
GIS depression-depth/fill tool and a separate cliff/exposure hypothesis. First
inspect native voids, registration/epoch seams and glacial/talus false positives.
Retain feature components and compare predeclared scale/threshold sensitivities
without cave labels. Improve geology detail if safely available. Then finalize
combined rankings and freeze input/output/configuration hashes plus a clean Git
commit. Only after the documented freeze may independent validation start.

See EXPERIMENTS.md for exact outputs, empirical results and commit associations.
