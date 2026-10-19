# Nearby carbonate areas for user review — 2026-10-19

Status: **proposals only; no new area approved or analyzed for cave candidates.**
The existing Denny map/library, models, rankings and frozen records are unchanged.
Only public geological polygons, geographic names and literature were screened.
No DEM acquisition/derivation, morphology detection, candidate scoring or routes
were run. No new library entries or study configurations were created.

## User's selection criterion and information exposure

The user explicitly requested public cave-specific trip reports/documentation
before approving additional areas. They then clarified that ordinary hiking and
other recreation reports do **not** lower priority. Accordingly, hiking, climbing,
mining/quarry history and geological publications alone do not count as previous
cave exploration. Natural-karst observations in a cave survey are distinguished
from confirmed caves and from identified entrances. Ice/snow caves and artificial
mine openings are not evidence that a particular carbonate lens was cave-prospected.

This request authorizes literature-informed area selection, superseding the
earlier no-cave-literature rule for this shortlist. These areas must not later be
described as independently blind holdouts. No private validation archive was read,
no one was contacted, and no entrance-coordinate dataset was requested or created.
The Cave Ridge freeze was verified before the literature review.

"No report found" means no geographically relevant public cave-specific source
was located in the searches listed below. It does not establish that nobody has
visited, prospected, privately recorded or discovered caves there. An absence of
public reports is especially weak evidence where cave information is withheld.

## Geological basis

