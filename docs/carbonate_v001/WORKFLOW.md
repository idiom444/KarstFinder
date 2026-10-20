# Opening the corrected prospecting maps

Use these Library entries for current carbonate prospecting:

```bash
./library open cave-ridge-carbonate-v001
./library open denny-mountain-carbonate-v001
./library open kaleetan-vicinity-carbonate-v001
./library open marble-peak-carbonate-v001
```

Alternatively open `prospecting_library/AREA-carbonate-v001/AREA-carbonate-v001.qgz`
in QGIS. The project needs the local shared `data/` and `results/` directories.
Library reopening validates dependencies and preserves a dirty live session.

The default view focuses on the largest documented marble body, with **every
eligible surface site visible**. There are no scale filters, top-N limits or
hidden score cutoffs. The saved **Study overview** layout covers the full approved
window; **Marble detail** layouts cover every mapped marble body. Cave Ridge has
two bodies; the other three areas have one each.

* **S01, S02… markers** are ranked local surface-site reference points. Triangles
  have cliff support, diamonds depression support. They are not entrance predictions.
* The exact purple → blue → teal → green → yellow ramp shows absolute 0–1
  prospecting priority. Yellow is strongest in this assumed ordinal model, not
  evidence that a cave exists. No per-area color stretching occurs.
* **Magenta outlines** show explicitly documented marble. **Dashed gray** marks
  the assumed 25 m contact-review margin. Boundary-only sites have a dark outline
  and cannot exceed priority 0.35. Mixed/unknown units farther away are ineligible.
* **Gray support outlines** show the actual grouped observation footprints. Long
  footprints describe a local exposure system, not a single opening or passage.

Use **Identify Features** on the site for its evidence, alternative explanations,
contradictions, terrain strength, geological support, data availability, waypoint
member, priority member and IDs. The layer's attribute table provides the same
fields. QGIS relations connect a site to the **membership** table, then to the
observation records; formation records also list their sites.

Expand **Eligible supporting observations • optional inspection** and enable
**Individual observations** and/or **Individual observation footprints** to inspect
every retained scoped feature. The seven unattached Cave Ridge drainage observations
are present here but do not create destinations. `source_v001_ids` links to the
untouched old `results/enhanced_v001_AREA/registry.gpkg`, table `lead_footprints`.
The original broad observations remain available in the original enhanced Library
entry; they are not candidate layers in the corrected map.

To review measurements outside QGIS, use
`results/carbonate_v001_AREA/{candidates,observations}.json` or CSV and
`membership.json`. [review_records.json](review_records.json) also stores the complete
new ranking, coordinates, measurements, lineage IDs and membership in Git.
See [methodology](METHODOLOGY.md), [results](RESULTS.md) and
[verification](verification.json) before interpreting a score.

Save later cartographic edits with `./library save AREA-carbonate-v001`; save
personal field observations with `./library note`, which keeps evidence in ignored
local files. Do not edit frozen numerical results or publish private field evidence.
These maps provide neither a route nor access clearance.

## Reproduction and preservation

The initial commands were:

```bash
.venv/bin/python scripts/run_carbonate.py all
.venv/bin/python scripts/make_carbonate_map.py all
.venv/bin/python scripts/carbonate_library.py all
.venv/bin/python scripts/verify_carbonate.py
.venv/bin/python -m pytest -q
```

Analysis/map builders refuse existing output paths. To revise the science, copy
the configuration to a new named version and use new directories; do not erase
existing outputs to rerun v001. The first unfrozen development runs are retained
locally in `_development_` directories. `scripts/carbonate_freeze.py --verify`
checks the final versioned snapshot. All eight previous Library entries are
preserved and independently compared with the captured original catalog.
