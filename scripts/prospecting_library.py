#!/usr/bin/env python3
"""Save, inspect and reopen local prospecting maps without rerunning analysis."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from karstfinder.library import Library, STATUSES, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list', help='List saved areas and their project paths')
    save = commands.add_parser('save', help='Save live QGIS, or register an existing .qgz')
    save.add_argument('area_id')
    save.add_argument('--spec', type=Path, help='Area metadata JSON (required for a new area)')
    save.add_argument('--project', type=Path, help='Existing local .qgz; omit to capture live MCP state')
    for name in ('open', 'verify', 'show'):
        command = commands.add_parser(name)
        command.add_argument('area_id')
    update = commands.add_parser('update', help='Change fieldwork status, retaining history')
    update.add_argument('area_id')
    update.add_argument('--status', choices=STATUSES, required=True)
    note = commands.add_parser('note', help='Append a private local observation; no model changes')
    note.add_argument('area_id')
    note.add_argument('--candidate', help='object_id from this area; omit for an area-level note')
    note.add_argument('--text', required=True)
    note.add_argument('--visited', choices=['yes', 'no', 'unknown'])
    note.add_argument('--rock-type')
    note.add_argument('--features')
    note.add_argument('--possible-opening', choices=['yes', 'no', 'unknown'])
    note.add_argument('--photo', action='append', default=[], help='File path or external photo reference; repeatable')
    note.add_argument('--follow-up', choices=['yes', 'no', 'unknown'])
    note.add_argument('--revise', help='Observation ID to append a new revision; prior record retained')
    notes = commands.add_parser('notes', help='Show private local observation history')
    notes.add_argument('area_id')
    notes.add_argument('--candidate')
    candidate = commands.add_parser('candidate', help='Inspect unchanged prediction measurements')
    candidate.add_argument('area_id')
    candidate.add_argument('candidate_id')
    args = parser.parse_args()
    library = Library(ROOT)
    boolean = lambda v: {'yes': True, 'no': False, 'unknown': None, None: None}[v]
    try:
        if args.command == 'list':
            for entry in library.catalog()['areas']:
                print(f"{entry['area_id']}: {entry['name']} | {entry['status']} | {entry['candidate_count']} indicators")
                print('  ' + str(library.path(entry['project_path'])))
            return
        if args.command == 'save':
            value = library.save(args.area_id,
                                 specification=read_json(args.spec) if args.spec else None,
                                 project=args.project, live=args.project is None)
            print(f"Saved {value['name']} (revision {value['revision']}, {value['layer_count']} verified layers)")
            print(library.path(value['project_path']))
            print('Local shared datasets required; this is not a portable package.')
            return
        if args.command == 'verify':
            value = library.verify(args.area_id)
        elif args.command == 'open':
            value = library.open(args.area_id)
        elif args.command == 'show':
            value = library.entry(args.area_id)
        elif args.command == 'update':
            value = library.update(args.area_id, args.status)
        elif args.command == 'note':
            value = library.observe(args.area_id, text=args.text, candidate_id=args.candidate,
                                    visited=boolean(args.visited), rock_type=args.rock_type,
                                    geological_features=args.features,
                                    possible_opening=boolean(args.possible_opening), photos=args.photo,
                                    follow_up=boolean(args.follow_up), observation_id=args.revise)
        elif args.command == 'notes':
            path = library.path(library.entry(args.area_id)['personal_notes'])
            value = read_json(path)['events'] if path.exists() else []
            if args.candidate:
                value = [e for e in value if e['candidate_id'] == args.candidate]
        elif args.command == 'candidate':
            entry = library.entry(args.area_id)
            if library._ranking_sha(entry['candidate_csv']) != entry['candidate_csv_sha256']:
                raise RuntimeError('Original candidate ranking changed')
            value = next((r for r in library._ranking(entry['candidate_csv'])
                          if r['object_id'] == args.candidate_id), None)
            if value is None:
                raise ValueError(f'Unknown candidate {args.candidate_id} in {args.area_id}')
        print(json.dumps(value, indent=2, ensure_ascii=False))
    except (ValueError, KeyError, FileNotFoundError, RuntimeError, FileExistsError, ConnectionError, TimeoutError) as error:
        parser.exit(1, f'Library: {error}\n')


if __name__ == '__main__':
    main()