Source: Washington DNR's
[1:100,000 Map Unit polygons](https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer/11)
and [Description of Map Units table](https://gis.dnr.wa.gov/site1/rest/services/Public_Geology/100K_Surface_Geology_WA_GeMS/MapServer/13).
The source data are documented by the
[Washington Geological Survey](https://dnr.wa.gov/washington-geological-survey/publications-and-data/geology-gis-data-and-databases).

The selected units are explicitly described as marble:

- `PMmb(e)`: crystalline marble pods/beds in the eastern melange belt, the same
  unit as the current Denny and Cave Ridge bodies.
- `TRmb(e)`: another eastern-melange marble unit, locally associated with metachert,
  greenstone and siliceous replacement. Same broad carbonate rock type, without
  asserting identical age, chemistry or karst behavior to Denny.
- `PMmb(w)`: marble beds/pods in the western melange belt, interbedded in places
  with chert/shale. A carbonate hypothesis, not a purity measurement.
- `JTRmb(c)`: marble lenses in the Chiwaukum Schist, a different geological host
  from Denny. Associated calc-silicate/schist can interrupt the carbonate.

An initial symbol screen also returned `Qls` and `Ols(d)`; these were rejected.
`Qls` denotes landslides, and the selected DMU description for `Ols(d)` is breccia,
not limestone. Formal unit names containing "Marble Creek" or "Marblemount" also
do not by themselves identify carbonate lithology.

The final query and SHA-256 are archived in
[the geological scoping record](proposals/20261019_carbonate_scope.json). Raw
responses/description tables remain ignored under `data/raw/area_shortlist_20261019/`.
This is a selected-marble screen, not an exhaustive inventory of every carbonate
or unmapped lens within the region. Contacts/areas inherit the map's coarse scale.

Distances below are the **straight-line shortest distances to polygon edges**
from the center of the approved Denny study, EPSG:26910 (617350, 5253750).
They are neither trail lengths nor driving distances. Multipart geological
features were separated before distance/area reporting: OBJECTID 741 contains
widely separated lenses and its centroid must not be used as an area's location.
Geographic names were checked against USGS Geographic Names layers, limited to
summits, ridges, streams and lakes. Points below describe **mapped geology, not
cave entrances**. No current public-access/approach determination has been made.

## Proposed areas

| Review priority | Area and approximate geological location | Mapped rock | Footprint / distance | Cave-specific documentation result |
|---|---|---|---|---|
| First, closest | Kaleetan Peak vicinity: small mapped pod near 47.4627 N, 121.4798 W, northwest of the current Denny area | `PMmb(e)`, OBJECTID 29440 | 3.132 ha; 4.7 km | No public cave-specific report naming this lens was found. Ordinary climbing/hiking reports are not a penalty. |
| Second, farther alternative | Marble Peak / upper Marble Gulch, Silverton area, near 48.0571 N, 121.5701 W | `TRmb(e)`, OBJECTID 741, component 2 | 1.091 ha; 70.6 km | No public carbonate-cave-specific report tied to this lens was found. Small/discontinuous carbonate lenses are documented geologically. |
| Secondary; regional karst history | Money Creek / eastern Palmer–Crosby Mountain slopes: two pods near 47.7210–47.7325 N, 121.4682–121.4654 W | `TRmb(e)`, OBJECTID 741, components 1 and 0 | 1.624 + 7.216 ha; 32.7–33.8 km | Cave literature already mentions sinkholes around Palmer Mountain/Maloney Peak. It does not establish that either exact polygon was explored or contains a cave. |
| Lower | Proctor Creek, southeast of Gold Bar, near 47.8251–47.8271 N, 121.6507–121.6568 W | `PMmb(w)`, OBJECTIDs 29441–29442 | 1.370 + 1.007 ha; 46.9–47.3 km | A historical cave rumor and unsuccessful cave search are explicitly documented; this is previous cave prospecting, not confirmation of a cave. |
| Lower | Lower Rainy Creek / Little Wenatchee River, north side of Nason Ridge, near 47.8477–47.8600 N, 120.9640–120.9534 W | `JTRmb(c)`, OBJECTIDs 10378–10382 | Five pods totaling about 34.34 ha; 59.0–60.5 km | Public grotto records describe cave-related visits/prospecting in 2022 and 2023. They do not locate an entrance within one of these particular mapped polygons. |

These are **priorities for choosing the next study**, not cave-potential scores.
For each option, the scoping JSON contains a proposed **3 × 3 km study window**
enclosing the selected lens or cluster, comparable in size to Denny. These are
review proposals only, not active configurations. For the two first choices:

- Kaleetan vicinity: EPSG:26910 bounds `[613050, 5256200, 616050, 5259200]`.
- Marble Peak: EPSG:26910 bounds `[605050, 5322150, 608050, 5325150]`.

Kaleetan is the first recommendation because it is nearby, explicitly mapped as
the same marble unit as Denny, and no cave-specific report tied to that pod was
located. Its selection does not imply safe accessibility, an observed opening,
large connected carbonate volume or likely cave discovery.

The Marble Peak alternative is farther and geologically small. Danner's
[Limestones of Western Washington, Marble Peak section](https://www.dnr.wa.gov/Publications/ger_b52_limestone_res_western_wa_3.pdf)
describes short disconnected limestone lenses. This geological account supports
the rock identification but does not establish cave exploration. Similarly, the
historic **Chair Peak occurrence east of Chair Peak** describes limestone float;
it must not be equated with the separately mapped Kaleetan-vicinity polygon.

## Cave-specific evidence causing lower priority

[Halliday, Caves of Washington (1963)](https://dnr.wa.gov/sites/default/files/publications/ger_ic40_caves_of_wa.pdf)
records a Proctor Creek cave rumor and an unsuccessful search, with possible
confusion with mining. It also mentions sinkholes in the Palmer/Maloney area.
Those are sufficient flags for previous karst attention; neither statement proves
a confirmed cave within one of the selected polygons. This old source is not a
current exhaustive cave inventory.

[Cascade Grotto's May 2022 public minutes](https://cascadegrotto.org/meeting-minutes-may-2022/)
mention Rainy Creek cave in the Lake Wenatchee area. The
[October 2023 public minutes](https://cascadegrotto.org/meeting-minutes-october-2023/)
describe work at an insurgence and searching cave/sinkhole rumors at Rainy Creek.
These provide direct evidence of earlier cave prospecting in that vicinity,
without locating its extent or any entrance relative to the geological polygons.
The October page title/publication metadata and internal meeting-date text differ;
use it as a published 2023 record, not proof of an exact trip date.

Neither ordinary hikers, mineral collecting, nor quarry operations alone caused
any area to be downgraded. A search result mentioning Chair Peak **viewed from
Cave Ridge** is not a Chair/Kaleetan cave report. Marble Peak results from British
Columbia/Pakistan/California and Gold Bar cave results from Utah were excluded as
wrong locations. Snow/ice-cave mentions near Silverton were excluded as a different
phenomenon from carbonate-cave exploration.

## Public search scope and limits

Search date: 2026-10-19. Public web search covered geographically qualified name
combinations with `cave`, `caves`, `caving`, `karst`, `sinkhole`, `limestone` and
`marble`, plus targeted searches of `cascadegrotto.org`, `alpental.com/grotto` and
`caves.org`. Relevant searches included:

- `"Kaleetan" cave caves limestone`; `"Kaleetan" cave karst sinkhole site:alpental.com/grotto`
- `"Kaleetan" limestone marble cave site:caves.org OR site:cascadegrotto.org OR site:alpental.com`
- `"Chair Peak" cave exploration limestone` (nearby context only; distinguish other mountains)
- `"Marble Peak" Washington cave caves limestone`; `"Marble Peak" cave site:alpental.com/grotto`
- `"Marble Peak" cave site:cascadegrotto.org`; `"Marble Gulch" Washington cave caves`
- `"Marble Pass" cave Washington -Colorado -Utah`
- `"Money Creek" cave caves limestone marble`; `"Palmer Mountain" Washington cave caves`
- `"Money Creek" cave site:cascadegrotto.org`
- `"Proctor Creek" cave caves karst`; `"Proctor Creek" cave site:alpental.com`
- `"Gold Bar" limestone cave -site:facebook.com`
- `"Rainy Creek" Washington cave marble limestone`; `"Rainy Creek" cave site:cascadegrotto.org`

General hiking searches were initially used to identify geographic context before
the user's clarification. Their presence/number is excluded from the final novelty
priority. Results were not an exhaustive full-text search of every newsletter,
unindexed scan, alternate place name, member-only archive or unpublished record.
No silence in these searches should be represented as proof of an undiscovered
cave area. No outreach or access to restricted records is authorized.

**Next step:** user chooses an area and approves its proposed study footprint
before any terrain/cave-candidate analysis or new map/library investigation begins.
