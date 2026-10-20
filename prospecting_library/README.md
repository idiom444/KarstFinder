# Prospecting Library

## Current carbonate prospecting entries

Use `cave-ridge-carbonate-v001`, `denny-mountain-carbonate-v001`,
`kaleetan-vicinity-carbonate-v001` or `marble-peak-carbonate-v001` for the current
geologically restricted maps. They contain 57, 3, 1 and 1 local sites respectively,
with inspectable underlying observations and unchanged exact priority colors.
The eight original/enhanced entries remain historical archives with all their
rankings and geometries. [Current workflow](../docs/carbonate_v001/WORKFLOW.md)
explains membership, geology, source-ID recovery and interpretation.

Open [Denny Mountain](denny-mountain/denny-mountain.qgz) or
[Cave Ridge](cave-ridge/cave-ridge.qgz) in QGIS with **Project → Open** (or
double-click the `.qgz` file). No Codex session, MCP connection, downloads, or
analysis run is required. The existing local datasets must remain available.

**These are reopenable local projects, not self-contained portable packages.**
GitHub contains the projects and catalog, but excludes the large terrain/results
and all private validation data. A Git clone alone cannot display the maps.

## Daily workflow

You can ask Codex “save Denny Mountain to the library,” “open Cave Ridge,” or
“record a note against Denny candidate C-007851.” The same operations are available
from the repository's small `./library` command:

```bash
./library list
./library open denny-mountain
./library save denny-mountain
./library update denny-mountain --status "Planned for a trip"
./library note denny-mountain --candidate C-007851 --text "Review on a future visit"
./library notes denny-mountain --candidate C-007851
./library verify denny-mountain
```

`open` and the default `save` use the existing localhost QGIS MCP plugin on
port 9876. All other commands, including verification, work without a running
desktop QGIS session (the installed PyQGIS environment is still required).
Run `/path/to/KarstFinder/library ...` from another directory if needed.

`save` captures the **currently displayed** QGIS project, including its current
canvas extent, center, CRS, rotation, layer tree, visibility, styles, transparency,
labels, print layouts, and annotations. Use the correct area's ID. It preserves
the live session's original filename and dirty state and does not overwrite the
original project. Save/discard pending **layer edits** first; the library will
not commit edits to scientific data on your behalf. Persist temporary/memory or
remote layers to local GeoPackage/GeoTIFF files before saving.

Each save creates a new `map-vNNNNNN.qgz` archive and verification record. The
stable `denny-mountain.qgz` filename points to the latest saved map via an ordinary
file copy in the same directory; opening an older archive also works directly.
Metadata-only updates create JSON revisions and leave every map unchanged.
The original projects under `qgis/` and all frozen experiments remain intact.

Opening through MCP checks the datasets first and backs up any dirty live project
under `.sessions/` before replacing it. Pending vector edit buffers prevent
replacement. Manual **Project → Open** uses QGIS's ordinary save prompt instead.
If you manually save changes to a library `.qgz`, register those edits with
`./library save denny-mountain` while it is open (or use `--project` below).
Until then, `verify` reports that the current project differs from its archive.

## Catalog and saved data

`index.json` is the current structured catalog: one record per area. Each record
has a stable ID, name, general location, study extent/CRS, creation/update times,
geological summary, candidate count and top ten original ranks, project path,
dataset paths/hashes, analysis/configuration references, fieldwork status, and a
path to personal notes. `versions/vNNNNNN.json` preserves previous catalog records.
IDs are unique lowercase names such as `denny-mountain`.

```text
prospecting_library/
  index.json
  denny-mountain/
    specification.json              # metadata used to register the area
    denny-mountain.qgz               # latest map; open this manually
    map-v000001.qgz                 # original saved map; never overwritten
    versions/
      v000001.json                  # catalog record at this revision
      v000001.state.json            # captured view/style/feature fingerprints
      v000001.verification.json     # fresh-process counts and required files
    local/field_notes.json          # personal observations; ignored by Git
  cave-ridge/                       # independent frozen-prediction map
```

