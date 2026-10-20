# Carbonate v001 results — 2026-10-20

The scientific eligibility gate reduces 15,804 enhanced v001 observations to 308 within documented marble or its explicitly flagged 25 m margin. Those form **62 local surface prospecting sites**; ordinary drainage adds context only. These are unvalidated hypotheses, not discovered caves. No new geographic data or cave records were acquired.

| Area | Previous enhanced observations | Scoped observations | Surface sites | Boundary-only sites | Unattached drainage context |
|---|---:|---:|---:|---:|---:|
| Cave Ridge | 7,117 | 212 | 57 | 11 | 7 |
| Denny Mountain | 2,625 | 78 | 3 | 1 | 0 |
| Kaleetan Peak vicinity | 2,071 | 3 | 1 | 0 | 0 |
| Marble Peak / upper Marble Gulch | 3,991 | 15 | 1 | 0 | 0 |

These are newly scoped components, not a one-to-one filtering of the old registry: detection and minimum-area filtering now follow geological masking and quality screening. All old features remain in their original registries. Cave Ridge and Denny overlap geographically, so totals are records, not necessarily distinct physical features. There is no top-N cap or hidden score threshold.

## Geological extent and uncertainty

| Area / polygon | Mapped marble (m²) | Marble + 25 m margin (m²) | Native surface components at 0 / 25 / 50 m margins |
|---|---:|---:|---|
| Cave Ridge / 29438 | 64,196.9 | 99,964.6 | 57 cliffs, 0 depressions / 68 cliffs, 0 depressions / 83 cliffs, 0 depressions |
| Cave Ridge / 29439 | 155,099.0 | 219,328.0 | 63 cliffs, 19 depressions / 86 cliffs, 31 depressions / 102 cliffs, 50 depressions |
| Denny Mountain / 29438 | 66,428.6 | 107,304.8 | 59 cliffs, 0 depressions / 69 cliffs, 0 depressions / 89 cliffs, 0 depressions |
| Kaleetan Peak vicinity / 29440 | 31,323.3 | 54,906.1 | 3 cliffs, 0 depressions / 3 cliffs, 0 depressions / 4 cliffs, 0 depressions |
| Marble Peak / upper Marble Gulch / 741 | 10,907.6 | 23,352.5 | 7 cliffs, 0 depressions / 15 cliffs, 0 depressions / 19 cliffs, 0 depressions |

The contact margin is an assumption, not measured contact accuracy. Surface component counts precede local-site grouping; exact clipping/minimum-area checks can remove a raster component. The active analysis uses 25 m, not the sensitivity alternatives. All four areas have documented marble; **geological evidence is insufficient outside these listed bodies and to establish carbonate purity, detailed exposure boundaries, underground continuity or caves within them**. Broad mélange polygons are not targets.

## Representative leading sites

Coordinates below are computed surface reference points (WGS84 decimal degrees), not known cave locations. A priority of 1 means the ordinal terrain index saturates, not a probability or demonstrated entrance. Stable IDs resolve to full measurement and membership records.

| Area | Site ID | Latitude | Longitude | Priority | Supporting observations |
|---|---|---:|---:|---:|---:|
| Cave Ridge | `cave-ridge:S-0d1ce80973430111` | 47.4511742 | -121.4062993 | 1.0000 | 2 |
| Denny Mountain | `denny-mountain:S-f3ebb0ee1e2ea0b3` | 47.4280627 | -121.4456705 | 1.0000 | 76 |
| Kaleetan Peak vicinity | `kaleetan-vicinity:S-37ffb871a52586c5` | 47.4610957 | -121.4809198 | 1.0000 | 3 |
| Marble Peak / upper Marble Gulch | `marble-peak:S-1011ba0db0a2775f` | 48.0575471 | -121.5703653 | 1.0000 | 15 |

Denny’s leading site is a connected local exposure system with 67 cliff patches and nine attached drainage-context patches, not 76 independent confirmations or one predicted opening. Its complete footprint makes the extent explicit. The other two Denny sites remain inspectable: one boundary-only cliff (priority 0.35), and one weak mapped-core cliff (about 0.2993). Kaleetan and Marble have single-method cliff support; this is retained rather than requiring artificial agreement between DEM-derived methods. Neither has a qualifying depression in this corrected scope.

Cave Ridge retains many separate small surface sites because mapped marble contains distinct cliff patches and closed-depression hypotheses. The 57 sites are concentrated in two mapped marble bodies rather than scattered over the whole landscape; 11 are boundary-only and lower priority. The primary map draws every site. It does not hide high counts by scale or silently remove weak features.

## Records, maps and recovery

The [methodology](METHODOLOGY.md) describes every gate, threshold, score and coordinate rule. [Workflow](WORKFLOW.md) explains map use. Per-area `*_summary.json`, `*_manifest.json` and `*_map.json` accompany these results. The local GeoPackage and CSV/JSON files under `results/carbonate_v001_AREA/` preserve every scoped observation, source-ID link, coordinate, pixel summary, alternative explanation, connecting edge and membership. These large/local files require the existing shared datasets and are not a standalone Git data package.

The [review export](review_records.json) preserves all site ranks/coordinates/supporting IDs and all scoped observation measurements in Git for independent review. Original enhanced geometry remains in the unchanged prior registry; corrected geometry is in `observation_footprints`, with a per-observation normalized geometry hash. Read [verification](verification.json) for actual audit results and the new snapshot for all hashes.

## Limitations

Terrain residuals and depressions are not diagnostic of caves. Glacial landforms, ordinary rock faces, talus, landslides, forest, snow, interbeds, DEM artifacts and airborne overhang occlusion remain unresolved. Relative rank cannot establish performance without reliable independent observations. Previous literature exposure remains recorded; these studies are not independent blind holdouts. No route or legal/safe access has been established, and these outputs do not recommend a hike. Existing original and enhanced Library entries and all frozen experiments remain unchanged.
