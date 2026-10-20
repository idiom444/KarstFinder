# Experiment ledger

## blind_v001 — exploratory landscape baseline, 2026-10-19

Original execution: **exploratory blind**; now preserved as part of the v002
freeze. Its original run manifest correctly retains its execution-time unfrozen flag. Final numerical implementation: Git `46e1a5c` (clean working tree at execution).
The original foundation is Git `5354ba9`. The run manifest identifies exact
code hashes; the final documentation commit also stores the QGIS project and
small result snapshots.
No known local cave sources accessed. This is an M2 exploratory analysis, not
M3's finalized independent entrance prediction.

Configuration: configs/blind_v001.json. Geographic selection uses a GNIS ridge
point and a 30 km² rectangle. Standardized elevation windows: 210/610/2,010 m.
Source data: 1 m USGS 2019/2021 bare earth, DNR 1:100,000 lithology.

| Observed quantity | Result |
|---|---:|
| Study area | 30.0000 km² |
| Complete 10 m analysis support | 30.0000 km² |
| Mapped marble at 10 m rasterization | 0.2199 km² |
| Mixed melange with possible carbonate | 1.3849 km² |
| Combined-index ≥0.5 area before component filtering | 0.1263 km² |
| Retained landscape components ≥1,000 m² | 6 |
| Total retained area | 0.1241 km² |
| Fraction of study selected | 0.4137% |
| Fraction of mapped marble selected | 56.4347% |
| Independent entrance validation | Not performed |

Most area reduction comes from lithology: 56.4% of mapped marble remains selected.
All six areas have 2021 data available in their 10 m cells; broad neighbourhoods
and seam cells may mix epochs. Native pixel proportions were not measured.
Selection area is an empirical property of the hypothesis; it is not predictive
performance. Largest/rank-one area intersects the southwest study edge and its
extent is censored. Other components occur in mapped carbonate near the ridge.
No component is interpreted as a detected opening. No study extent was changed
to remove the edge candidate or promote the ridge based on expectation.

Persistent local outputs: `results/blind_v001/` contains GeoTIFF components,
`candidates.gpkg`, `candidates.csv`, summary/configuration, source provenance,
run manifest and map preview. `data/processed/` contains 1/10 m buffered DEMs,
source epoch raster and context GeoPackage. The QGIS project uses relative paths
and can be opened independently. Small result records are mirrored under
`docs/experiments/` for Git review; large rasters remain ignored locally.

Verification: seven unit/analytical tests pass; all candidate polygons are
geometrically valid; QGIS save/reopen reports 21 valid local layers. A repeat
run must use a new output directory and compare scientific raster arrays and
ranking attributes, rather than GeoPackage byte identity (SQLite metadata can
vary). Two development outputs are preserved locally as
`results/blind_v001_development_01/` and `results/blind_v001_development_02/`.
A separate repeat in `results/blind_v001_repeat/` reproduced all 18 raster
arrays exactly, byte-identical candidate CSV and identical numerical summary.
The tracked artifact inventory hashes the final numerical outputs, preview,
live canvas render and QGIS file; this inventory is explicitly not a blind freeze.

## Freeze and validation ledger

The initial first-session ledger had no frozen experiment or validation data.
That stage is now superseded by the v002 freeze and public-reference evaluation
recorded below. The original exploratory run files have not been rewritten.

## blind_v002 — complementary native feature analysis

Blind numerical implementation: `bc64030`. Outputs are in results/blind_v002.
The candidate map is finalized before independent local cave sources are read.
The separate freeze record will identify its final implementation/archive commit.

- 76 depression cores and 520 cliff exposures: 596 unverified surface indicators.
- Geological/contact context area: 1.630497 km². Native surface morphology area:
  0.102971 km², before any tolerance buffers or area-budget comparisons.
- Exact native survey provenance and 25 m seam exclusion; no missing native cells.
- Depth-threshold sensitivity 0.3/0.5/1/2 m: 102/76/47/23 objects with unbuffered
  carbonate/melange support. Counts alone do not measure prediction skill.
- Six seeded terrain classes, purely descriptive, with centroids retained.
- Thirteen tests pass, including known flat basin/open outlet, score masks and
  area-budget/uncertainty metrics. Artifact checks verify all 596 geometries,
  point containment and geological/quality support.
- Independent execution reproduced all 13 v002 raster arrays and byte-identical
  indicator rankings. QGIS reopened with 36 valid local layers and two layouts;
  independent provider reads found 76 depression, 520 cliff and 596 point records.

Top-ranked native DEM reviews show surface relief but do not identify openings
or distinguish glacial, talus, vegetation-classification and karst causes.
No cave probability or confirmed entrance is claimed. Model rankings, alternative
explanations and uncertainty fields are retained individually for each object.
Validation will use the predeclared configs/validation_v001.json protocol.


## Frozen v002 public-reference evaluation