Study extents are in the catalog, and study-boundary polygons already exist in
the saved QGIS projects. A second boundary database is unnecessary for these
entries. Large rasters and candidate GeoPackages stay shared under `data/` and
`results/`; saving a map does not duplicate them.

Both current entries begin **Not yet investigated**, which records fieldwork
progress only. Other supported statuses are **Planned for a trip**, **Partially
explored**, **Explored**, **Follow-up needed**, and **Archived**. They never establish
whether a cave exists. No field visits or observations were invented during setup.

## Candidates and field notes

In QGIS, use **Identify Features**, or open the attribute table of **All indicators
• geological rank + access flags** in Denny. `object_id` identifies each original
candidate; `rank`, `score`, evidence, geology/terrain/morphology components,
coordinates, slope, depth, residual and access flags remain available. The top-ten
layer is a filtered view of those same features. Cave Ridge's representative-point
and surface-indicator layers similarly retain their original attributes.

```bash
./library candidate denny-mountain C-007851
./library note denny-mountain --candidate C-007851 \
  --text "Describe only what was actually observed" \
  --visited yes --rock-type "field identification" \
  --features "describe geological features" --possible-opening unknown \
  --follow-up yes --photo "/path/to/photo.jpg"
```

These are examples, not recorded visits or route recommendations. Omit
`--candidate` for an area-level note. Photos may be paths or external references;
the command does not upload or copy them. All observation fields support unknown
values; “not visited” is `--visited no`. Area notes and candidate notes live in
the same ordinary local JSON file, associated by `candidate_id` and the original
map revision/ranking checksum. They are deliberately separate from QGIS prediction
tables and are not automatically displayed as map layers.

To correct an observation, use `--revise OBSERVATION_ID` with the same candidate
and the complete corrected fields. It appends a revision and retains the previous
event. `notes` shows the full history. Back up `local/` yourself: Git excludes it
to keep personal field evidence, possible openings, photo references and notes
out of the public repository. Avoid putting private observations in tracked
specification or catalog files. A failed search does not establish cave absence
or invalidate a geological hypothesis.

## New areas and updated analyses

Use a new ID and a small metadata specification, following either existing
`specification.json`: name, general location, study extent (`crs` and four bounds),
geological summary, candidate CSV, and analysis references. Paths in metadata are
relative to the repository root. Candidate CSVs use the existing KarstFinder
`object_id`, `rank`, `score`, `kind`, `easting` and `northing` fields.
Landscape CSVs using `candidate_id` and `mean_score` also work; headings are
normalized in the catalog without altering the original file. Empty candidate
tables are supported. For an unranked area, omit `candidate_csv` or set it to
`null`: its catalog count is unknown and area-level notes still work. When a
candidate CSV is provided, saving verifies its IDs, ranks, scores and coordinates
against a complete loaded candidate layer, preventing an accidental area/map mix-up.

```bash
./library save new-area --spec /path/to/new-area-specification.json
# Register a saved .qgz instead of capturing live QGIS:
./library save new-area --spec /path/to/new-area-specification.json \
  --project /path/to/existing-analysis.qgz
```

For later map changes, use `save AREA_ID` again. For genuinely new scientific
results, first create a separately named experiment/output directory under the
existing research rules; pass an updated `--spec` with the new references when
saving. Old map archives and metadata retain the previous references. Observations
retain their original prediction association. This feature never reruns an
analysis or changes rankings. Private validation layers are rejected before
opening source projects and cannot be registered.

## Backup, moving and missing paths

The `dataset_references` in each catalog entry and verification JSON list the
exact local files used by every layer, including GeoPackages, GeoTIFFs, GDAL
sidecars and transitive VRT dependencies when present. `candidate_csv` and
`analysis_references` also identify records needed to inspect/review the analysis.
For Denny, retain:

- `data/processed/denny_v001/` and `data/raw/naip2017_rgb_2m.tif` with sidecars.
- `results/denny_v001_landscape/`, `denny_v001_features/`, `denny_v001_access/`
  and `denny_v001_observation/`.
- The referenced configurations, manifests and review documentation.

