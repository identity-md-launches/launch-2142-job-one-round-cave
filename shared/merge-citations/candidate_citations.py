#!/usr/bin/env python3
"""Review an applied candidate's retained additions and saved source citations."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


additions = module('shared_candidate_additions', 'tools/candidate-additions/candidate_additions.py')
ledger = module('shared_candidate_ledger', 'tools/citation-ledger/ledger.py')


def review_snapshots(snapshots, saved):
    """Inspect four already-read UTF-8 trees; demo results are not live verified."""
    if len(snapshots) != 4:
        raise ValueError('base, ours, theirs and candidate snapshots required')
    ledger.validate(saved)
    base, _, _, candidate = snapshots
    rows = []
    for entry in saved['entries']:
        anchor = entry['anchor']
        path = anchor['path']
        original = base['files'].get(path)
        if original is None:
            raise ledger.engine.SearchError('cited source missing from base: ' + path)
        if ledger.anchor.check_bytes(anchor, original.encode('utf-8'))['status'] != 'unchanged':
            raise ledger.engine.SearchError('saved citation does not match base: ' + path)
        current = candidate['files'].get(path)
        if current is None:
            status = 'deleted'
        else:
            status = ledger.anchor.check_bytes(anchor, current.encode('utf-8'))['status']
        rows.append({'id': entry['id'], 'source': path, 'status': status,
                     'needs_review': status != 'unchanged'})
    addition_report = additions.inspect(snapshots)
    needs_review = addition_report['needs_review'] or any(row['needs_review'] for row in rows)
    return {'format': 'candidate-citations/v1',
            'status': 'review' if needs_review else 'ready-for-review',
            'needs_review': needs_review, 'source_verified': False,
            'inputs_rechecked': False,
            'candidate_additions': addition_report,
            'citations': {'entry_count': len(rows),
                          'review_count': sum(row['needs_review'] for row in rows),
                          'entries': rows},
            'limits': ['Exact line counts and exact citation bytes only; inspect meaning and ordering.',
                       'A recheck detects ordinary file changes, not an atomic filesystem snapshot.']}


def check(base, ours, theirs, candidate, ledger_path):
    paths = [base, ours, theirs, candidate]
    saved = ledger.load(ledger_path)
    budget = [0]
    snapshots = [additions.tree.snapshot(path, budget) for path in paths]
    report = review_snapshots(snapshots, saved)
    expected = [additions.tree.manifest(snapshot) for snapshot in snapshots]
    budget = [0]
    rechecked = [additions.tree.manifest(additions.tree.snapshot(path, budget)) for path in paths]
    if expected != rechecked or saved != ledger.load(ledger_path):
        raise ValueError('input changed during review; retry with stable trees and ledger')
    report['inputs_rechecked'] = True
    report['source_verified'] = True
    return report


def demo():
    raw = (HERE / 'examples/zto.md').read_bytes()
    text = raw.decode('utf-8')
    saved = {'format': ledger.FORMAT, 'entries': [
        {'id': 'zto-metadata', 'anchor': ledger.anchor.capture_bytes(raw, 'zto.md', 3, 6)}]}
    def snapshot(files):
        return {'files': files, 'directories': set()}
    base = snapshot({'zto.md': text})
    ours = snapshot({'zto.md': text, 'note.md': 'Review the source.\n'})
    theirs = snapshot({'zto.md': text, 'other.md': 'Keep both additions.\n'})
    complete = snapshot({'zto.md': text, 'note.md': 'Review the source.\n',
                         'other.md': 'Keep both additions.\n'})
    omitted = snapshot({'zto.md': text, 'note.md': 'Review the source.\n'})
    relocated = snapshot({**complete['files'], 'zto.md': '# Reading copy\n' + text})
    return {'example': 'Historical stored ZTO document; in-memory candidate examples.',
            'complete': review_snapshots([base, ours, theirs, complete], saved),
            'omitted_addition': review_snapshots([base, ours, theirs, omitted], saved),
            'relocated_citation': review_snapshots([base, ours, theirs, relocated], saved)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('demo')
    review = subs.add_parser('check')
    for name in ('base', 'ours', 'theirs', 'candidate', 'ledger'):
        review.add_argument(name)
    args = parser.parse_args(argv)
    try:
        report = demo() if args.command == 'demo' else check(
            args.base, args.ours, args.theirs, args.candidate, args.ledger)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        if args.command == 'demo':
            return 0 if (report['complete']['status'] == 'ready-for-review' and
                         report['omitted_addition']['status'] == 'review' and
                         report['relocated_citation']['status'] == 'review') else 1
        return 1 if report['needs_review'] else 0
    except (ledger.engine.SearchError, OSError, UnicodeError, ValueError,
            RecursionError, OverflowError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
