# Experiment ledger

## blind_v001 — exploratory landscape baseline, 2026-10-19

Status: **UNFROZEN, blind**. Implementation foundation: Git `5354ba9`; later
candidate metadata/reporting refinements are committed separately. The run
manifest identifies the exact code hashes and commit used for its execution.
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
| Independent entrance validation | Not performed |

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
vary). The first development output is preserved locally as
`results/blind_v001_development_01/` after candidate metadata refinements.

## Freeze and validation ledger

No frozen experiment exists. No cave validation data have been acquired.
Commit and output hashing during exploration do not authorize validation.
Complete M3 and follow AGENTS.md before creating the first freeze manifest.
