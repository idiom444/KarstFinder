"""Versioned local prospecting catalog; independent of scientific algorithms.

index.json is the current catalog. Each revision also has an immutable JSON
record, and each map save has an independently reopen-tested QGIS archive.
Personal observations are append-only local JSON, excluded from Git.
"""
from contextlib import contextmanager
import copy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

STATUSES = ('Not yet investigated', 'Planned for a trip', 'Partially explored',
            'Explored', 'Follow-up needed', 'Archived')
SCHEMA_VERSION = 1


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    try:
        with temporary.open('w') as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_id(area_id):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', area_id):
        raise ValueError('Area ID must use lowercase letters, numbers and single hyphens')


def read_ranking(path):
    """Normalize existing surface/landscape CSV headings without rewriting them."""
    if path is None:
        return []
    path = Path(path).resolve()
    if 'private' in path.parts:
        raise ValueError('Private validation data cannot be registered')
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    surface = {'object_id', 'rank', 'score', 'kind', 'easting', 'northing'}
    landscape = {'candidate_id', 'rank', 'mean_score', 'easting', 'northing'}
    if not surface.issubset(fields) and not landscape.issubset(fields):
        raise ValueError('Candidate CSV must use KarstFinder surface-indicator or landscape headings')
    if not surface.issubset(fields):
        rows = [{**r, 'object_id': r['candidate_id'], 'score': r['mean_score'], 'kind': 'landscape'} for r in rows]
    if len({r['object_id'] for r in rows}) != len(rows):
        raise ValueError('Candidate IDs must be unique within an area')
    return rows


