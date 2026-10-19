# KarstFinder

Reproducible, blind geospatial research into cave-bearing landscapes near Cave
Ridge, Snoqualmie Pass, Washington. Initial outputs describe **landscape
hypotheses, not cave locations or probabilities**. Known local cave locations
have not been consulted. Read [PROJECT_STATE.md](PROJECT_STATE.md) before work.

## Setup on Arch Linux

Use the repository open in VS Code: `/home/Idiom/Repos/MyRepos/KarstFinder`.
The original brief's `~/Projects` location was superseded by the user.

System prerequisites: QGIS with PyQGIS, GDAL with Python bindings, NumPy, SciPy,
Python, Git, and optionally Poppler for technical-report text extraction. GRASS
and SAGA runtimes are absent; the QGIS GRASS provider listing alone is not proof
that GRASS algorithms can execute. Rasterio, GeoPandas and scikit-learn are not
required for this baseline.

```bash
python -m venv --system-site-packages .venv
uv pip install --python .venv/bin/python -r requirements.lock
uv pip install --python .venv/bin/python --no-deps -e .
.venv/bin/python -m pytest -q
```

Whitebox's Python wrapper downloads the open WhiteboxTools binary on first use.
The observed binary version/hash is recorded with the run. Source system GIS
versions are recorded under `docs/`; exact replays require compatible packages
and the recorded binary. Do not pip-install another GDAL or Qt into this venv.

## Reproduce

```bash
.venv/bin/python scripts/acquire.py
.venv/bin/python scripts/acquire_supplemental.py
.venv/bin/python scripts/prepare.py
.venv/bin/python scripts/run_baseline.py
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/make_qgis_project.py
```

Downloads are cached and checksummed. Acquisition manifests contain exact URLs;
source files, processing outputs and local validation data are ignored by Git.
About 1.5 GB of disk is needed initially; allow extra space for repeat experiments.
The model refuses to overwrite an existing run. To repeat locally, use
`--output results/blind_v001_repeat`, then pass the same results path to
`make_qgis_project.py --results results/blind_v001_repeat`. That command updates
the review project to the specified run; it does not freeze an experiment.
Run acquisition scripts in the listed order: the supplemental script merges
its records into the acquisition manifest created by the primary script.

Open `qgis/KarstFinder.qgz` in QGIS. To load it through the running QGIS MCP
plugin, run `.venv/bin/python scripts/review_in_qgis.py`; it preserves another
open session before loading. Use `.venv/bin/python scripts/verify_results.py`
for artifact checks. All map layers are persistent local files;
no web basemap or Codex session is needed. The imagery and data files must remain
at their relative locations. GeoTIFFs and candidate GeoPackages are under
`results/blind_v001/`; original terrain/context data are under `data/`.

## Research records

- [RESEARCH.md](RESEARCH.md): sources, assumptions and transfer limits.
- [METHODOLOGY.md](METHODOLOGY.md): exact baseline and scoring definitions.
- [EXPERIMENTS.md](EXPERIMENTS.md): run history and empirical results.
- [docs/DATASETS.md](docs/DATASETS.md): provenance, coverage, units and uncertainty.
- [AGENTS.md](AGENTS.md): instructions that protect the blind experiment.

M1 foundation and an exploratory M2 baseline are the first-session scope. M3
requires an independent high-resolution feature detector before any final blind
freeze. Validation, supervised learning and geographic expansion come later.

![Exploratory blind landscape map](docs/experiments/blind_v001_map.png)
