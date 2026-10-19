"""Real QGIS round trips with tiny synthetic data, never the private archive."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from karstfinder.library import Library, STATUSES, read_json, read_ranking, sha


@pytest.fixture
def example(tmp_path):
    data = tmp_path / 'data'
    data.mkdir()
    features = [{'type': 'Feature', 'properties': {'object_id': f'C-{i}', 'rank': i, 'score': 1 / i,
                                                 'kind': 'cliff', 'easting': 617000 + i, 'northing': 5254000 + i},
                 'geometry': {'type': 'Point', 'coordinates': [617000 + i, 5254000 + i]}}
                for i in (1, 2)]
    (data / 'candidates.geojson').write_text(json.dumps({
        'type': 'FeatureCollection', 'crs': {'type': 'name', 'properties': {'name': 'EPSG:26910'}},
        'features': features}))
    (data / 'ranking.csv').write_text('object_id,rank,score,kind,easting,northing\n'
                                    'C-1,1,1.0,cliff,617001,5254001\nC-2,2,0.5,cliff,617002,5254002\n')
    # Create real styled vector/raster layers in a separate process. This also
    # avoids sharing QApplication state with unrelated GIS tests.
    code = '''
import sys
from pathlib import Path
from qgis.core import *
from qgis.PyQt.QtGui import QColor
from osgeo import gdal, osr
import numpy as np
root=Path(sys.argv[1]); app=QgsApplication([],False);app.initQgis()
ds=gdal.GetDriverByName('GTiff').Create(str(root/'data/terrain.tif'),3,3,1,gdal.GDT_Byte)
ds.SetGeoTransform((617000,1,0,5254003,0,-1));s=osr.SpatialReference();s.ImportFromEPSG(26910)
ds.SetProjection(s.ExportToWkt());ds.GetRasterBand(1).WriteArray(np.arange(9,dtype='uint8').reshape(3,3));ds=None
p=QgsProject();p.setFileName(str(root/'original.qgz'));p.setCrs(QgsCoordinateReferenceSystem('EPSG:26910'))
p.setFilePathStorage(Qgis.FilePathType.Relative);p.setTitle('Synthetic prospecting test')
group=p.layerTreeRoot().addGroup('Predictions');group.setExpanded(False)
v=QgsVectorLayer(str(root/'data/candidates.geojson'),'Candidate measurements','ogr');v.setReadOnly(True)
v.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name':'triangle','color':'#123456','size':'4'}))
labels=QgsPalLayerSettings();labels.fieldName='object_id';v.setLabeling(QgsVectorLayerSimpleLabeling(labels));v.setLabelsEnabled(True)
p.addMapLayer(v,False);group.addLayer(v)
r=QgsRasterLayer(str(root/'data/terrain.tif'),'Terrain','gdal');r.setOpacity(.43)
p.addMapLayer(r);p.layerTreeRoot().findLayer(r.id()).setItemVisibilityChecked(False)
p.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(QgsRectangle(616995,5253995,617010,5254010),p.crs()))
p.viewSettings().setDefaultRotation(12)
assert p.write()
'''
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'
    subprocess.run([sys.executable, '-c', code, str(tmp_path)], env=env,
                   capture_output=True, text=True, check=True)
    spec = {'name': 'Example', 'general_location': 'Synthetic test area',
            'study_extent': {'crs': 'EPSG:26910', 'bounds': [616995, 5253995, 617010, 5254010]},
            'geological_summary': 'Synthetic hypotheses only', 'candidate_csv': 'data/ranking.csv',
            'analysis_references': ['data/ranking.csv']}
    return Library(tmp_path), spec


def test_save_reopen_styles_extent_candidates_and_relative_paths(example):
    lib, spec = example
    original = sha(lib.repo / 'original.qgz')
    entry = lib.save('example', specification=spec, project='original.qgz')
    assert entry['candidate_count'] == 2
    assert entry['highest_priority_candidates'][0]['object_id'] == 'C-1'
    assert entry['status'] == STATUSES[0]
    assert entry == read_json(lib.path(entry['metadata_path']))
    state = read_json(lib.path(entry['state_path']))
    assert state['view_extent'] == [616995, 5253995, 617010, 5254010]
    assert state['rotation'] == 12
    assert state['tree']['children'][1]['expanded'] is False
    assert state['tree']['children'][0]['checked'] is False
    vector = next(l for l in state['layers'].values() if 'feature_count' in l)
    assert vector['feature_count'] == 2 and vector['labels_enabled']
    assert lib.verify('example')['fresh_process_reopened']
    assert sha(lib.repo / 'original.qgz') == original
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(lib.path(entry['project_path'])) as archive:
        root = ET.fromstring(archive.read(next(n for n in archive.namelist() if n.endswith('.qgs'))))
    sources = [n.text for n in root.findall('.//projectlayers/maplayer/datasource')]
    assert all(source.startswith('../../data/') for source in sources)


def test_versions_notes_status_and_independent_areas(example):
    lib, spec = example
    first = lib.save('one', specification=spec, project='original.qgz')
    second = lib.save('two', specification={**spec, 'name': 'Second area'}, project='original.qgz')
    old_map = lib.path(first['archived_project']).read_bytes()
    ranking_sha = sha(lib.repo / 'data/ranking.csv')
    event = lib.observe('one', text='Test visit did not establish cave absence', candidate_id='C-1',
                        visited=True, rock_type='Test rock', possible_opening=False,
                        follow_up=True, photos=['photo-reference.jpg'])
    revised = lib.observe('one', text='Revised note', candidate_id='C-1', observation_id=event['observation_id'])
    assert revised['revision'] == 2
    assert revised['prediction_reference'] == event['prediction_reference']
    notes = read_json(lib.path(first['personal_notes']))
    assert len(notes['events']) == 2 and notes['events'][0]['notes'].startswith('Test visit')
    for status in STATUSES:
        updated = lib.update('one', status)
        assert updated['status'] == status
    resaved = lib.save('one', project='original.qgz')
    assert resaved['map_revision'] > first['map_revision']
    assert lib.path(first['archived_project']).read_bytes() == old_map
    assert lib.entry('two') == second
    assert not lib.path(second['personal_notes']).exists()
    assert sha(lib.repo / 'data/ranking.csv') == ranking_sha
    assert lib.verify('one')['candidate_csv_unchanged']
    before = lib.index_path.read_bytes()
    with pytest.raises(ValueError, match='Unknown candidate'):
        lib.observe('one', text='Invalid association', candidate_id='C-999')
    with pytest.raises(ValueError, match='Status'):
        lib.update('one', 'Cave found')
    assert lib.index_path.read_bytes() == before


def test_missing_dataset_and_failed_save_preserve_catalog(example):
    lib, spec = example
    entry = lib.save('example', specification=spec, project='original.qgz')
    catalog = lib.index_path.read_bytes()
    saved = lib.path(entry['project_path']).read_bytes()
    (lib.repo / 'data/terrain.tif').rename(lib.repo / 'data/missing.tif')
    with pytest.raises(FileNotFoundError, match=r'Missing datasets.*'):
        lib.verify('example')
    with pytest.raises(RuntimeError, match='Missing dataset'):
        lib.save('example', project='original.qgz')
    assert lib.index_path.read_bytes() == catalog
    assert lib.path(entry['project_path']).read_bytes() == saved
    assert not (lib.area_dir('example') / 'map-v000002.qgz').exists()


def test_changed_data_and_ranking_are_detected(example):
    lib, spec = example
    lib.save('example', specification=spec, project='original.qgz')
    path = lib.repo / 'data/candidates.geojson'
    data = read_json(path)
    data['features'][0]['properties']['score'] = .01
    path.write_text(json.dumps(data))
    with pytest.raises(RuntimeError, match='Dataset changed: data/candidates.geojson'):
        lib.verify('example')
    (lib.repo / 'data/ranking.csv').write_text('changed ranking')
    with pytest.raises(RuntimeError, match='ranking changed'):
        lib.observe('example', text='Do not attach to changed predictions')


def test_publish_failure_rolls_back_alias_and_keeps_old_revision(example, monkeypatch):
    lib, spec = example
    first = lib.save('example', specification=spec, project='original.qgz')
    before = lib.path(first['project_path']).read_bytes()
    def fail(entry):
        raise OSError('Simulated disk failure')
    monkeypatch.setattr(lib, '_publish', fail)
    with pytest.raises(OSError, match='Simulated'):
        lib.save('example', project='original.qgz')
    assert lib.entry('example') == first
    assert lib.path(first['project_path']).read_bytes() == before
    assert not (lib.area_dir('example') / 'versions/v000002.json').exists()


def test_wrong_area_candidate_metadata_rejected_and_no_csv_supported(example):
    lib, spec = example
    csv = lib.repo / 'data/ranking.csv'
    csv.write_text(csv.read_text().replace('617001', '618001'))
    with pytest.raises(RuntimeError, match='Candidate CSV does not match'):
        lib.save('wrong', specification=spec, project='original.qgz')
    assert not lib.catalog()['areas']
    entry = lib.save('unranked', specification={**spec, 'candidate_csv': None}, project='original.qgz')
    assert entry['candidate_count'] is None
    assert not entry['highest_priority_candidates']
    lib.observe('unranked', text='Area-level note only')
    assert lib.verify('unranked')['fresh_process_reopened']


def test_landscape_headings_and_empty_rankings_are_supported(tmp_path):
    path = tmp_path / 'landscape.csv'
    path.write_text('candidate_id,rank,mean_score,easting,northing\nKF-001,1,0.8,617001,5254001\n')
    assert read_ranking(path)[0]['object_id'] == 'KF-001'
    assert read_ranking(path)[0]['kind'] == 'landscape'
    path.write_text('object_id,rank,score,kind,easting,northing\n')
    assert read_ranking(path) == []


def test_private_paths_and_invalid_ids_rejected_before_loading(example):
    lib, spec = example
    for name in ('../escape', 'With Spaces', '', 'a--b'):
        with pytest.raises(ValueError, match='Area ID'):
            lib.save(name, specification=spec, project='original.qgz')
    bad = copy.deepcopy(spec)
    bad['candidate_csv'] = 'data/private/validation.csv'
    with pytest.raises(ValueError, match='Private validation'):
        lib.save('private', specification=bad, project='original.qgz')


def test_moving_complete_tree_keeps_relative_projects_reopenable(example, tmp_path):
    import shutil
    lib, spec = example
    entry = lib.save('example', specification=spec, project='original.qgz')
    moved = tmp_path.parent / (tmp_path.name + '-relocated')
    shutil.copytree(lib.repo, moved)
    relocated = Library(moved)
    assert relocated.verify('example')['state_matches_capture']
    assert relocated.entry('example')['project_sha256'] == entry['project_sha256']