class Library:
    def __init__(self, repo, directory=None):
        self.repo = Path(repo).resolve()
        self.directory = Path(directory).resolve() if directory else self.repo / 'prospecting_library'
        self.index_path = self.directory / 'index.json'

    @contextmanager
    def locked(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / '.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def catalog(self):
        if not self.index_path.exists():
            return {'schema_version': SCHEMA_VERSION, 'areas': []}
        catalog = read_json(self.index_path)
        if catalog.get('schema_version') != SCHEMA_VERSION:
            raise ValueError('Unsupported catalog schema version')
        return catalog

    def entry(self, area_id):
        validate_id(area_id)
        for entry in self.catalog()['areas']:
            if entry['area_id'] == area_id:
                return entry
        raise KeyError(f'No saved area named {area_id}; use list')

    def relative(self, path):
        return os.path.relpath(Path(path).resolve(), self.repo)

    def path(self, path):
        return (self.repo / path).resolve()

    def area_dir(self, area_id):
        validate_id(area_id)
        return self.directory / area_id

    def _publish(self, entry):
        catalog = self.catalog()
        catalog['areas'] = [e for e in catalog['areas'] if e['area_id'] != entry['area_id']] + [entry]
        catalog['areas'].sort(key=lambda e: e['area_id'])
        write_json(self.index_path, catalog)

    def _revision(self, entry, change):
        number = entry.get('revision', 0) + 1
        entry['revision'] = number
        entry['updated_utc'] = now()
        entry['change'] = change
        entry['metadata_path'] = self.relative(self.area_dir(entry['area_id']) / 'versions' / f'v{number:06d}.json')
        return entry

    def _qgis(self, *args):
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['PYTHONPATH'] = str(self.repo / 'src') + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run([sys.executable, '-m', 'karstfinder.library_qgis', *map(str, args)],
                                env=env, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('QGIS verification failed:\n' + result.stdout + result.stderr)

    def _ranking(self, path):
        return read_ranking(self.path(path) if path else None)

    def _ranking_sha(self, path):
        return sha(self.path(path)) if path else None

    def save(self, area_id, *, specification=None, project=None, live=False):
        """Register or save another map revision; never write original outputs."""
        validate_id(area_id)
        if live == bool(project):
            raise ValueError('Choose exactly one of live=True or a project file')
        with self.locked():
            try:
                old = self.entry(area_id)
            except KeyError:
                old = None
            spec = specification or (old or {}).get('specification')
            if not spec:
                raise ValueError('A new area needs a specification JSON file')
            spec = copy.deepcopy(spec)
            for key in ('name', 'general_location', 'study_extent', 'geological_summary',
                        'analysis_references'):
                if key not in spec:
                    raise ValueError(f'Missing area specification field: {key}')
            bounds = spec['study_extent'].get('bounds', [])
            if len(bounds) != 4 or not (bounds[0] < bounds[2] and bounds[1] < bounds[3]) or not spec['study_extent'].get('crs'):
                raise ValueError('study_extent requires crs and [xmin, ymin, xmax, ymax] bounds')
            spec.setdefault('candidate_csv', None)
            rows = self._ranking(spec['candidate_csv'])
            ranking_sha = self._ranking_sha(spec['candidate_csv'])
            for ref in spec['analysis_references']:
                path = self.path(ref)
                if 'private' in path.parts:
                    raise ValueError('Private validation references cannot enter the catalog')
                if not path.exists():
                    raise FileNotFoundError(f'Missing analysis reference: {ref}')
            entry = copy.deepcopy(old) if old else {
                'area_id': area_id, 'created_utc': now(), 'status': STATUSES[0],
                'personal_notes': self.relative(self.area_dir(area_id) / 'local' / 'field_notes.json'),
            }
            entry = self._revision(entry, 'map saved from live QGIS' if live else 'map registered from saved project')
            revision = entry['revision']
            folder = self.area_dir(area_id)
            folder.mkdir(parents=True, exist_ok=True)
            archive = folder / f'map-v{revision:06d}.qgz'
            state = folder / 'versions' / f'v{revision:06d}.state.json'
            report = folder / 'versions' / f'v{revision:06d}.verification.json'
            state.parent.mkdir(exist_ok=True)
            if archive.exists() or state.exists() or report.exists():
                raise FileExistsError(f'Revision files already exist for {area_id} v{revision}; inspect interrupted save before retrying')
            temporary = folder / f'.capture-{uuid.uuid4().hex}.qgz'
            alias = folder / f'{area_id}.qgz'
            previous_alias = alias.read_bytes() if alias.exists() else None
            alias_replaced = False
            try:
                if live:
                    from karstfinder.qgis_bridge import request
                    code = (f'import sys\nsys.path.insert(0, {str(self.repo / "src")!r})\n'
                            'import importlib\nfrom karstfinder import library_qgis\n'
                            'importlib.reload(library_qgis)\n'
                            f'library_qgis.capture(QgsProject.instance(), {str(temporary)!r}, {str(state)!r}, iface)\n'
                            'print("Library capture complete; live session preserved")')
                    result = request('execute_code', {'code': code}, timeout=120)
                    if not result.get('executed') or not temporary.exists() or not state.exists():
                        raise RuntimeError(f'Live QGIS capture failed: {result}')
                else:
                    self._qgis('capture', '--project', self.path(project), '--destination', temporary, '--state', state)
                temporary.replace(archive)  # same parent: relative source paths are unchanged
                self._qgis('verify', '--project', archive, '--state', state,
                           '--report', report, '--repo', self.repo,
                           *(['--candidates', self.path(spec['candidate_csv'])] if spec['candidate_csv'] else []))
                if self._ranking_sha(spec['candidate_csv']) != ranking_sha:
                    raise RuntimeError('Candidate CSV changed during save; refusing to publish')
                verified = read_json(report)
                entry.update(name=spec['name'], general_location=spec['general_location'],
                             study_extent=spec['study_extent'], geological_summary=spec['geological_summary'],
                             specification=spec, candidate_count=len(rows) if spec['candidate_csv'] else None,
                             highest_priority_candidates=[{k: r[k] for k in ('object_id', 'rank', 'kind', 'score')}
                                                          for r in rows[:10]],
                             candidate_csv=spec['candidate_csv'], candidate_csv_sha256=ranking_sha,
                             analysis_references=spec['analysis_references'],
                             analysis_reference_hashes={ref: sha(self.path(ref)) for ref in spec['analysis_references']
                                                        if self.path(ref).is_file()},
                             project_path=self.relative(folder / f'{area_id}.qgz'),
                             archived_project=self.relative(archive), project_sha256=sha(archive),
                             map_revision=revision, state_path=self.relative(state),
                             verification_path=self.relative(report),
                             dataset_references=verified['dependencies'],
                             portability=verified['portability'], layer_count=verified['layer_count'])
                # Store the original map source too, without relying on it to reopen.
                if not live:
                    entry['source_project'] = self.relative(self.path(project))
                write_json(self.path(entry['metadata_path']), entry)
                alias = self.path(entry['project_path'])
                alias_temp = alias.with_suffix('.qgz.tmp')
                shutil.copyfile(archive, alias_temp)
                alias_temp.replace(alias)
                alias_replaced = True
                self._publish(entry)
                return entry
            except Exception:
                # A failed save never changes the current catalog or previous map.
                if alias_replaced:
                    if previous_alias is None:
                        alias.unlink(missing_ok=True)
                    else:
                        alias.write_bytes(previous_alias)
                for path in (temporary, archive, state, report, Path(str(state) + '.mismatch.json')):
                    path.unlink(missing_ok=True)
                self.path(entry['metadata_path']).unlink(missing_ok=True)
                raise

    def update(self, area_id, status=None):
        if status is not None and status not in STATUSES:
            raise ValueError(f'Status must be one of {STATUSES}')
        with self.locked():
            entry = copy.deepcopy(self.entry(area_id))
            if status is not None:
                entry['status'] = status
            self._revision(entry, 'fieldwork metadata updated; scientific map unchanged')
            write_json(self.path(entry['metadata_path']), entry)
            self._publish(entry)
            return entry

    def observe(self, area_id, *, text, candidate_id=None, visited=None, rock_type=None,
                geological_features=None, possible_opening=None, photos=None,
                follow_up=None, observation_id=None):
        """Append observations/revisions; never infer cave absence from a visit."""
        with self.locked():
            entry = copy.deepcopy(self.entry(area_id))
            if self._ranking_sha(entry['candidate_csv']) != entry['candidate_csv_sha256']:
                raise RuntimeError('Original candidate ranking changed; notes cannot be attached safely')
            path = self.path(entry['personal_notes'])
            notes = read_json(path) if path.exists() else {
                'schema_version': SCHEMA_VERSION, 'area_id': area_id, 'events': []}
            if notes.get('area_id') != area_id:
                raise ValueError('Notes file belongs to another area')
            previous = [e for e in notes['events'] if e['observation_id'] == observation_id]
            if observation_id and not previous:
                raise ValueError('Cannot revise an unknown observation ID')
            if previous and previous[-1].get('candidate_id') != candidate_id:
                raise ValueError('A revised observation must retain its area/candidate association')
            candidates = {r['object_id'] for r in self._ranking(entry['candidate_csv'])}
            if not previous and candidate_id is not None and candidate_id not in candidates:
                raise ValueError(f'Unknown candidate {candidate_id} in {area_id}')
            event = {'observation_id': observation_id or str(uuid.uuid4()),
                     'revision': len(previous) + 1, 'recorded_utc': now(),
                     'candidate_id': candidate_id, 'visited': visited,
                     'rock_type_observed': rock_type, 'geological_features_observed': geological_features,
                     'possible_opening_observed': possible_opening, 'photo_references': photos or [],
                     'follow_up_warranted': follow_up, 'notes': text,
                     'prediction_reference': previous[-1]['prediction_reference'] if previous else {
                         'map_revision': entry['map_revision'], 'candidate_csv': entry['candidate_csv'],
                         'candidate_csv_sha256': entry['candidate_csv_sha256']},
                     'record_type': 'personal field observation; separate from automated prediction'}
            notes['events'].append(event)
            write_json(path, notes)
            self._revision(entry, 'local field notes updated; scientific map unchanged')
            write_json(self.path(entry['metadata_path']), entry)
            self._publish(entry)
            return event

    def verify(self, area_id, full=True):
        entry = self.entry(area_id)
        missing = [r['path'] for r in entry['dataset_references'] if not self.path(r['path']).is_file()]
        if missing:
            raise FileNotFoundError('Missing datasets (restore these paths before opening):\n' + '\n'.join(missing))
        for key in ('project_path', 'archived_project'):
            path = self.path(entry[key])
            if not path.is_file() or sha(path) != entry['project_sha256']:
                raise RuntimeError(f'Saved {key} changed or missing: {path}. Save a new version or restore the archive.')
        if self._ranking_sha(entry['candidate_csv']) != entry['candidate_csv_sha256']:
            raise RuntimeError('Candidate ranking file changed')
        if full:
            for item in entry['dataset_references']:
                if sha(self.path(item['path'])) != item['sha256']:
                    raise RuntimeError(f'Dataset changed: {item["path"]}; save revised analysis as a new map version')
            for ref, expected in entry.get('analysis_reference_hashes', {}).items():
                path = self.path(ref)
                if not path.is_file() or sha(path) != expected:
                    raise RuntimeError(f'Analysis reference changed or missing: {ref}')
        self._qgis('verify', '--project', self.path(entry['project_path']),
                   '--state', self.path(entry['state_path']),
                   *(['--candidates', self.path(entry['candidate_csv'])] if entry['candidate_csv'] else []))
        return {'area_id': area_id, 'layer_count': entry['layer_count'],
                'candidate_count': entry['candidate_count'], 'fresh_process_reopened': True,
                'state_matches_capture': True, 'dataset_files': len(entry['dataset_references']),
                'dataset_hashes_checked': full, 'candidate_csv_unchanged': True,
                'portability': entry['portability']}

    def open(self, area_id):
        """Validate first; retain any dirty live session before loading another map."""
        self.verify(area_id)
        from karstfinder.qgis_bridge import request
        from karstfinder.library_qgis import preflight_project
        target = self.path(self.entry(area_id)['project_path'])
        preflight_project(target)
        backup_dir = self.directory / '.sessions'
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / f'session-{uuid.uuid4().hex}.qgz'
        # Execute safety check and replacement together in the QGIS main thread.
        code = ('import json\np = QgsProject.instance()\n'
                'editing = [l.name() for l in p.mapLayers().values() if isinstance(l, QgsVectorLayer) and l.isEditable()]\n'
                'if editing:\n    raise RuntimeError("Save or discard layer edits first: " + str(editing))\n'
                'if p.isDirty():\n'
                '    old_filename = p.fileName()\n'
                '    try:\n'
                f'        if not p.write({str(backup)!r}):\n            raise RuntimeError("Cannot preserve the dirty session")\n'
                '    finally:\n        p.setFileName(old_filename)\n        p.setDirty(True)\n'
                f'if not p.read({str(target)!r}):\n    raise RuntimeError("Cannot load library project")\n'
                'iface.mapCanvas().setDestinationCrs(p.viewSettings().defaultViewExtent().crs())\n'
                'iface.mapCanvas().setExtent(p.viewSettings().defaultViewExtent())\n'
                'iface.mapCanvas().setRotation(p.viewSettings().defaultRotation())\n'
                'iface.mapCanvas().refresh()\n'
                'invalid = [l.name() for l in p.mapLayers().values() if not l.isValid()]\n'
                'if invalid:\n    raise RuntimeError("Unavailable layers: " + str(invalid))\n'
                'print(json.dumps({"filename": p.fileName(), "layer_count": len(p.mapLayers()), '
                f'"session_backup": {str(backup)!r} if __import__("pathlib").Path({str(backup)!r}).exists() else None}}))')
        result = request('execute_code', {'code': code}, timeout=120)
        if not result.get('executed') or result.get('stderr') or not result.get('stdout', '').strip():
            raise RuntimeError(f'Cannot open saved area: {result}')
        info = json.loads(result['stdout'].strip().splitlines()[-1])
        if info['filename'] != str(target):
            raise RuntimeError(f'QGIS did not open {target}')
        return info
