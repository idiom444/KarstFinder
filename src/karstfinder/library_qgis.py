"""QGIS persistence checks for the local prospecting library (no model runs).

Imported in a fresh offscreen process, or by the existing live MCP plugin.
Scientific layers are opened read-only; only new library projects are written.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from qgis.core import (
    Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsProviderRegistry,
    QgsMapLayerStyle, QgsReferencedRectangle, QgsReadWriteContext,
)
from qgis.PyQt.QtXml import QDomDocument


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_xml(xml):
    return ET.canonicalize(xml, strip_text=True)


def xml_sha(element):
    doc = QDomDocument()
    doc.appendChild(doc.importNode(element, True))
    return hashlib.sha256(canonical_xml(doc.toString()).encode()).hexdigest()


def local_source(layer):
    """Reject ephemeral and remote layers: reopening must work offline."""
    if layer.providerType() not in ('ogr', 'gdal'):
        raise ValueError(f'{layer.name()}: persist the {layer.providerType()} layer to a local file first')
    uri = QgsProviderRegistry.instance().decodeUri(layer.providerType(), layer.source())
    path = uri.get('path', '')
    if not path or '://' in path or path.startswith('/vsi'):
        raise ValueError(f'{layer.name()}: a persistent local data source is required')
    result = Path(path).resolve()
    # Do not open private validation data, including through a symlink.
    if 'private' in result.parts or 'validation.gpkg' in result.name.lower():
        raise ValueError(f'{layer.name()}: private reference sources cannot enter the library')
    return result


def preflight_project(path):
    """Check source URIs before QGIS can open any private reference layers."""
    with zipfile.ZipFile(path) as archive:
        xml = archive.read(next(n for n in archive.namelist() if n.endswith('.qgs')))
    root = ET.fromstring(xml)
    for layer in root.findall('.//projectlayers/maplayer'):
        source = layer.findtext('datasource', '')
        provider = layer.findtext('provider', '')
        if provider not in ('ogr', 'gdal'):
            raise ValueError(f'Unsupported persistent source: {provider}')
        uri = QgsProviderRegistry.instance().decodeUri(provider, source)
        raw = uri.get('path', '')
        resolved = (Path(path).parent / raw).resolve()
        if 'private' in resolved.parts or 'validation.gpkg' in resolved.name.lower():
            raise ValueError('Private validation layers are not permitted in library projects')
        if not raw or '://' in raw or raw.startswith('/vsi'):
            raise ValueError(f'Project source must be a local file: {raw}')
        if not resolved.is_file():
            raise FileNotFoundError(f'Missing dataset: {resolved}')


def normalized_value(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    return str(value)


def tree_state(node):
    item = {'name': node.name(), 'checked': node.itemVisibilityChecked(),
            'expanded': node.isExpanded()}
    if hasattr(node, 'layerId'):
        item['layer_id'] = node.layerId()
    else:
        item['children'] = [tree_state(child) for child in node.children()]
    return item


def state(project):
    """Semantic fingerprint: styles, tree, view, annotations, and vector values."""
    layers = {}
    for layer in project.mapLayers().values():
        path = local_source(layer)
        if not path.is_file() or not layer.isValid():
            raise FileNotFoundError(f'Missing or invalid dataset for {layer.name()}: {path}')
        style = QgsMapLayerStyle()
        style.readFromLayer(layer)
        item = {'name': layer.name(), 'provider': layer.providerType(),
                'crs': layer.crs().authid(), 'opacity': layer.opacity(),
                'style_sha256': hashlib.sha256(canonical_xml(style.xmlData()).encode()).hexdigest()}
        if isinstance(layer, QgsVectorLayer):
            if layer.isEditable():
                raise ValueError(f'{layer.name()}: save or discard layer edits before saving the library map')
            values = sorted((feature.id(), [normalized_value(v) for v in feature.attributes()],
                             bytes(feature.geometry().asWkb()).hex()) for feature in layer.getFeatures())
            item.update(feature_count=layer.featureCount(),
                        fields=[[f.name(), f.typeName()] for f in layer.fields()],
                        features_sha256=digest(values), subset=layer.subsetString(),
                        labels_enabled=layer.labelsEnabled())
        else:
            item.update(width=layer.width(), height=layer.height(), bands=layer.bandCount())
        layers[layer.id()] = item
    extent = project.viewSettings().defaultViewExtent()
    context = QgsReadWriteContext()
    context.setPathResolver(project.pathResolver())
    # Layout serialization contains relative data/image paths, so compare it at
    # a fixed project filename in capture() and the verifier.
    doc = QDomDocument()
    layouts = project.layoutManager().writeXml(doc)
    annotations = project.annotationManager().writeXml(doc, context)
    annotation_layer = doc.createElement('maplayer')
    if not project.mainAnnotationLayer().writeLayerXml(annotation_layer, doc, context):
        raise RuntimeError('Cannot serialize the project annotation layer')
    return {'crs': project.crs().authid(), 'title': project.title(),
            'view_extent': [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()],
            'view_crs': extent.crs().authid(),
            'rotation': project.viewSettings().defaultRotation(),
            'tree': tree_state(project.layerTreeRoot()), 'layers': layers,
            'custom_order': [l.id() for l in project.layerTreeRoot().customLayerOrder()],
            'has_custom_order': project.layerTreeRoot().hasCustomLayerOrder(),
            'layouts_sha256': xml_sha(layouts), 'annotations_sha256': xml_sha(annotations),
            'main_annotation_layer_sha256': xml_sha(annotation_layer),
            'layout_names': [l.name() for l in project.layoutManager().layouts()]}


def capture(project, destination, expected_path, iface=None):
    """Write a new map, restoring the live session's filename/dirty/view state."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    for layer in project.mapLayers().values():
        local_source(layer)  # safety before any feature read or project write
    old_filename, old_dirty = project.fileName(), project.isDirty()
    old_storage = project.filePathStorage()
    old_extent = project.viewSettings().defaultViewExtent()
    old_rotation = project.viewSettings().defaultRotation()
    try:
        if iface is not None:
            canvas = iface.mapCanvas()
            project.viewSettings().setDefaultViewExtent(
                QgsReferencedRectangle(canvas.extent(), canvas.mapSettings().destinationCrs()))
            project.viewSettings().setDefaultRotation(canvas.rotation())
        project.setFilePathStorage(Qgis.FilePathType.Relative)
        project.setFileName(str(destination))
        expected = state(project)
        if not project.write():
            raise RuntimeError(f'QGIS could not write {destination}')
        Path(expected_path).write_text(json.dumps(expected, indent=2, ensure_ascii=False) + '\n')
    finally:
        project.setFileName(old_filename)
        project.setFilePathStorage(old_storage)
        project.viewSettings().setDefaultViewExtent(old_extent)
        project.viewSettings().setDefaultRotation(old_rotation)
        project.setDirty(old_dirty)


