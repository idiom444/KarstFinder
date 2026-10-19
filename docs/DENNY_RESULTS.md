# Southern Denny Mountain — unvalidated prospecting results

User-approved follow-up, completed 2026-10-19. The 3 × 3 km study is centered on
the nearest separate explicitly mapped marble body found in the regional DNR
screen. This is a prospecting application of the existing methods; it is not
evidence that they reliably detect caves. The area overlaps the old study edge.
The Cave Ridge freeze and its original predictions remain unchanged. No one was
contacted. No Denny entrance records or cave reports were acquired for modeling.
An incidental, unopened caving-newsletter search snippet is recorded in DENNY_PLAN.md.

## Findings

- 9 km² study plus 1,100 m computational buffer. Native 1 m elevation coverage is
  complete. The 25 m survey-seam exclusion removes 0.07284 km².
- DNR 1:100,000 marble polygon 29438 covers about 0.06643 km² (6.64 ha); its
  10 m center-cell raster footprint is 0.0667 km². Finer DNR 24K and 25–99K
  map-unit services return zero coverage in the queried processing envelope.
- The landscape threshold selects one area covering the entire rasterized marble
  lens. It does not narrow the search within the lens or establish cave presence.
- The native methods retain 477 cliff patches and 12 depression cores in all
  eligible geological/contact/melange context: 489 surface objects total.
- **48 cliff patches overlap mapped marble. No retained depression overlaps it.**
  Other indicators are in uncertain contact-buffer or mixed-rock context.
- The 48 marble-cliff representative points lie 382–560 m in a straight line
  from the mapped Denny Creek trail. All have steep nearby terrain. This analysis
  produces **no verified hiking-ready route to a target** and recommends no
  direct off-trail cliff approach. All representative points fall in USFS mapped
  ownership; that layer does not settle legal boundaries, access or routes.
- Native reviews show relief and steep exposures, without a recognizable opening
  or diagnostic proof of karst. Glacial erosion, talus, noncarbonate rock and
  geological contact uncertainty remain plausible explanations.

## Hiking-oriented observation options

Three teal OBS triangles lie on the official USFS Denny Creek trail geometry.
GDAL bare-earth viewsheds were evaluated at 34 trail samples spaced every 100 m,
within 1 km of the target marble. Three stations at least 200 m apart were chosen
by modeled visibility of the target marble terrain. The model uses a 10 m DEM,
1.7 m observer height, ground targets, a 1.5 km range and curvature coefficient
0.85714. It considers only Denny marble polygon 29438.

**Trees, snow, weather and actual trail-tread alignment are not modeled.** These
are possible places to look toward the geological target while staying on the
existing trail, not verified viewpoints, entrances or approach routes. Modeled
visible fractions in the data describe bare-earth terrain only. They do not
measure visible rock faces or chances of seeing a cave.

| Station | Latitude, longitude (WGS84) | Straight-line gap to mapped marble |
|---|---|---:|
| OBS-01 | 47.422617, -121.449697 | 520 m |
| OBS-02 | 47.424860, -121.454264 | 651 m |
| OBS-03 | 47.415926, -121.442758 | 911 m |

Coordinates preserve the source trail geometry; displayed digits do not imply
GPS or survey accuracy. Follow the existing trail rather than walking a straight
line between waypoints or toward the magenta cliff points. Record whether rock
is actually visible, apparent lithology and any useful photographs from lawful
trail positions. Inability to see a feature is not evidence that a cave is absent.
No opening or mine entry, excavation or disturbance is proposed.

A waypoint-only GPX is saved at
[trail_observation_waypoints.gpx](../results/denny_v001_observation/trail_observation_waypoints.gpx).
The [CSV](../results/denny_v001_observation/trail_observation_points.csv) includes
coordinates and the model limitations. The GPX contains no route or cave locations.

## Access checked on 2026-10-19

The [USFS Denny Creek Trailhead page](https://www.fs.usda.gov/r06/mbs/recreation/denny-creek-trailhead)
listed the site open. It lists day-use parking payment or accepted federal
recreation passes, and states that the Washington Discover Pass is not accepted.
The [trail page](https://www.fs.usda.gov/r06/mbs/recreation/trails/denny-creek-trail-1014)
says parking is at Franklin Falls Trailhead and describes the walk to the Denny
Creek trailhead. It lists a free self-issued Alpine Lakes Wilderness permit
requirement for May 15–October 31 and requires leashed dogs; stock, bicycles and
motorized use are prohibited on the trail.

The [forest alert index](https://www.fs.usda.gov/r06/mbs/alerts) was checked,
including the North Bend road-damage notice; no Denny-specific closure was
established from those retrieved pages. This is a dated web review, not a
guarantee of current access, snow conditions or safe travel. Check posted signs
and the land-manager pages again before a trip.

Nearby Alpental has [seasonal uphill restrictions](https://www.summitatsnoqualmie.com/uphill-travel-guide).
No resort-permit boundary clearance or route through ski terrain is inferred
from ownership data. The observations supplied here are on the mapped Denny
Creek trail; no ski-area approach is proposed.

Dated source HTML snapshots and hashes are local, with provenance in
experiments/denny_v001_access_sources.json. USFS trail and basic ownership
geometry is likewise retained with exact acquisition requests.

## Working map and verification

Open [KarstFinder_Denny_v001.qgz](../qgis/KarstFinder_Denny_v001.qgz) or the active
[KarstFinder.qgz](../qgis/KarstFinder.qgz). Known-entrance X marks, red uncertainty
circles and historical validation boundaries are absent. Detailed Cave Ridge
validation remains in its ignored local archive.

Purple outline = target mapped marble; orange = overlapping cliff patches;
magenta C# = scientific cliff rank; green = ordinal combined evidence; teal lines
= USFS trails; teal OBS triangles = possible trail observation stations; gray
polygons = non-FS mapped land. Other model components, quality layers and
bare-earth viewsheds are stored but initially hidden. Inspect the all-indicators
attributes for geological evidence and separate access flags.

All 28 layers reopen in a fresh QGIS process with expected feature counts and
persistent sources. Prediction/context GeoPackages are opened read-only with
the GDAL IMMUTABLE option, resolving transient SQLite reopen errors encountered
with mutable provider connections during project generation. The final build
log is clean, and the live map and three native-scale review images were
visually inspected. Before finalization, mutable provider access changed file
bytes in the feature/access GeoPackages relative to their initial run manifests.
Every SQLite table row matches an independent rerun after excluding expected
creation timestamps, including feature attributes and geometry. Original run
manifests retain their initial hashes; the final snapshot records post-review
hashes. See experiments/denny_v001_provider_audit.json.

An independent rerun matches all 18 landscape and 13 feature raster arrays and
both ranking CSVs exactly. All 489 feature geometries/support checks pass, all
three OBS points lie on the source trail geometry, and all 163 original Cave Ridge
freeze entries verify. Fifteen unit/analytical tests pass.

![Denny Mountain prospecting overview](experiments/denny_v001_map.png)

Final artifact snapshot: [denny_v001.json](../experiments/snapshots/denny_v001.json),
144 verified file hashes, implementation dfaf523. Final numerical
result directories are write-protected. The active QGIS project remains an
editable review copy and is excluded from the immutable artifact snapshot.
