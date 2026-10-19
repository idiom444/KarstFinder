# Approved Kaleetan and Marble Peak investigations

On 2026-10-19 the user approved **both** proposed 3 × 3 km study windows in
`docs/proposals/20261019_carbonate_scope.json`, asking for persistent maps like
Cave Ridge and Denny. This supersedes the shortlist's historical approval-pending
status. No further geographic expansion is implied.

| Experiment | Library ID | EPSG:26910 bounds [west, south, east, north] | Target rock |
|---|---|---|---|
| kaleetan_v001 | kaleetan-vicinity | 613050, 5256200, 616050, 5259200 | PMmb(e), OBJECTID 29440 |
| marble_v001 | marble-peak | 605050, 5322150, 608050, 5325150 | TRmb(e), OBJECTID 741, local component |

Both use an additional 1,100 m numerical-processing buffer. The existing 10 m
landscape and 1 m working-grid surface-indicator methods are transferred without
changing their thresholds, scales, weights or ranking rules. The regional adapter
recognizes the actual marble map-unit code; it does not fit a new model.

These are **literature-informed, unvalidated prospecting investigations**, not
independently blind holdouts. The preceding approved public cave-specific
literature screen informed area selection. It found no geographically matched
cave report for these small lenses within the documented search scope; that does
not demonstrate that nobody has visited or explored them. No cave inventories,
entrance coordinates, private validation archive or known-entrance overlays are
used as model inputs. No person or organization is contacted.

## Execution and evidence

- `scripts/acquire_approved_areas.py`: whitelisted DNR geology, USGS terrain
  catalogs/rasters and USFS trail/ownership context; per-area source manifests.
- `scripts/acquire_marble_pslc.py` and `prepare_marble_pslc.py`: public PSLC
  Tulalip 2013 bare-earth mosaic download, archive verification and GDAL unit/CRS
  conversion. Original data and supplier metadata remain local and unchanged.
- `scripts/prepare_approved_area.py`: valid-pixel coverage check, oldest-to-newest
  mosaic, 25 m survey-seam exclusion, source-year masks and clipped geology.
- `scripts/derive_features.py`: unchanged GDAL slope/hillshade and WhiteboxTools
  depression filling, D8 context and 11 m residual calculations.
- `scripts/run_approved_area.py`: calls unchanged numerical implementations in
  `run_baseline.py` and `run_features.py`; `karstfinder.prospecting.geology_codes`
  parameterizes lithology names while retaining category precedence. Explanatory
  text and exposure flags explicitly identify the new areas and prior literature.
- `scripts/screen_approved_area.py`: descriptive mapped ownership, straight-line
  trail proximity and local slope flags, without changing scientific ranks.
- `scripts/make_approved_area_project.py`: independent relative-path QGIS maps,
  full-area overview and marble-detail print layouts; no entrance-reference layers.
- `scripts/audit_approved_area.py`: saved-pixel score reconstruction, geometry and
  point checks, unchanged access-table attributes and repeat-run comparisons.

The commands take `kaleetan` or `marble`. Each area has separately named configs,
`data/processed/AREA_v001/`, `results/AREA_v001_{landscape,features,access}/`,
`docs/experiments/AREA_v001_*.json` and an additive methodology review under
`docs/reviews/AREA_v001_methodology/`. Reruns use new paths; `--repeat` is available
for the two model stages. Existing Cave Ridge and Denny frozen records, numerical
outputs, original configurations and all four archived QGIS projects are retained.

### Coverage review at Marble Peak

Initial standard USGS 1 m tiles covered only 41.25% of the processing buffer and
34.58% of the approved study, and **none of the 10,922 rasterized marble cells**.
A Glacier Peak 2014 OPR native crop was entirely nodata. Those inputs were rejected
for model execution; no missing cells were filled and the approved window was not
shrunk. `docs/experiments/marble_v001_coverage_screening.json` preserves that finding.
The incomplete preparation is retained locally as
`data/processed/marble_v001_rejected_partial_01/` after a usable source is prepared.

PSLC documents Tulalip 2013 terrain at 3 US survey foot spacing in NAD83(HARN)
Washington North (EPSG:2926), with NAVD88/Geoid03 heights in US survey feet. GDAL
converts the horizontal grid to NAD83 UTM10N and nearest-neighbour 1 m spacing;
valid height values are multiplied by **1200/3937** to obtain metres. No fitted
vertical offset or vertical-datum shift is applied. Newer valid USGS 2016/2021
pixels take precedence. The provenance and overlap checks report actual coverage;
nominal project years do not assert an exact acquisition date for every pixel.

## Map interpretation

Purple outlines show approximate mapped marble contacts at 1:100,000. Purple dots
represent ranked surface patches that intersect those polygons; they are not
entrance positions. Orange polygons retain their actual surface footprint. The
hidden full indicator layer also includes less certain mixed-melange/contact
support. Labels retain the original rank within kind (C for cliff, D for depression)
and do not imply probabilities. The hidden raster components preserve the
landscape/feature evidence separately. Print layouts include the entire approved
study and a readable close view of its small marble lens.

Glacial terrain, talus, landslides, vegetation, snow and overhead occlusion remain
alternative explanations or limitations. A low score or absent depression core
is not evidence of cave absence. No safe/legal route or current field destination
is certified by a map; public trail/ownership context is descriptive only. No
field visit, cave opening or field observation is invented.
