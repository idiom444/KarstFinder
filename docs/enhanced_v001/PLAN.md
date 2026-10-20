# Enhanced prospecting v001 implementation plan

Authorized by the user's enhanced-prospecting brief on 2026-10-19. Existing
scientific files, original map entries, ranks and field notes remain unchanged.
The new work is an unvalidated methodological comparison, not blind validation.
No known-cave sources/private archives or outreach are permitted.

1. **Preserve and audit** — pin baseline commit, full current library maps,
   candidate CSVs and data hashes; preserve the baseline methodology. Verify all
   existing freezes and library entries before and after implementation.
2. **Versioned acquisition** — inspect DNR geological services at all scales,
   their source-map catalogs and USGS mapping metadata. Acquire whitelisted
   geology/structure fields only. Treat finer maps as overrides only where actual
   coverage and explicit lithology justify them; unknown geology remains unknown.
   Do not open cave-bearing publications or inventories. Native four-band NAIP
   and bounded LiDAR tile acquisition are independent optional modules.
3. **Established terrain tools** — use GDAL/WhiteboxTools on existing buffered
   DEMs for local relief/relative position, curvature, ruggedness, valley/ridge
   relationships and modeled drainage. Retain all component rasters. Robust patch
   quantiles replace dependence on one extreme residual pixel in the enhanced
   formula; the old calculation remains available as baseline evidence.
4. **Evidence registry** — retain every baseline candidate and independent
   method detections with stable area/geometry IDs, coordinates, footprints,
   source links, measurements, counter-evidence, missing-data flags and geological
   confidence. Geological zones follow source polygons and carbonate-contact
   relationships, not distance-only clustering. No max-score/min-support filter
   removes legitimate single-method leads.
5. **Ordinal scoring** — configure evidence-family weights; correlated DEM,
   drainage and same-survey point-cloud measurements do not count as independent
   confirmations. Missing is distinct from measured absence/counter-evidence.
   Geological confidence and observation/data confidence are separate fields.
6. **Exact maps and library** — continuous interpolated stops at
   0:#440154, .25:#3b528b, .5:#21918c, .75:#5ec962, 1:#fde725; type by marker shape,
   uncertainty shown separately. Default shows every retained lead. Provide
   reversible filters, component layers, a continuous legend and persistent
   independent enhanced library entries for all four current areas.
7. **Compare and deliver** — geology-only/simple-terrain/baseline comparisons,
   slope-correlation and residual-robustness audits, missing-data and synthetic
   tests, exact ramp checks, fresh QGIS reopen/visual inspection, dataset hashes,
   updated project/methodology/research records and committed implementation.

Optional acquisition is bounded; missing point clouds/imagery/geological detail
must not block the DEM workflow or eliminate a lead. Report actual coverage and
limitations rather than claiming a missing-data component works. No published
cave-prospecting threshold is transferred without a stated rationale and tests.
No field route is certified by an analytical coordinate.