Back up the whole repository **including ignored data/results and library local
notes**, together with referenced photos. Copying only `prospecting_library/`
does not include the shared datasets. To retain the same map on another computer,
keep the relative `prospecting_library/`, `data/` and `results/` structure, install
compatible QGIS/fonts, and run `./library verify AREA_ID`. External absolute
datasets and photo references need separate backup/path repair. The original
raw DEMs and other research inputs referenced by experiment manifests should also
be retained for full scientific reproducibility, even when not directly rendered.

`verify` reports missing dataset paths explicitly; no download or model rerun is
attempted. Restore those files from backup to their recorded relative locations.
If files were intentionally relocated, open a **copy** of the saved project in
QGIS, use **Handle Unavailable Layers** to repair paths, save it under a new name,
then register that copy with `save AREA_ID --project ...` and update `--spec` if
the analysis/CSV paths changed. Preserve the old archive and do not repair paths
by editing frozen original projects or their manifests.

Map extents/centers are preserved in map units. QGIS fits the extent to the window
shape, so a different screen aspect ratio can show extra surroundings. Installed
QGIS, fonts, and externally referenced styling resources remain environmental
dependencies; these projects do not bundle an operating environment.

## Verification and implementation

`save` verifies a fresh QGIS process before publishing an entry. Fingerprints cover
CRS/view, layer IDs/counts, vector geometries and all attribute values, subsets,
label/style definitions, opacity, grouping/order/visibility, layouts and annotations.
Dataset and candidate CSV checksums detect later changes. `verify` repeats the
reopen and checks those hashes. Version archives plus atomic catalog writes and
a local file lock protect existing entries against failed/concurrent saves.

The [real-project verification record](../docs/PROSPECTING_LIBRARY_VERIFICATION.json)
checks both existing entries, all 307 frozen research hashes and all four original
QGIS files. Repeat with `.venv/bin/python scripts/verify_prospecting_library.py`;
add `--live denny-mountain` to also compare its currently open MCP map.

Implementation: [catalog and workflow](../src/karstfinder/library.py),
[QGIS capture/reopen checks](../src/karstfinder/library_qgis.py),
[CLI](../scripts/prospecting_library.py), and
[round-trip tests](../tests/test_library.py). No scientific analysis code changed.


## Kaleetan and Marble Peak

The approved additional areas are saved independently as `kaleetan-vicinity` and
`marble-peak`, both **Not yet investigated**. Open their `AREA_ID/AREA_ID.qgz`
projects manually or use `./library open AREA_ID`. Each has 31 persistent layers,
a full-study overview and a readable marble-detail print layout. The default
purple points represent 2 Kaleetan and 5 Marble cliff patches intersecting mapped
marble; one Marble patch is a weak contact-edge overlap. These are unvalidated
surface indicators, not entrances. Full tables also retain 808 and 1,525 indicators
across less certain surrounding geology. See
[results and evidence](../docs/APPROVED_AREAS_RESULTS_20261019.md).

Each area has its own `kaleetan_v001` or `marble_v001` configurations, prepared
inputs, outputs, original candidate checksums and unvalidated prospecting
snapshot. Source-year/quality masks and the shared data/results are required to
reopen the saved maps. These literature-informed choices are not independent
blind holdouts. Original Cave Ridge/Denny entries and archives remain intact.


## Enhanced v001 analyses

All four original entries are retained, with separately saved enhanced entries:
`cave-ridge-enhanced-v001`, `denny-mountain-enhanced-v001`,
`kaleetan-vicinity-enhanced-v001`, and `marble-peak-enhanced-v001`.
Open `prospecting_library/ID/ID.qgz` directly, or `./library open ID`.
The enhanced maps retain all 3,418 original leads and add terrain/drainage
hypotheses; they use exact continuous strength colors, separate geological
uncertainty and source-unit zones. They are unvalidated, not cave entrances.

See [enhanced workflow](../docs/enhanced_v001/WORKFLOW.md) for filters, method
views, source data requirements and private notes. Original notes remain under
their original IDs; enhanced rows retain original ID/checksum links. All entries
start Not yet investigated. The first enhanced map revision preserves the
initial review style; the next improves outline contrast on bright cliffs
without changing any evidence strength or palette anchor. Both archives remain.
