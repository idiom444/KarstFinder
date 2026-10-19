# KarstFinder session instructions

Work only in this repository. The user corrected the original ~/Projects path:
this VS Code workspace is the canonical project. Do not modify Atlas or other repos.

## Frozen blind experiment and validation (critical)

Initial blind v002 was frozen before any local cave source was acquired.
Freeze: experiments/frozen/blind_v002.json; implementation commit
243b7307fea8abccee7693ae4cec926fb09e6e0c. Verify it with
karstfinder.freeze.verify_freeze before reading local cave validation records.
Detailed references/evaluation may now be acquired for Cave Ridge validation,
only from reliable legally accessible sources, and kept under data/private/.
Never publish sensitive locations or put detailed reference data in Git.

Do not modify frozen outputs, original configurations, inputs or the archived
QGIS projects. Implement new experiments under new names/directories, retaining
the old frozen comparison. Once validation sources are read, new Cave Ridge
models are no longer independently blind; do not claim otherwise. Only an
appropriately separate holdout or new geographic area can support new validation.

For any future blinded area, do not search/read named caves, cave inventories,
entrance maps/coordinates/photographs or exploration reports until predictions
are finalized, committed, hashed and frozen. Use only geology, numerical terrain
and unlabeled imagery. Historical Washington publications can mix geology and
cave locations. A keyword filter is not proof that a source is blind-safe.
If new information contaminates an intended blind experiment, record it.

The user permanently prohibits contacting anyone. Never send messages, email,
contact requests, or approach data custodians on the user's behalf. Do not ask
again for outreach authorization. Use public sources and local analysis only.
No excavation, entry into
unstable openings, or restricted-access suggestions. Fieldwork requires current
land-manager rules and suitable non-invasive survey arrangements.

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

## Approved Denny Mountain follow-up

On 2026-10-19 the user approved a 3 × 3 km southern Denny Mountain study near
47.4265 N, 121.4444 W. Apply the existing methods as unvalidated prospecting,
without obtaining cave records. This explicitly authorizes this geographic
follow-up despite the earlier validation prerequisite for a demonstrated method.
It does not establish model skill. The area overlaps the old study edge and is
not an independent blind holdout. Use configs/denny_v001_*.json and separate
data/processed/denny_v001 and results/denny_v001_* paths.
Remove entrance-reference layers from the active prospecting map. Retain private
validation archives locally, but never load them into the Denny project. Do not
contact anyone. Field-observation leads require public access/terrain screening;
straight-line trail distances are not routes or proof of safe/legal access.

Denny results are finalized under experiments/snapshots/denny_v001.json, an
unvalidated prospecting snapshot (not the blind Cave Ridge freeze). Its final
numerical result directories are write-protected. Future revisions require new
names/paths; the active qgis/KarstFinder.qgz is an editable review copy.

## Current methodology review / information restriction

The user explicitly prohibits looking up known cave locations or compromising
the ongoing investigation. Do not acquire or read cave reference data, including
the local private validation archive, for Denny work or methodology review.
Use existing geology, terrain, unlabeled imagery and numerical results only.
METHODOLOGY.md documents the implemented assumptions and Denny priority evidence.
Preserve the original ranks/measurements and snapshot; the additive review record
is docs/reviews/denny_v001_methodology/. No score/threshold retuning is authorized
by the documentation request. Prior information exposure must not be erased or
misrepresented as a new independent blind holdout.
