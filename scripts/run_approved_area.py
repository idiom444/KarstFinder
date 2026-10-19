#!/usr/bin/env python3
"""Reuse the established numerical models with explicit regional source adapters."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys
from osgeo import ogr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from karstfinder.gis import sha
from karstfinder.prospecting import geology_codes


def load(name):
    spec = importlib.util.spec_from_file_location('approved_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('area', choices=['kaleetan', 'marble'])
    parser.add_argument('kind', choices=['landscape', 'features'])
    parser.add_argument('--repeat', action='store_true')
    args = parser.parse_args()
    area = args.area + '_v001'
    cfgpath = ROOT / f'configs/{area}_{args.kind}.json'
    cfg = json.loads(cfgpath.read_text())
    output = ROOT / f'results/{area}_{args.kind}{"_repeat" if args.repeat else ""}'
    module = load('run_baseline' if args.kind == 'landscape' else 'run_features')
    if args.kind == 'features':
        module.geology = lambda ref, context: geology_codes(ref, context, cfg['marble_units'], cfg['mixed_units'])
    else:
        # The legacy numerical routine labels all carbonate as PMmb(e). Correct
        # only its explanatory text to the region's actual source unit(s).
        original = module.candidate_areas
        def candidates(*values):
            rows, cells = original(*values)
            text = 'Mapped marble ' + ', '.join(cfg['marble_units']) + '; DNR 1:100,000'
            for row in rows:
                row['geo_evidence'] = text
            dest = ogr.Open(str(output / 'candidates.gpkg'), 1)
            layer = dest.GetLayerByName('candidate_areas')
            for feature in layer:
                feature['geo_evidence'] = text; layer.SetFeature(feature)
            dest = None
            with (output / 'candidates.csv').open(newline='') as stream:
                fields = csv.DictReader(stream).fieldnames
            with (output / 'candidates.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
            return rows, cells
        module.candidate_areas = candidates
    sys.argv = [sys.argv[0], '--config', str(cfgpath.relative_to(ROOT)), '--output', str(output.relative_to(ROOT))]
    module.main()
    summary_path = output / 'summary.json'
    summary = json.loads(summary_path.read_text())
    summary.update(known_cave_sources_accessed=True, public_cave_literature_consulted_for_area_selection=True,
                   independently_blind=False, known_entrance_locations_used_as_model_inputs=False,
                   area_name=cfg['area_name'], marble_units=cfg['marble_units'])
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    manifest_path = output / 'run_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.update(adapter='scripts/run_approved_area.py + karstfinder.prospecting.geology_codes',
                    numerical_thresholds_and_weights_transferred_unchanged=True,
                    independent_blind_validation=False)
    key = 'output_hashes' if args.kind == 'landscape' else 'outputs'
    manifest[key] = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != 'run_manifest.json'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    if not args.repeat:
        (ROOT / f'docs/experiments/{area}_{args.kind}_summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    ogr.UseExceptions()
    main()
