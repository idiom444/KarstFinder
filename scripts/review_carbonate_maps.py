#!/usr/bin/env python3
"""Render regional/default/detail reviews and optionally reopen each live Library map."""
import argparse
import json
import os
import sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from qgis.core import QgsApplication, QgsProject, QgsRectangle, QgsMapSettings, QgsMapRendererParallelJob
from qgis.PyQt.QtCore import QSize
from karstfinder.carbonate.common import config, safe_path, write_json
from karstfinder.library import Library
from karstfinder.qgis_bridge import request


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--live', action='store_true'); args = parser.parse_args()
    app = QgsApplication([], False); app.initQgis()
    report = {'areas': {}, 'purpose': 'Saved maps reviewed at regional, default formation and close scales; no scientific filters or thresholds changed.'}
    for aid, area in config()['areas'].items():
        p = QgsProject()
        entry = Library(ROOT).entry(area['library_id'])
        assert p.read(str(safe_path(entry['project_path'])))
        sites = p.mapLayersByName('Prospecting sites • ALL eligible destinations')[0]
        obs = p.mapLayersByName('Individual observations • carbonate scope only')[0]
        first = min(sites.getFeatures(), key=lambda f: f['rank'])
        xy = first.geometry().asPoint()
        focused = QgsRectangle(xy.x()-100, xy.y()-100, xy.x()+100, xy.y()+100)
        views = [('regional', QgsRectangle(*area['study_bounds'])),
                 ('formation', p.viewSettings().defaultViewExtent()), ('close', focused)]
        renders = []
        for name, extent in views:
            settings = QgsMapSettings(); settings.setDestinationCrs(p.crs()); settings.setExtent(extent)
            settings.setOutputSize(QSize(1200, 800))
            layers = [n.layer() for n in p.layerTreeRoot().findLayers() if n.isVisible()]
            if name == 'close':
                layers.insert(0, obs)  # explicit inspection of all eligible detailed observations
            settings.setLayers(layers)
            job = QgsMapRendererParallelJob(settings); job.start(); job.waitForFinished()
            path = ROOT / f'docs/carbonate_v001/{aid}_review_{name}.png'
            assert job.renderedImage().save(str(path))
            renders.append({'view': name, 'scale': settings.scale(), 'preview': str(path.relative_to(ROOT)),
                            'site_features': sites.featureCount(), 'individual_observations_loaded': obs.featureCount(),
                            'individual_observations_visible': name == 'close', 'all_sites_unfiltered': not sites.subsetString() and not sites.hasScaleBasedVisibility()})
        report['areas'][aid] = {'renders': renders}
        p.clear()
        if args.live:
            report['areas'][aid]['live_open'] = Library(ROOT).open(area['library_id'])
            # Library.open handles dirty-session preservation and refuses layer edits.
            code = ('import json\np=QgsProject.instance()\n'
                    "sites=p.mapLayersByName('Prospecting sites • ALL eligible destinations')[0]\n"
                    "obs=p.mapLayersByName('Individual observations • carbonate scope only')[0]\n"
                    "assert not sites.subsetString() and not sites.hasScaleBasedVisibility()\n"
                    "assert all(l.isValid() for l in p.mapLayers().values())\n"
                    'print(json.dumps({"sites":sites.featureCount(),"observations":obs.featureCount(),"dirty":p.isDirty(),"crs":p.crs().authid(),"extent":iface.mapCanvas().extent().toString()}))')
            result = request('execute_code', {'code': code}, timeout=60)
            assert result.get('executed') and not result.get('stderr'), result
            report['areas'][aid]['live_state'] = json.loads(result['stdout'].strip().splitlines()[-1])
        write_json(ROOT / 'docs/carbonate_v001/map_review.json', report)
        print(aid, 'rendered regional, formation and close; live:', args.live, flush=True)


if __name__ == '__main__':
    main()
