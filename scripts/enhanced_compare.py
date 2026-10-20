#!/usr/bin/env python3
"""Descriptive comparisons on identical objects and the complete union registry."""
import json,sys
from pathlib import Path
from collections import Counter
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from karstfinder.enhanced.common import config,safe_path,write_json,sha


def main():
    reports={};table=[]
    for area_id,area in config()['areas'].items():
        out=safe_path(area['result_dir']);rows=json.loads((out/'candidate_evidence.json').read_text());legacy=[r for r in rows if r['baseline_object_id']]
        def top(records,key):return [r['object_id'] for r in sorted(records,key=lambda r:(-(r[key] if r[key] is not None else -1),r['object_id']))[:20]]
        rankings={name:top(legacy,key) for name,key in [('original_baseline','baseline_score'),('enhanced_on_original_objects','score'),('geology_only_on_original_objects','geology_component'),('simple_slope_on_original_objects','mean_slope_deg')]}
        compare=json.loads((out/'comparison.json').read_text())
        compare['matched_object_top20']=rankings
        compare['top20_overlap_with_original']={name:len(set(ids)&set(rankings['original_baseline'])) for name,ids in rankings.items()}
        compare['new_mapped_carbonate_leads']=sum(not r['baseline_object_id'] and r['geo_class']=='mapped_carbonate' for r in rows)
        compare['ground_return_covered_leads']=sum(r['has_pointcloud'] for r in rows)
        compare['observed_geology_and_terrain_families']=sum(r['geology_component'] is not None and (r['terrain_component'] is not None or r['hydrology_component'] is not None) for r in rows)
        compare['positive_geology_and_terrain_support']=sum((r['geology_component'] or 0)>0 and max(r['terrain_component'] or 0,r['hydrology_component'] or 0)>0 for r in rows)
        compare['robust_cliff_diagnostic']={name:{stat:float(function([r[name] for r in legacy if r['kind']=='cliff' and r[name] is not None])) for stat,function in [('median',np.median),('min',np.min)]} for name in ['baseline_min_residual_m','robust_residual_q10_m']}
        # Actual multithreshold drainage sensitivity, no cave labels or selection.
        from osgeo import gdal
        from karstfinder.gis import array
        compare['modeled_stream_threshold_cell_counts']={str(t):int(np.count_nonzero(array(safe_path(area['processed_dir'])/f'terrain/modeled_streams_{t}m2.tif')==1)) for t in config()['terrain']['stream_sensitivity_areas_m2']}
        compare['registry_sha256']=sha(out/'candidate_evidence.json')
        compare['confidence_note']='More leads and more context are measured improvements in coverage/inspectability. Sources share DEM ancestry. No independent evidence of improved cave detection, precision or recall. Top-20 ties are broken by stable ID; ties carry no scientific ordering.'
        reports[area_id]=compare
        table.append(f"| {area['name']} | {len(legacy):,} | {len(rows):,} | {len(rows)-len(legacy):,} | {compare['new_mapped_carbonate_leads']} | {sum(r['score']<.25 for r in rows):,} |")
    write_json(ROOT/'docs/enhanced_v001/comparison.json',reports)
    text='''# Enhanced v001 comparison

These are unvalidated prospecting outputs, not entrance predictions. Original object coordinates, geometry, ranks and measurements remain available. The expanded coverage removes the baseline carbonate-proximity gate and maximum-component cap; it does not demonstrate new caves.

| Area | Preserved original leads | Enhanced union | Added | Added overlapping mapped carbonate | Strength <0.25 retained |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(table)+'\n\n'
    for aid,r in reports.items():
        text+=f"## {config()['areas'][aid]['name']}\n\nIdentical-object Spearman score/slope correlation: baseline **{r['spearman_on_identical_baseline_objects']['baseline_score_vs_slope']:.3f}**, enhanced **{r['spearman_on_identical_baseline_objects']['enhanced_score_vs_slope']:.3f}**. This describes dependence, not predictive performance. {r['positive_geology_and_terrain_support']:,} leads have positive geology and terrain-family support; {r['ground_return_covered_leads']} have partial ground-return coverage.\n\n"
    text+='''## What improved and what remains unresolved

The registry retains weak/single-method leads, exposes missing lithology rather than masking it, replaces the single minimum residual with footprint q10 summaries at three scales, and attaches drainage, structure and native imagery context. Geology-only and simple-slope rankings are evaluated on the same original objects; full rankings and overlap counts are in [comparison.json](comparison.json). There is no accuracy claim. Much of the larger lead count lies in unknown or noncarbonate surroundings and requires geological review, so count alone is not evidence of better prospecting.

Terrain and hydrology are correlated observations from the same DEM. Maximum-within-family scoring limits arithmetic double counting; it cannot make these observations independent. Positive geological and terrain-family support is not two confirmations of a cave. Some cliff scores plateau because robust relief reaches the exploratory 2 m scale; tied rankings have no scientific order. Residual q10 is less sensitive to one extreme pixel, but can still respond to large glacial cliffs, talus or interpolation.

Source-scale coverage did not improve: usable finer mapping was absent in the queried services, and USGS regional products do not supply entrance-scale certainty. No cave locations, inventories, private references or field observations were used. No cave-specific literature was read for this upgrade. Earlier literature-informed area selection and prior exposure remain documented; these experiments are not independent blind validation.
'''
    (ROOT/'docs/enhanced_v001/COMPARISON.md').write_text(text)


if __name__=='__main__':main()