Initial freeze: implementation 243b730, 163 file hashes; recorded before local
cave-reference acquisition. See experiments/frozen/blind_v002.json and
 docs/FREEZE_AUDIT.md. The original freeze is unchanged.

Primary protocol: configs/validation_v001.json. Four public map points have
unknown accuracy and one contributor; zero accuracy-qualified entrance records.
A 100 m assumed uncertainty scenario and one historical section-level region
support exploratory coverage comparisons only. At 10% comparable area, central
coverage is geology 1/4, terrain 0/4, v001 1/4, native morphology 4/4, combined
3/4. No 100 m uncertainty region is fully selected at that budget.

A supplemental evaluation audit averages score ties and evaluates 303 rigid
translations of the full reference pattern while preserving geological evidence
classes. It is explicitly post-freeze evaluation work, not a change to predictions
or the primary protocol; no inferential p-values or independent localization
success are claimed. Complete aggregate results are in docs/VALIDATION_REPORT.md,
validation_summary.json, historical_validation_summary.json and validation_audit.json.

The private validation project has 39 valid persistent layers. Detailed local
records are excluded from Git. The current suite has 15 passing tests. M5/M6
are conditional on stronger reference observations; no supervised model or new
prospecting region has been presented as validated.

### Final public-source coverage and reporting audit

A full-study OSM API extract returned the same four records as the initial ridge
subset; import clips the geographic envelope to the projected study bounds.
The comparison denominator is 1.6684 km² on the 10 m maximum-aggregated geology
grid, distinct from the native 1 m mask's 1.630497 km². At 10%, 1,668 cells
(0.1668 km²) are selected. Earlier prose conflated these two resolutions; the
metrics and frozen model did not change. Area denominators are now explicit in
the evaluation JSON. A localization eligibility guard additionally requires
verified source accuracy: assigning a small assumed radius cannot qualify a
record. None of the present references qualifies, so results are unchanged.

The user permanently prohibits contacting anyone. No outreach was sent; the
earlier unsent request is withdrawn and further outreach is not an action item.

## denny_v001 — approved unvalidated prospecting follow-up

User approved southern Denny Mountain on 2026-10-19. Implementation/config
checkpoint 684bf9c. Study 9 km²; unchanged 210/610/2010 m landscape scales,
0.4/0.3/0.3 combined weights, 0.5 m depression threshold and 45° cliff threshold.
Data and results use separate denny_v001 paths; the original freeze is unchanged.

Landscape selects one 0.0667 km² rasterized marble area (the whole lens), with
no boundary clipping. Native 1 m coverage is complete; seam exclusion removes
0.07284 km². Native extraction yields 12 depressions and 477 cliff patches.
Forty-eight cliff patches intersect mapped marble; no retained depression does.
These are surface forms, with no cave-detection claim.

Access screening keeps scientific rank unchanged. All marble-cliff representative
points are 382–560 m straight-line from the official Denny Creek trail, with
steep nearby ground; zero verified hiking-ready approaches. Three possible
on-trail observation points were selected from 34 samples using GDAL bare-earth
viewsheds to the approved Denny marble body only. The initial development
viewshed also counted a buffered neighboring marble fragment; that evaluation
was corrected to target polygon 29438, retained separately under ignored
results/denny_v001_observation_development_01, and never used as cave evidence.
The terrain-only viewshed omits forest, snow and actual tread alignment.

Independent runs match all 18 landscape and 13 feature raster arrays plus both
ranking CSVs. All 489 feature geometries/support checks pass. Three OBS points
are on source trail geometry; the 28-layer project reopens in a fresh process
with expected counts and no private/reference layers. Fifteen tests pass.
Final headless generation uses read-only IMMUTABLE GPKG connections to avoid
transient SQLite reopen errors seen with mutable providers; final build log clean.
Live QGIS map and native review images were inspected. Mutable provider access
changed feature/access GeoPackage bytes before finalization; every SQLite table
row matches an independent repeat except expected creation timestamps. Initial
run hashes are retained and post-review hashes recorded in the final snapshot.
See denny_v001_provider_audit.json; no numerical raster or ranking CSV changed.

See docs/DENNY_RESULTS.md and docs/experiments/denny_v001_*.json for complete
results/provenance. An incidental unopened caving-newsletter search snippet
appeared during access research and is recorded; no Denny entrance source was
used in modeling. The area overlaps the old study edge. This is not an
independent blind holdout or a validated M6 expansion. No outreach occurred.

## Documentation and numerical traceability review — 2026-10-19

At the user's request, the implemented methodology and Denny cliff-priority
evidence are documented in METHODOLOGY.md without further prospecting, external
research or cave-reference access. The review script reads saved polygons and
raster pixels and preserves byte-identical candidate/access/landscape CSVs and
configuration copies under docs/reviews/denny_v001_methodology/.

