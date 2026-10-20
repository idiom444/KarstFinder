# Implementation verification, 2026-10-20

This verifies the corrected implementation and preserved records. It is **not
validation of cave-finding skill**: no independent cave reference dataset was used.

* **50 tests pass**: [record](TESTS.txt), including carbonate eligibility, legitimate
  single-method surface leads, robust local statistics, spatial connectors,
  separate formations, non-bridging drainage, drainage-only exclusion, stable
  grouping and exact ramp behavior inherited from the preserved implementation.
* [Independent saved-output audit](verification.json): all 308 observation geometries
  lie within the admitted marble/contact scope; 1,848 key native statistic records
  were recomputed from slope, depth, quality and three residual scales. Priorities,
  actual source intersections, original geometry hashes, source IDs, waypoint
  membership, membership tables, site scores and original Library entries match.
* All four new Library projects were captured and reopened in fresh QGIS processes.
  Dataset hashes, layers, attribute types, geometries, styles, layouts, rankings,
  candidate coordinates and visibility match the saved state. Every primary site
  is unfiltered; no scale-based visibility suppresses a candidate. Every scoped
  individual observation remains recoverable.
* [Map review](map_review.json): each Library entry was opened in live desktop QGIS
  with its normal dirty-session protection. All layers are valid, CRS is EPSG:26910
  and projects open clean. Regional (~1:14,173–23,622), formation (~1:2,835–5,001)
  and close (~1:945) renders were inspected. The default formation views show 57,
  3, 1 and 1 sites respectively; Cave Ridge's default focuses on its larger marble
  body and its other body is included in a separate saved detail layout. The
  regional Cave Ridge view resolves two marble targets; individual labels naturally
  need the formation/detail view. Close review explicitly enabled the observation
  layer and recovered its original individual marker geometry.
* Exact saved marker color expressions and continuous raster-legend stops match
  #440154, #3b528b, #21918c, #5ec962, #fde725 at 0/.25/.5/.75/1, with an absolute
  0–1 range. No quantiles or area-relative rescaling are used.
* The old eight Library catalog entries and stable project aliases are unchanged.
  All prior freeze/snapshot entries pass: blind v002 163, Denny 144, Kaleetan 149,
  reviewed Marble 156 and enhanced v001 541 (1,153 hash entries across snapshots).
  The previously documented pre-review Marble container difference remains in its
  old archive; this correction does not rewrite that historical record.

No cave locations or private records were looked up, no geographic data was
downloaded, and no person was contacted. Current geological uncertainty outside
the admitted bodies and within-unit exposure/purity limitations are reported in
[results](RESULTS.md). Numerical results are frozen separately as carbonate v001;
future scientific changes require new names and paths.