def dependencies(project, repo):
    """Layer files plus GDAL sidecars and transitive VRT dependencies."""
    from osgeo import gdal
    files = {}

    def add(path, layer_name):
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f'Missing dataset: {path}')
        try:
            key = str(path.relative_to(repo))
        except ValueError:
            key = str(path)
        if key not in files:
            files[key] = {'path': key, 'bytes': path.stat().st_size,
                          'sha256': file_sha(path), 'layers': []}
        if layer_name not in files[key]['layers']:
            files[key]['layers'].append(layer_name)

    for layer in project.mapLayers().values():
        path = local_source(layer)
        add(path, layer.name())
        if layer.providerType() == 'gdal':
            dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
            if dataset is None:
                raise ValueError(f'Cannot open raster: {path}')
            for dependency in dataset.GetFileList() or []:
                add(dependency, layer.name())
        elif path.suffix.lower() == '.shp':
            for suffix in ('.shx', '.dbf', '.prj', '.cpg'):
                sidecar = path.with_suffix(suffix)
                if sidecar.exists():
                    add(sidecar, layer.name())
    return sorted(files.values(), key=lambda item: item['path'])


def check_candidate_table(project, path):
    """Prevent accidentally saving one area's map under another area's metadata."""
    from karstfinder.library import read_ranking
    expected = read_ranking(path)
    def values(row):
        return (str(row['object_id']), int(row['rank']), float(row['score']),
                row['kind'], float(row['easting']), float(row['northing']))
    target = sorted(values(row) for row in expected)
    for layer in project.mapLayers().values():
        if not isinstance(layer, QgsVectorLayer):
            continue
        fields = set(layer.fields().names())
        identifier = 'object_id' if 'object_id' in fields else 'candidate_id'
        score = 'score' if 'score' in fields else 'mean_score'
        if not {identifier, score, 'rank', 'easting', 'northing'}.issubset(fields):
            continue
        actual = sorted(values({'object_id': f[identifier], 'rank': f['rank'], 'score': f[score],
                                'kind': f['kind'] if 'kind' in fields else 'landscape',
                                'easting': f['easting'], 'northing': f['northing']}) for f in layer.getFeatures())
        if actual == target:
            return {'candidate_count': len(expected), 'matching_layer': layer.name(),
                    'ids_ranks_scores_coordinates_match_csv': True}
    raise RuntimeError('Candidate CSV does not match any complete loaded candidate layer; check the area ID/specification')


def run(action, project_path, state_path, report_path=None, repo=None, candidates=None):
    app = QgsApplication([], False)
    app.initQgis()
    preflight_project(project_path)
    project = QgsProject()
    if not project.read(str(Path(project_path).resolve())):
        raise RuntimeError(f'Cannot reopen QGIS project: {project_path}')
    if action == 'capture':
        raise ValueError('Capture requires a separate source and destination')
    actual = state(project)
    expected = json.loads(Path(state_path).read_text())
    differences = [key for key in expected if expected[key] != actual.get(key)]
    if differences:
        detail = {key: {'expected': expected[key], 'actual': actual.get(key)} for key in differences}
        Path(str(state_path) + '.mismatch.json').write_text(json.dumps(detail, indent=2))
        raise RuntimeError(f'Reopened map differs in {differences}; see {state_path}.mismatch.json')
    candidate_check = check_candidate_table(project, candidates) if candidates else None
    if report_path:
        report = {'fresh_process': True, 'qgis_version': Qgis.QGIS_VERSION,
                  'layer_count': len(actual['layers']), 'state_matches_capture': True,
                  'vector_counts': {v['name']: v['feature_count'] for v in actual['layers'].values()
                                    if 'feature_count' in v},
                  'candidate_table_check': candidate_check,
                  'dependencies': dependencies(project, Path(repo).resolve()),
                  'portability': 'local_shared_datasets; not a self-contained package'}
        Path(report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    # Let process shutdown own QGIS teardown; no exitQgis while project objects live.


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['capture', 'verify'])
    parser.add_argument('--project', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--destination')
    parser.add_argument('--report')
    parser.add_argument('--repo')
    parser.add_argument('--candidates')
    args = parser.parse_args()
    if args.action == 'capture':
        app = QgsApplication([], False)
        app.initQgis()
        preflight_project(args.project)
        project = QgsProject()
        if not project.read(str(Path(args.project).resolve())):
            raise RuntimeError(f'Cannot read {args.project}')
        capture(project, args.destination, args.state)
    else:
        run('verify', args.project, args.state, args.report, args.repo, args.candidates)


if __name__ == '__main__':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    main()
