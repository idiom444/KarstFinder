# KarstFinder session instructions

Work only in this repository. The user corrected the original ~/Projects path:
this VS Code workspace is the canonical project. Do not modify Atlas or other repos.

## Blind experiment (critical)

**Current stage: exploratory blind; initial predictions are NOT frozen.**
Do not search for or read named Cave Ridge caves, entrances, cave inventories,
exploration reports, entrance photographs, cave-location maps or cave GIS layers.
Do not use labeled topo basemaps that might disclose cave names/locations.
A GNIS query for the ridge itself is permitted; restrict to exact name and class.
Avoid historical Washington cave publications entirely during this stage.
Only use geology unit polygons, structural lines/measurements, unlabeled imagery,
and numeric elevations. Restrict service attribute fields; do not display arbitrary
notes or regional map annotations. A text keyword filter is only a precaution,
not proof that an arbitrary source is blind-safe. Log possible contamination and
stop the experiment if any entrance evidence is exposed.

Before any independent validation: finish complementary feature detection,
review and finalize rankings/configuration, commit all code, ensure a clean tree,
record Git commit plus SHA-256 of every input/output/configuration, and create a
separate immutable freeze manifest. Merely committing the exploratory baseline
is NOT a freeze. Never tune a frozen experiment against known entrances.
Keep permitted detailed validation data under ignored data/private/ locally.
Do not publish sensitive locations. No messages/contact requests without authorization.

## Implementation

Use .venv created with system site packages: packaged PyQGIS/GDAL/NumPy/SciPy
must remain ABI compatible. Never install into system Python. Dependency/setup
instructions are in README.md; installed package evidence is in docs/.
Use GDAL, OGR, WhiteboxTools, or available established GIS implementations.
Do not implement hydrology, TPI or terrain derivatives from scratch.
Processing scripts are local; QGIS MCP is for inspecting and loading the result.
The installed MCP plugin transport listens on 127.0.0.1:9876, using 4-byte
big-endian length-prefixed JSON. See src/karstfinder/qgis_bridge.py. It is not
an exposed MCP tool in this session. Preserve a live project's unsaved state
before replacing it. Do not overwrite unrelated projects.

Baseline commands: scripts/acquire.py, scripts/acquire_supplemental.py,
scripts/prepare.py, scripts/run_baseline.py, scripts/make_qgis_project.py.
Use a NEW output path for reruns; baseline script refuses overwrites.
Do not change hypotheses silently. Version revised configurations separately.
Keep large files ignored under data/ and results/, with provenance/hashes tracked.
Maintain README, PROJECT_STATE, RESEARCH, METHODOLOGY, EXPERIMENTS.
Run .venv/bin/python -m pytest -q for analytical changes. Reopen and inspect QGIS
projects after changes. Outputs must be persistent GeoTIFF / GeoPackage.

## Scientific interpretation

Landscape scores are ordinal hypothesis indices, never fitted cave probabilities.
Map polygons and their representative points are landscape areas, not predicted
entrances. Separate cave formation, surface indicators, entrance detection and
cave confirmation. Retain model components. Treat glacial terrain, talus, rockfall,
landslides, forests, snow and overhang occlusion as limitations. No excavation,
unstable-opening entry or restricted-access recommendations. Before any field
suggestion, verify current land-manager rules.
