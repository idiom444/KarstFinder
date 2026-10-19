# Preserved Denny methodology review

This is a review of existing unvalidated predictions, not a new model run or
cave-location search. No original candidate rank, measurement or geometry was
changed. Computational coordinates describe model objects, not known entrances.

- `landscape_candidates.csv`: exact original one-area landscape CSV.
- `ranked_indicators.csv`: exact original 489-object ranking and evidence fields.
- `screened_indicators.csv`: exact 489-object ranking plus separate access and
  mapped-marble intersection measurements; no access-based reordering.
- Config JSONs: byte-identical executable parameters.
- `score_audit.csv`: existing IDs/ranks and recomputed weighted contributions.
- `top10_evidence.md`: rounded display of the unchanged top-ten cliff evidence.
- `audit_summary.json`: explicit fields checked against saved object pixels.
- `methodology_at_review.md`: methodology text at this review; later changes to
  the working methodology do not change this preserved explanation.
- `review_manifest.json`: original-source and bundle-file SHA-256 hashes.

Original polygons/representative points remain in the write-protected
`results/denny_v001_features/features.gpkg`; original GeoTIFFs retain the pixel
measurements. The existing 144-file snapshot is not overwritten. Refer to
`experiments/snapshots/denny_v001.json` for final geometry/raster/config hashes
and committed implementation. Initial provider metadata differences are explained
in `docs/experiments/denny_v001_provider_audit.json`.

From the repository root, verify without rerunning the models or reading cave
references:

```bash
.venv/bin/python scripts/audit_denny_methodology.py --verify
```

To independently repeat the pixel audit into a new review directory, run the
same script with a new `--output` path. Existing review directories are refused.
The audit verifies model-raster arithmetic and rank consistency; it does not
validate that any object is a cave or that a cliff is safely reachable.
