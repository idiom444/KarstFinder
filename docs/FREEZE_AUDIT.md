# Freeze integrity and bookkeeping correction

The blind v002 manifest was written before any local cave reference was acquired.
It identifies Git 243b7307fea8abccee7693ae4cec926fb09e6e0c and 163 hashed files.
The original manifest and numerical products have not been rewritten.

The first full verification attempt encountered ignored editable-package
metadata under src/karstfinder.egg-info/. The verifier initially tried to retrieve
all files under src/ from Git, but those generated metadata files are deliberately
untracked. Verification was corrected to audit .py implementation files against
the frozen Git commit and generated metadata/data against their recorded local
hashes. All 163 entries then passed. This is a validation/audit correction,
not a new model fit, changed ranking or replacement freeze.

The initial public-reference search followed the completed freeze; downloading
local validation records followed successful complete hash verification. Later
source-code changes affect evaluation and reporting, while the frozen code is
still audited against the original Git commit. A regression test checks archived
code, ignored package metadata and rejection of altered numerical artifacts.

Frozen numerical result directories remain write-protected. The active/private
QGIS project can change for review; archived blind QGIS projects and all numerical
artifacts remain covered by the freeze. No detailed validation coordinates are
stored in tracked files.

The later evaluation guard requires verified source accuracy as well as the
predeclared uncertainty threshold. This prevents an assumed small radius from
qualifying a record; it changes neither the frozen scoring nor the current
comparison (all four records already fail the threshold/verification criteria).
The 10 m evaluation-area denominator is now explicit in the aggregate JSON,
and the distinction from the native 1 m mask is documented in VALIDATION_REPORT.md.
