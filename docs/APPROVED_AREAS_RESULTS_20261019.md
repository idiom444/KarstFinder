# Kaleetan and Marble Peak results — 2026-10-19

Both user-approved 3 × 3 km studies are complete as **literature-informed,
unvalidated prospecting**. These are hypotheses about terrain and mapped rock,
not cave probabilities, detected entrances or evidence that nobody has explored
an area. No cave inventory, known-entrance overlay or private validation archive
was used in these models. Nobody was contacted.

| Measurement | Kaleetan Peak vicinity | Marble Peak / upper Marble Gulch |
|---|---:|---:|
| Approved study area | 9 km² | 9 km² |
| Complete 10 m landscape support | 9 km² | 9 km² |
| Surface-indicator eligible area after seam exclusion | 9 km² | 8.773256 km² |
| Mapped marble at 10 m rasterization | 3.13 ha | 1.12 ha |
| Retained landscape hypothesis areas | 1 | 1 |
| Retained landscape area | 3.12 ha | 1.09 ha |
| Ranked cliff patches, all geological support | 773 | 1,517 |
| Ranked depression cores, all geological support | 35 | 8 |
| Total ranked surface indicators | 808 | 1,525 |
| Cliff patches intersecting mapped marble | **2** | **5** |
| Depression cores intersecting mapped marble | **0** | **0** |
| Verified routes / confirmed caves | 0 / 0 | 0 / 0 |

The large full-table counts include uncertain mixed-melange and contact-buffer
support. They must not be described as hundreds of likely caves on mapped marble.
The landscape threshold selects nearly the whole mapped lens at both sites
(99.68% and 97.32% at 10 m), so that stage provides little localization within the
lens. The smaller surface patches remain nondiagnostic exposure hypotheses.

## Persistent maps

- [Kaleetan saved map](../prospecting_library/kaleetan-vicinity/kaleetan-vicinity.qgz)
  — `./library open kaleetan-vicinity`.
- [Marble Peak saved map](../prospecting_library/marble-peak/marble-peak.qgz)
  — `./library open marble-peak`.

Each map has a full-area overview and a marble-detail print layout. It opens at
the small marble lens so the indicators are readable; the approved 9 km² boundary
and overview are retained. Purple outlines are approximate mapped marble, purple
dots are representative points of intersecting patches, and orange polygons are
the actual footprints. Labels preserve original kind ranks (C for cliff, D for
depression). Hidden layers retain all ranked objects and terrain components.
No entrance-reference X marks, red uncertainty circles or private layers are
included. Both fieldwork statuses are **Not yet investigated**.

[Previews: Kaleetan overview](experiments/kaleetan_v001_overview.png),
[Kaleetan detail](experiments/kaleetan_v001_marble_detail.png),
[Marble overview](experiments/marble_v001_overview.png),
[Marble detail](experiments/marble_v001_marble_detail.png).

Original named source projects are `qgis/KarstFinder_Kaleetan_v001.qgz` and
`qgis/KarstFinder_Marble_v001.qgz`. Library versions preserve subsequent review
maps separately. All projects require the shared local data/results; the public
Git repository is not a standalone data backup.

## Specific marble evidence

Kaleetan's C1/C2 are 36 m² and 43 m² cliff patches, with mean slopes 47.406° and
46.530° and ordinal scores 0.721928 and 0.680599. Both intersect mapped marble
throughout their footprints. They are about 1.34–1.35 km straight-line from the
nearest mapped USFS trail; that is not a route. No direct approach is proposed.

Marble Peak's C1–C4 are 231, 74, 47 and 31 m² cliff patches wholly inside mapped
marble, with ordinal scores 0.749652, 0.701222, 0.690136 and 0.675608. The fifth
intersecting patch is **C754**, global rank 757, 51 m² total area, only 2.994930 m²
of mapped-marble overlap and score 0.471341. It is a weaker contact-edge hypothesis,
not a fifth equally strong marble exposure. All five representative points have
mapped USFS ownership, but no official USFS trail features were returned in the
query window. That does not establish that no trails or other paths exist.
Ownership geometry does not certify a legal boundary or public access.

