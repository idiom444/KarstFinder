# Marble provider review — 2026-10-19

The final QGIS library reopen changed the byte hash of
`data/processed/marble_v001/context.gpkg` after the first new-area snapshot.
The original snapshot is retained unchanged as pre-review evidence; it is not
silently rewritten. All other 152 entries, including every score raster, candidate
geometry, full-precision ranking and original review measurement, still match.

A fresh reconstruction from the retained raw DNR files and identical GDAL/context
preparation code matches **every layer schema, attribute and exact geometry**:
17 bedrock features, 10 faults, 30 contacts, 24 orientations and one study polygon.
This establishes unchanged scientific context despite the container-byte change.
The exact changed pre-review byte fields cannot be identified because no byte
copy of that earlier container was retained. No original data was patched to
force its hash to match.

The additive final record is
`experiments/snapshots/marble_v001_reviewed.json`; its provider audit is
`docs/experiments/marble_v001_provider_review.json`. The new record also pins the
unchanged original snapshot file and audit script. Prepared context files are
now read-only as well as the already-protected numerical result directories.
The original `marble_v001.json` remains historical, rather than the current
container-integrity target. Kaleetan's initial 149-entry snapshot still verifies
without a provider amendment. Cave Ridge and Denny's older 307 entries and four
original maps remain unchanged.

The current Marble library revision references both records and the audit.
No model, rank, score, threshold, field observation or cave conclusion changed.
Use `scripts/verify_approved_snapshots.py` to check the current snapshots and all
four library entries. The first-snapshot creation helper's direct Marble verify
command intentionally still detects the preserved pre-review mismatch.
