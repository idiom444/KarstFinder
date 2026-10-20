# Carbonate prospecting v001 — corrected scientific scope

Analysis revision: `carbonate_v001`; ranking revision: `carbonate_priority_v001`.
This supersedes enhanced v001 as the recommended prospecting map, without changing
that experiment. Scores are ordinal hypotheses, never cave probabilities.

## Eligibility is decided before terrain detection

The target is limestone or marble capable of dissolution. The four approved
windows contain **explicitly mapped marble**, not a newly established limestone
formation. The reviewed allowlist is `PMmb(e)` and `TRmb(e)` in
[configuration](../../configs/carbonate_v001.json). A place name or the mere mention
of marble within a broad mixed unit does not qualify a formation.

Washington DNR's 1:100,000 geology polygons are already stored in each preserved
`results/enhanced_v001_AREA/geology.gpkg`, table `geology`. Their `source_id` is the
original DNR polygon OBJECTID. Unit evidence comes from the previously acquired
`data/raw/area_shortlist_20261019/selected_unit_descriptions.json`, reproduced as
[geological evidence](GEOLOGY_EVIDENCE.json) with the same hash. The official
[DNR unit-description service](https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer/13)
provides the `DMU_FEATURE_QUAD_UNIT`, `DMU_100K_MAP_UNIT`, name and description
fields. Only geological metadata was checked for this correction; no new geographic
data, cave records, exploration reports or private validation material was acquired.

| Area | DNR polygon | Unit | Documentary basis |
|---|---|---|---|
| Cave Ridge | 29438, 29439 | PMmb(e) | Crystalline marble beds/pods with local noncarbonate interbeds |
| Denny Mountain | 29438, clipped to its approved window | PMmb(e) | Same mapped marble unit; overlapping studies are not independent |
| Kaleetan vicinity | 29440 | PMmb(e) | Explicit mapped marble lens |
| Marble Peak | 741, local polygon component | TRmb(e) | Crystalline marble interlayered locally with chert/greenstone |

The cached descriptions establish carbonate lithology, **not purity, continuous
exposure, dissolution rate, cave development, an entrance or safe access**.
`JTRmt(e)` mélange, other mixed/metamorphic units, unknown rock and surficial units
are excluded: no separately localized carbonate exposure has been established
there. A future such record requires a new reviewed eligibility revision.

[scope.py](../../src/karstfinder/carbonate/scope.py) requires an exact reviewed unit
code and matching description key, splits multipart formations into components,
and preserves source IDs and geometry hashes. It does not promote units through
word matching. Each run's `summary.json` lists every admitted and excluded polygon.

## Contact uncertainty

Mapped contacts are approximate. A **25 m** margin around only an admitted marble
body allows explicit contact-review observations. It is smaller than the former
100 m context margin and remains local to a documented exposure. It is an analyst
assumption, **not a measured positional accuracy or confidence interval**. At
1:100,000, even 50 m is only 0.5 mm on the source map; this does not establish that
any chosen buffer contains the true contact. Water is removed and scope is clipped
to the approved study. A narrow mapped lens can therefore have a substantial
margin-to-core area ratio, especially at Marble Peak; these areas are reported.

Persistent native eligibility masks encode 0 excluded, 1 mapped marble, 2 contact
margin. Exact vector clipping follows raster masking. Each observation records its
actual marble overlap fraction and whether it is mapped, mixed core/margin or
boundary-only. Boundary-only support is capped at 0.35 and explicitly flagged.
The 0/25/50 m sensitivity tables report native eligible pixels and surface component
counts with identical detector thresholds. They measure scope sensitivity, not
accuracy, and do not select a buffer by a preferred result count.

## Existing measurements and detection

[pipeline.py](../../src/karstfinder/carbonate/pipeline.py) reads existing persistent
rasters, masks **before connected-component detection**, then clips each footprint
exactly. No broad landscape-wide candidate layer is merely hidden by the map.

* Bare-earth LiDAR DEM derivatives: existing USGS 2019/2021 elevation, with existing
  PSLC Tulalip 2013 coverage at Marble where needed; source epoch and seam-quality
  rasters remain attached. See the original acquisition manifests and
  [previous source record](../enhanced_v001/GEOLOGY_SOURCES.md).
* Native 1 m slope and depression depth from `baseline_features` in the configuration.
  Cliffs require slope ≥45° and ≥25 m²; depressions depth ≥0.5 m and ≥4 m². Quality
  must equal 1 throughout sampled native support. Existing 25 m seam exclusions
  remain enforced. Single-method surface observations survive these requirements.
* Existing 11/31/61 m terrain residuals and 10 m contributing area / height above
  modeled drainage (HAND) from `source_enhanced_processed/terrain` and
  `baseline_feature_prepared`. Existing established GDAL/Whitebox terrain and
  hydrology products are reused; no new hand-coded derivative is introduced.
* Drainage context requires HAND ≤5 m, catchment ≥25,000 m², ≥100 m² and valid native
  quality. These are ordinary modeled channels, **not measured sinks or springs**.
  They cannot seed a destination, bridge surface sites or increase site priority.
  Unattached drainage is retained as context in the observations table/layer.
* Existing 2023 native 0.6 m RGB/NIR, NDVI and exposed-surface/vegetation masks, and
  existing partial native point-cloud summaries at Marble are supporting context.
  Missing coverage remains NULL. Neither NDVI nor cloud curvature confirms an opening.