All 489 core object summaries and score decompositions match the saved values;
maximum numerical difference 1.1102230246251565e-16. Declared deterministic overall
and per-method rank order matches. Existing Denny snapshot (144 hashes) and
Cave Ridge freeze (163 hashes) verify before and after the review. The review
is arithmetic/provenance verification, not predictive validation or new cave
evidence. No candidate, supporting measurement, threshold or geometry changed.
The field carbonate_fraction is explicitly documented as positive geological
support fraction, not measured carbonate-rock percentage. A worked C1 example
separates its fixed geological/terrain/morphological contributions from the lack
of detected depression, entrance or verified access.


## kaleetan_v001 / marble_v001 — approved regional prospecting, 2026-10-19

The user approved both proposed 3 × 3 km windows after public cave-specific
literature screening. These are literature-informed, unvalidated transfers of
the existing numerical hypotheses, not independently blind validation. No cave
entrance records or private archive were used. Thresholds, weights, scales,
component limits and ranks were not tuned. PMmb(e) and TRmb(e) are explicitly
mapped to the same established marble class by a tested regional vocabulary
adapter; the frozen original implementation remains unchanged.

| Result | Kaleetan | Marble Peak |
|---|---:|---:|
| Landscape zones | 1 | 1 |
| Selected landscape area | 3.12 ha | 1.09 ha |
| Total surface indicators | 808 | 1,525 |
| Cliffs / depression cores | 773 / 35 | 1,517 / 8 |
| Cliff patches intersecting mapped marble | 2 | 5 |
| Depression cores intersecting mapped marble | 0 | 0 |
| Independent repeat raster arrays matched | 31 | 31 |
| Complete preserved ranking CSVs matched | 2 | 2 |
| GeoPackage layers with matching geometries / attributes | 3 | 3 |
| Saved-pixel audit maximum discrepancy | 1.11e-16 | 5.55e-17 |

Marble Peak's original selected USGS tiles had no data over the mapped marble.
A separately acquired public PSLC 2013 3 ftUS bare-earth source provides complete
combined coverage after GDAL reprojection/explicit height-unit conversion. The
accepted source-year mosaic and 25 m seam exclusion are retained; 0.226744 km² of
the Marble study is excluded from feature selection. All marble cells themselves
are eligible 2013 data, at least 107 m from a seam. Overlap differences and rejected
source coverage are documented, without fitting offsets or changing the study
boundary. Marble C754 has only ~3 m² carbonate overlap and is retained at its
original low rank, not promoted to match the four wholly overlapping patches.

Persistent results are in `results/{kaleetan,marble}_v001_*`, with full-precision
additive reviews in `docs/reviews/{kaleetan,marble}_v001_methodology/`. New snapshots
in `experiments/snapshots/` pin source/code/data/rank/map hashes and protect final
numerical folders. Each independent QGIS map has 31 persistent layers, an overview
and a marble-detail layout, and no entrance-reference overlays. Library IDs are
`kaleetan-vicinity` and `marble-peak`, both Not yet investigated. The four original
archived maps and the original 163 + 144 frozen entries are preserved.

See [the full results and map key](docs/APPROVED_AREAS_RESULTS_20261019.md) and
[execution/source record](docs/APPROVED_AREAS_20261019.md). Reproducibility and score
arithmetic checks do not validate cave prediction or certify hiking access.


### Additive Marble provider finalization

The first Marble snapshot is retained as pre-review evidence. A subsequent QGIS
provider reopen changed only the prepared context GeoPackage's container hash.
A fresh raw-source reconstruction matches every layer schema, attribute and exact
geometry; all other 152 initial hashes, scores and rankings match. The additive
current integrity record is `experiments/snapshots/marble_v001_reviewed.json`.
Prepared context files are now read-only. No numerical model or candidate changed.
[Provider audit details](docs/MARBLE_PROVIDER_REVIEW_20261019.md) document the
preserved initial record and limits on attributing the exact byte-level change.


## Enhanced v001 prospecting union

`configs/enhanced_v001.json` defines separate four-area inputs, output paths,
exact five-stop continuous colors, conservative correlation-family aggregation
and optional-data budgets. Numeric outputs live in `results/enhanced_v001_AREA/`
and prepared measurements in `data/processed/enhanced_v001/AREA/`. Original
experiments are untouched. All original candidate IDs, ranks, scores, coordinates
and geometries are retained alongside enhanced strength and source evidence.

The [comparison](docs/enhanced_v001/COMPARISON.md), per-area acquisition/terrain/
registry manifests, independent [verification](docs/enhanced_v001/verification.json)
and `experiments/snapshots/enhanced_v001.json` provide the audit trail.
The enhanced snapshot is unvalidated prospecting, not a blind cave experiment.
New scientific revisions require new names/paths. Separately saved Library IDs
end `-enhanced-v001`; older entries still open the original analyses.
