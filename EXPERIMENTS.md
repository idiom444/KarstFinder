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
