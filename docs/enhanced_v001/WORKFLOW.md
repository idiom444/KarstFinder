# Enhanced workflow and saved-map use

Use the existing system-site-packages `.venv`; do not install binary GIS wheels into system Python. Required software remains QGIS/GDAL/WhiteboxTools, NumPy/SciPy and Requests. PDAL is optional; its absence leaves the DEM analysis usable. No paid service/account or outreach is required.

## Open a completed map

Use QGIS **Project → Open** with the stable library project, or:

```bash
./library open denny-mountain-enhanced-v001
./library open kaleetan-vicinity-enhanced-v001
./library open marble-peak-enhanced-v001
./library open cave-ridge-enhanced-v001
```

The original IDs without `-enhanced-v001` still open the original analyses. Library opening backs up dirty sessions and refuses pending layer edits. Each enhanced entry has a stable `.qgz` under `prospecting_library/AREA_ID/`, a version archive and fresh-process verification. The independently generated research projects also live under `qgis/KarstFinder_BASE_AREA_ID_enhanced_v001.qgz`. All are local persistent maps requiring the shared ignored data/results; Git alone is not a portable dataset bundle.

All retained points are initially visible. Expand **Measured components**, **Independent method views**, **Geological zones + structure**, and **2023 native RGB/NIR** to inspect the evidence. Identify a point to read its ID, coordinates, scalar strength, separate confidence, alternative explanations and JSON measurement fields. Use **Project → Layouts → Enhanced overview / Enhanced carbonate_detail** for the saved continuous legend and geological detail views. Main points are feature representatives, never detected entrances.

Filters affect the live main points and footprint views without changing the registry or independent method layers:

```bash
.venv/bin/python scripts/enhanced_filter.py --min-strength .4
.venv/bin/python scripts/enhanced_filter.py --geology mapped_carbonate
.venv/bin/python scripts/enhanced_filter.py --min-geological-confidence .5 --method terrain_cliff
.venv/bin/python scripts/enhanced_filter.py --zone 'denny-mountain:DNR100k:29438'
.venv/bin/python scripts/enhanced_filter.py --status 'Not yet investigated' --availability imagery
.venv/bin/python scripts/enhanced_filter.py --availability pointcloud
.venv/bin/python scripts/enhanced_filter.py --reset
```

Native QGIS Query Builder offers the same reversible filtering on any attributes. Saving a filtered view creates a new library map revision; it does not delete hidden candidates. Strength colors always use the original absolute 0–1 scale, never a filtered min/max stretch. Confidence is separately shown with marker outlines. Shapes distinguish feature types.

Record personal observations through the unchanged `./library note` workflow using the enhanced area ID and exact candidate ID, or retain original notes under their original area/ID. The enhanced registry includes `baseline_object_id`, `field_note_link` and original prediction checksum; original private note files are untouched. Notes are ignored by Git and are not silently copied into public attributes. Prediction-time status fields are a saved snapshot, while private observations and later Library status revisions retain their own history.

## Reproduce or revise

Completed terrain/registry runs refuse overwrite. The commands below describe the original stage order for an area on an empty output tree; they must not be used to overwrite a finalized experiment. A scientific revision needs a new config/version and new data/results/project/library IDs. The v001 config is deliberately fixed; clone/version the workflow references when introducing a v002 experiment.

```bash
.venv/bin/python scripts/enhanced_acquire_geology.py denny-mountain
.venv/bin/python scripts/enhanced_pointcloud.py denny-mountain
.venv/bin/python scripts/enhanced_terrain.py denny-mountain
.venv/bin/python scripts/enhanced_acquire_imagery.py denny-mountain
.venv/bin/python scripts/enhanced_run.py denny-mountain
.venv/bin/python scripts/enhanced_map.py denny-mountain
.venv/bin/python scripts/enhanced_register.py denny-mountain
```

Repeat for `cave-ridge`, `kaleetan-vicinity`, `marble-peak`. Optional point-cloud/imagery failures write explicit fallback reports and leave the numerical DEM path enabled. Completed successful optional acquisitions are hash-checked and retained. Failed/incomplete caches must be inspected and archived before replacement. Catalog completeness and budgets are checked; arbitrary bulk downloads are not used. Download timestamps and metadata serialization can vary on reacquisition; scientific reproducibility is assessed against saved input hashes and tool versions, not an assertion that web services never change.

A fresh clone must first recreate/restore the original baseline terrain and public geology using the repository's original workflows and source manifests, then acquire the enhanced inputs. The new registry intentionally depends on preserved baseline outputs; it does not bypass the original terrain-quality checks.

After all four runs:

```bash
.venv/bin/python scripts/enhanced_compare.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_approved_snapshots.py
.venv/bin/python scripts/enhanced_verify.py
.venv/bin/python scripts/enhanced_freeze.py --verify
./library verify denny-mountain-enhanced-v001
```

`enhanced_verify.py` independently checks original IDs/coordinates/ranks/scores/geometries, recomputes score aggregation/colors, checks manifest hashes and reopens all enhanced library entries. `enhanced_freeze.py --verify` checks the final enhanced snapshot. Do not recreate a frozen snapshot; new experiments get new names. The older Marble pre-provider-review container mismatch is retained and explained by the original provider audit, not erased by this upgrade.

## Backup and development records

Back up the complete repository including ignored `data/`, `results/`, personal library `local/` folders and referenced photos. Native LiDAR LAZ is retained under the enhanced point-cloud processed directory and can be opened separately; Library maps use persistent GeoTIFF derivatives because the unchanged Library verifies GDAL/OGR layers.

Development-only directories ending `_development_01` / `_development_02` retain interrupted or corrected preliminary runs. They are excluded from final references and the enhanced snapshot. They include an early imagery nodata correction, an explicit Whitebox CLI parameter correction, a prototype map CRS-constructor correction and an empty-point-bin availability correction. No frozen original or final ranking was overwritten during these development corrections. The final selected output paths are the ones in the v001 config and library catalog.

Complete original method components and access-screening measurements are also
preserved without numeric conversion in each result directory's
`baseline_measurement_records.json`, keyed by the enhanced area-prefixed ID.
Its source checksum points to the unchanged original ranking CSV. This additive
record does not alter the new map dataset or its strengths. Regenerate it once
on a fresh experiment with `scripts/enhanced_baseline_records.py`.

Additional point-cloud source discovery, the DNR portal HTTP 403 limitation,
public EPT bounds/overlap tests and targeted tile sizes are retained in
`pointcloud_discovery.json`. A catalog label does not establish a usable bounded
point-cloud acquisition; unavailable optional sources do not imply missing caves.