Full-precision measurements, original IDs/ranks and score decompositions:
[Kaleetan evidence](reviews/kaleetan_v001_methodology/direct_marble_evidence.md),
[Marble evidence](reviews/marble_v001_methodology/direct_marble_evidence.md).
Each review directory also preserves the exact full ranking/access CSVs and
configurations, plus `score_audit.csv` and `review_manifest.json`.

## Terrain coverage and limitations

Kaleetan's study uses 2021 USGS LiDAR throughout. Marble Peak combines PSLC 2013,
USGS 2016 and USGS 2021 data with newest-valid precedence. The processing buffers
and study windows have complete numerical elevation coverage; no void filling or
coarse-data substitution was needed. The original failed Marble preparation is
retained as `data/processed/marble_v001_rejected_partial_01/`.

All 10,922 native-grid marble cells at Marble Peak use the 2013 source and pass
the 25 m seam exclusion; their nearest survey seam is 107 m away. The wider study
excludes 0.226744 km² around survey transitions. In 10 m-stride overlap samples,
2016 minus 2013 has median −0.074585 m and 95th-percentile absolute difference
2.186447 m (63,806 samples); 2021 minus 2013 has median −0.186874 m and corresponding
95th percentile 1.443198 m (28,952 samples). The 2016/2021 pair has no sampled
overlap. These differences combine temporal change, sampling, registration and
surface-processing effects; they are not independent measurements of accuracy.
No bias correction was fitted. Source-year masks, all pairwise overlap summaries
and explicit source-unit conversion checks remain available for inspection.

The original 1 m USGS tiles and a Glacier Peak OPR crop were rejected as complete
coverage sources before scoring. The PSLC archive passed CRC verification; GDAL
reads its explicitly named 32-bit bare-earth elevation raster. Its legacy HARN
WKT was checked against supplier-declared EPSG:2926, including interchangeable
Lambert standard parallels and sub-millifoot false-easting rounding. Heights are
converted from US survey feet with 1200/3937. 110 sampled output/source pixel
comparisons verify that GDAL preserved foot heights before this explicit scale.
The complete records are `marble_v001_pslc_{acquisition,conversion}.json` and
`marble_v001_{data_quality,marble_quality,coverage_screening}.json` under
`docs/experiments/`. Inherited `elevation_project`, `fallback_elevation_project`
and `dem_raw_dir` fields are unused legacy metadata; `elevation_sources` and the
regional preparation records specify the actual inputs.

Glaciation, talus, landslides, ordinary rock faces, vegetation, snow and overhead
occlusion remain material limitations. Absence of a modeled depression or low
ordinal score is not evidence of cave absence. No field destination or route is
certified; current land-manager rules would need checking for an actual trip.

## Verification and preservation

Independent repeat model runs match **31 raster arrays, both ranking CSVs and
three GeoPackage layers per area** exactly (geometries/attributes compared rather
than SQLite file bytes). Saved-pixel audits reconstruct every score and supporting
measurement: 808 Kaleetan and 1,525 Marble objects, maximum discrepancies
1.1102230246251565e-16 and 5.551115123125783e-17. All representative points lie inside
their original polygons, all retained objects pass their quality masks, ranks
follow the declared deterministic ordering, and the access screen preserves all
original scientific fields.

New snapshots under `experiments/snapshots/{kaleetan,marble}_v001.json` pin source,
prepared-input, result, review and named-map hashes. They are unvalidated
prospecting snapshots, not independent blind freezes. Final numerical result
folders are protected against accidental overwrites; future numerical revisions
need new experiment names/paths. Cave Ridge's 163 frozen entries, Denny's 144
snapshot entries, its preserved methodology review and all four original archived
QGIS projects remain unchanged. Fresh QGIS reopening and library verification
check the full candidate tables and persistent data dependencies.