* Original mapped structural-intersection detector results were reviewed: there
  are zero structural-intersection observations in all four enhanced registries.
  No structural-only destination is discarded or invented in this correction.

Four-neighbor components use the existing SciPy/GDAL implementation. Local
footprint statistics are recomputed from source pixels, not copied from a larger
out-of-scope cliff. Measurements include min/max, mean/median, q10/q90 and valid
pixel counts. A clipped observation can have a new coordinate and ID; its original
source footprints, coordinates, scores and IDs remain unchanged in enhanced v001.
`source_v001_ids` links same-kind footprints with actual positive-area intersection;
these are lineage links rather than claims of independent evidence. Some newly
scoped components have no old ID because eligibility and QA splitting now precede
minimum-area filtering. Their raster, formation and geometry hashes identify them.

## Separate ranking model

[priority.py](../../src/karstfinder/carbonate/priority.py) implements the new,
auditable ranking; enhanced v001's scoring implementation is byte-preserved.

For a cliff, terrain anomaly strength is
`0.2 + 0.8 × clip(max(0, -q10_11, -q10_31, -q10_61) / 2 m, 0, 1)`.
For a depression it is `clip(max_depth / 3 m, 0, 1)`.
The cliff floor retains otherwise ordinary single-method steep patches in marble,
but gives them weak terrain support. Negative elevation residual is local relief,
not a wall recess or observable cave opening; glacial troughs can also saturate
this index. Saturation at 1 does not imply certainty or a trained prediction.

For an **eligible** observation with mapped-marble area fraction `f`, geological
support factor `g = 0.35 + 0.65f` and provisional support `p = g × terrain_strength`.
An ineligible location has **no candidate**, rather than a high terrain-only score.
Hydrology retains its old nominal 0.4 support for context comparison only. A site's
priority is the maximum **cliff/depression** member support. Counts, drainage,
imagery and repeated DEM methods add no confirmation bonus. Site terrain and
geological factor fields belong to the identified `priority_member_id`; their
product reconstructs the site score. The site-wide overlap fraction is separately
reported and need not equal that member's fraction.

`data_confidence = 0.4 + 0.3 + 0.2 × imagery_available + 0.1 × cloud_available`
is an explicitly assumed **data availability index**, not an error estimate or
confidence in a cave. The first two terms represent valid native terrain and
documented geological coverage. `geological_confidence` is an ordinal map-context
flag (0.5 for a core-related member, 0.25 boundary-only), not calibrated certainty.
Full measurements, boundary status, alternatives and contradictions remain primary.

The exact continuous linear sRGB ramp is reused without quantiles or per-area
rescaling: **0 #440154; .25 #3b528b; .5 #21918c; .75 #5ec962; 1 #fde725**.
Color expresses this new combined priority, while separate terrain, geological
and data-availability fields remain inspectable.

## Local sites and coordinates

[grouping.py](../../src/karstfinder/carbonate/grouping.py) joins surface footprints
only within the same mapped formation component when they overlap/touch or have
a ≤10 m gap whose GIS shortest connector stays inside eligible geology. The
0.001 m geometric tolerance is numerical only. The 10 m local-exposure gap is a
declared grouping assumption, not a cave-passage length or fitted parameter.
Transitive connections can create a long cliff exposure system; the complete
footprint and every connecting edge are preserved rather than implying one opening.
Drainage can support several surface sites but cannot connect them to each other.

Stable site IDs derive from the formation and surface-member IDs; stable observation
IDs derive from formation, detector and normalized geometry. Priority ties use IDs.
The representative point is the strongest surface member with core overlap where
available, placed on that actual overlap using OGR PointOnSurface. Otherwise it is
on the explicitly flagged boundary footprint. It is not an averaged coordinate,
an entrance, a proven route or necessarily the highest-scoring member if that
member lies entirely in the uncertain margin.

## Review, preservation and limits

New files live under `results/carbonate_v001_AREA`,
`data/processed/carbonate_v001/AREA`, `qgis/*_carbonate_v001.qgz` and separate
Library IDs `AREA-carbonate-v001`. All old registries, measurements, maps,
Library entries, frozen implementations and snapshots are preserved.
The local unfrozen development runs are retained under `_development_` paths and
are excluded from the final snapshot. No previous score is relabeled as this model.

Each result contains GeoPackage point/footprint layers, formation/margin geometry,
membership table, CSV/JSON records, sensitivity, configuration and hashed input,
code, prepared-raster and output manifests. See [results](RESULTS.md) and
[verification](verification.json). The independent audit reconstructs native
statistics, geometry scope, lineage links, priority, waypoint membership, ramp and
fresh project/Library reopening, then checks all previous freeze hashes again.

These areas are **unvalidated and not independently blind**: previous Cave Ridge
reference exposure and the earlier authorized literature-informed shortlist are
already recorded. This correction did not read private validation records or look
up cave locations. Absence of cave literature is not evidence of an unexplored area.
Glaciation, talus, landslides, forest, snow, LiDAR occlusion, interbeds and approximate
contacts remain alternative explanations or limits. There are no confirmed caves
and no certified access routes. These results do not recommend a field route;
current land-manager rules and non-invasive access screening are still required
before any field suggestion.
