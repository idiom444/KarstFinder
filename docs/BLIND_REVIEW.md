# Blind review before validation — v002

No named local caves, entrance coordinates, cave maps, cave inventories or
entrance photographs have been consulted. Reviews use only the acquired numeric
DEM and independently derived layers. Current object rankings and model weights
were selected without local cave labels.

## Native data and tool verification

All 59,040,000 native 1 m cells in the buffered DEM are valid. There are no
internal NoData holes requiring interpolation. Native survey identity is now
resolved at 1 m rather than inferred from 10 m availability. Primary feature
objects are rejected if any cell is within 25 m of the survey seam. This removes
0.402154 km² of the study, leaving 29.597846 km² eligible. A deterministic
10 m-stride sample of 24,142 native overlap points has median 2021−2019 difference
−0.27356 m, p95 absolute 1.11217 m and p99 absolute 2.29878 m. This is not a
ridge-specific accuracy certification. The larger differences from independently
averaged 10 m products include partial coverage and resampling effects.

A flat-bottom synthetic basin exposed a failure of Whitebox 2.4.0's default
DepthInSink/FillDepressions implementations: the expected 2 m depth was returned
as zero. Wang–Liu and Planchon–Darboux implementations both recovered 2 m.
Wang–Liu with flat fixing disabled is used for measured depression depth;
flat fixing is enabled only for the separate drainage-context DEM. The rejected
default depth/drainage products are retained in ignored data/processed/rejected_v002
and excluded from the experiment. Tests retain the known-basin and open-notch
checks. Terrain derivatives and depression filling use established GIS tools.

## Surface objects and interpretation

The initial primary thresholds produce 76 depression cores and 520 cliff patches.
A depression core is a connected region at least 0.5 m below its modeled spill
level, 4–2,500 m² in area. A cliff patch is a connected ≥45° surface, 25–10,000 m².
Objects are four-connected and must have complete quality support, some mapped
carbonate/contact-buffer support, and no intersection with mapped open water.
Features crossing the study boundary are flagged. Very large depressions/cliffs
are retained in raster evidence but omitted from the primary object inventory.

Closed depressions can be glacial hollows, forest classification pits, talus
voids, excavation or DEM artifacts. Cliff patches are exposed-slope opportunities,
not openings. Overhead DEMs cannot resolve overhangs or many vertical entrances.
Native review maps show real relief in the numeric DEM, but cannot distinguish
these origins or establish cave connectivity. No candidate is promoted or
removed based on an imagined cave entrance in a hillshade.

## Ranking and sensitivity

The method-specific and overall rankings retain component values. Geological
support is the mean evidence index across the object, with its supported
fraction recorded. A representative point is selected within the geologically
supported part by highest geological/landscape prior; it is not an opening
coordinate. Cliff and depression rankings are kept separately because their
morphology scores are not calibrated to a shared cave probability.

The 0.3/0.5/1/2 m depth sensitivities yield 102/76/47/23 quality-filtered objects
within unbuffered mapped marble or mixed melange. With 250 m contact uncertainty,
the 0.3 m count rises to 103; other primary counts remain unchanged. This count
stability does not establish positional geological accuracy or stable rankings.
The 100 m primary buffer is explicitly an assumption, not a confidence interval.

The highest combined ranks are chiefly cliffs. That is a consequence of the
stated geological/terrain/morphology weights, not observed success. Thresholds
and weights must not be changed after cave validation begins. Top-ten-per-method
review layers keep the depression approach visible despite this imbalance.

Seeded k-means clusters describe six terrain classes using slope and three DEV
scales. Classes are not given cave labels and do not contribute an unvalidated
"ML probability" to ranking. D8 contributing area is modeled contextual drainage,
not observed streams or an independent record of sinking water.

## Before/after boundary

Validation protocol is configs/validation_v001.json. It predeclares equal-area
comparisons, uncertainty coverage, 5/10/25 m localization tolerances, and a 25 m
maximum source uncertainty for entrance-localization evaluation. Coarser
historical locations can evaluate regional coverage only. No confidence in
individual entrance prediction may be inferred from broad ridge overlap.

The implementation and all output/input hashes must be committed and frozen
before the first local cave source is acquired. A source change or model revision
after validation is a new experiment and loses the original independent test.
