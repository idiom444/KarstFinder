# Validation of frozen blind v002

Status: **exploratory public-reference comparison complete; entrance-localization
validation remains unresolved.** No prediction was modified after references
were accessed. Freeze implementation: 243b7307fea8abccee7693ae4cec926fb09e6e0c.

## Reference quality

The independent [Halliday 1963 survey](https://www.dnr.wa.gov/publications/ger_ic40_caves_of_wa.pdf),
printed pp.22–23, confirms cave-bearing terrain in a historical land-survey section.
The section was georeferenced using DNR's public PLSS polygons. The 2.587 km²
reference region is one spatial observation, not a set of independent entrance
coordinates. Underground drawings have local scales but do not establish surface
GNSS locations. General overlap with this region cannot count as entrance discovery.

A full-study public OpenStreetMap extract, clipped to the projected study
boundary, contains four named cave-entrance nodes. All four are associated with one contributor. Node tags and examined
changeset metadata state no survey source or positional accuracy. The official
GNIS query returned no cave records in this study envelope. A 100 m radius is
used only as an exploratory uncertainty **scenario**, not a measured error or
confidence interval. There are zero records meeting the predeclared ≤25 m
accuracy criterion. Detailed coordinates, names, source extracts, diagrams and
per-record results remain local under ignored data/private/validation/.

## Equal-area comparison

The comparison uses 1.6684 km² of positive geological support on the 10 m
scoring grid. The native 1 m geological/contact mask covers 1.630497 km²;
maximum aggregation marks an entire 10 m cell when any source pixel has
support, slightly enlarging the comparison footprint. At a 10% selected-area
budget (0.1668 km² after cell rounding), the
predeclared fixed-tie-order comparison gives:

| Model | Public map points selected | Mean area of assumed 100 m regions covered |
|---|---:|---:|
| Geology only | 1/4 | 44.8% |
| Terrain only | 0/4 | 0.4% |
| Original landscape v001 | 1/4 | 28.1% |
| Native surface morphology | 4/4 | 17.6% |
| Combined v002 | 3/4 | 19.0% |

Point selection and uncertainty-region coverage answer different questions.
None of the four uncertainty regions is fully selected at this budget. Thus
map-point coincidences do not establish robust coverage of the possible true
entrance locations. All area budgets, whole-study and comparable-geology results,
actual support caps and descriptive gains are in docs/validation_summary.json.

The spatial ranking suggests the native surface features are worth investigating.
It does not establish an entrance detector or calibrated cave probability.
Four unverified, spatially associated points are too weak a reference sample for
a claim of independently established predictive skill.

## Baseline and spatial audit

A supplemental evaluation audit, added after the primary comparison, addresses
tie variability and spatial dependence without changing any model or primary
metric. Averaging geological-score ties gives expected geology-only central
coverage 34.4% at the 10% budget, versus 25% in the single predeclared tie ordering.
The baseline comparison is therefore not summarized solely by one lucky or
unlucky tie realization.

A rigid-translation null preserves the entire four-point configuration and
requires every translated point to retain its original geological evidence class.
There are 303 valid placements on the 10 m grid. At 10% comparable area, mean
coverage across these placements is 33.3% for geology, 2.2% for terrain, 28.8% for
v001 landscape, 19.0% for morphology and 23.2% for v002 combined. The observed
central-map coverage is higher for morphology and combined. These are descriptive
controls, not inferential p-values: the original observation process, mapped
locations and geological reference itself have unresolved biases/uncertainties.
Details are in docs/validation_audit.json.

Historical regional overlap is present for all methods, including geology alone.
The combined method and geology have the same positive support fraction of the
historical section (28.5%). This cannot distinguish added predictive value.

![Aggregate exploratory comparison; no coordinates](validation/coverage.png)

## Decisions for M5 and M6

Retain the frozen experiment as the initial test. A supervised model is **not
justified with the current records**: no independently verified training labels,
accuracy-qualified validation entrances or independent geographic test regions
are available. Fitting to these four points would confound public-map provenance,
spatial association and training/test reuse. Do not call a refitted Cave Ridge
model blind.

Expansion as a demonstrated method is not yet justified. The user has stated
that no local reference dataset is available and permanently prohibits contacting
anyone. The earlier unsent request was withdrawn. No outreach, membership
purchase or field activity has occurred.

The software, freeze, public-source comparison and local QGIS review are complete.
Credible entrance-localization claims need independently verified observations
that are not currently available. Further fitting to the existing four points
cannot resolve that reference-quality limitation. M5 and M6 remain conditional;
no outreach is authorized or planned.

Public map data attribution: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
ODbL 1.0. Historical regional evidence: Washington DNR/Halliday (1963).
