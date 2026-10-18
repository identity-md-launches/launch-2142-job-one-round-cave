#!/usr/bin/env python3
"""Read-only review of the order of branch-grown lines in a merge candidate."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SPEC = importlib.util.spec_from_file_location(
    'candidate_order_tree', Path(__file__).resolve().parents[1] / 'tree-review' / 'tree_review.py')
tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tree)
SIDES = ('base', 'ours', 'theirs', 'candidate')
LIMITS = [
    'For each branch, select line identities whose exact count grew from base; retain all their branch occurrences in order.',
    'Each branch trace must be a subsequence of the candidate; unrelated candidate lines may interleave freely.',
    'No ordering constraint between independent branches; shared occurrences may satisfy both traces.',
    'Untouched lines, net-zero moves, deletions, empty-file presence, syntax and semantics are not checked.',
    'Intentional reordering or removal can require review; checked means this policy passed, not approval.',
    'Exact line endings matter. Line hashes omit source text but can reveal guessable content.',
    'Reads require stable bounded UTF-8 trees; no atomic snapshot or protection against path races.']


def branch_order(base, branch, candidate):
    """Linear scans, no ambiguous diff alignment or candidate execution."""
    before = Counter((base or '').splitlines(keepends=True))
    lines = (branch or '').splitlines(keepends=True)
    after = Counter(lines)
    grown = {line for line in after if after[line] > before[line]}
    trace = [(number, line) for number, line in enumerate(lines, 1) if line in grown]
    result = (candidate or '').splitlines(keepends=True)
    available = Counter(result)
    missing = sum(max(0, after[line] - available[line]) for line in grown)
    matched = 0
    for line in result:
        if matched < len(trace) and line == trace[matched][1]:
            matched += 1
    first = None if matched == len(trace) else {
        'branch_line': trace[matched][0],
        'line_sha256': hashlib.sha256(trace[matched][1].encode('utf-8')).hexdigest()}
    return {'status': 'checked' if first is None else 'review',
            'issue': None if first is None else
                     'missing_occurrences' if missing else 'order_changed',
            'selected_line_identities': len(grown), 'trace_lines': len(trace),
            'matched_prefix_lines': matched, 'missing_occurrences': missing,
            'first_unmatched': first}


def inspect(sources):
    if len(sources) != 4:
        raise ValueError('exactly four trees required: base, ours, theirs, candidate')
    files = set().union(*(set(source['files']) for source in sources))
    directories = set().union(*(source['directories'] for source in sources))
    collisions = sorted(files & directories)
    rows = []
    for path in sorted(files):
        blocked = [p for p in collisions if path == p or path.startswith(p + '/')]
        if blocked:
            rows.append({'path': path, 'status': 'blocked', 'blocked_by': blocked})
            continue
        base, ours, theirs, candidate = [s['files'].get(path) for s in sources]
        branches = {side: branch_order(base, text, candidate)
                    for side, text in (('ours', ours), ('theirs', theirs))}
        rows.append({'path': path, 'status': 'review' if any(
            b['status'] == 'review' for b in branches.values()) else 'checked',
            'branches': branches})
    totals = {status: sum(row['status'] == status for row in rows)
              for status in ('checked', 'review', 'blocked')}
    return {'schema': 'candidate-order/v1',
            'needs_review': bool(totals['review'] or totals['blocked']),
            'inputs': {side: tree.manifest(source) for side, source in zip(SIDES, sources)},
            'counts': totals, 'files': rows, 'limits': LIMITS}


def from_directories(paths):
    if len(paths) != 4:
        raise ValueError('exactly four directories required')
    budget = [0]
    return inspect([tree.snapshot(path, budget) for path in paths])


def demo():
    base = 'Review the inputs.\n'
    ours = base + 'Prepare the candidate.\nInspect the candidate.\n'
    theirs = base + 'Keep the receipt.\n'
    good = ours + 'Keep the receipt.\n'
    reversed_steps = base + 'Inspect the candidate.\nPrepare the candidate.\nKeep the receipt.\n'
    def report(candidate):
        return inspect([{'files': {'guide.md': text}, 'directories': set()}
                        for text in (base, ours, theirs, candidate)])
    return {'ordered': report(good), 'same_counts_reversed': report(reversed_steps)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='BASE_DIR OURS_DIR THEIRS_DIR CANDIDATE_DIR')
    parser.add_argument('--demo', action='store_true')
    args = parser.parse_args(argv)
    if (args.demo and args.paths) or (not args.demo and len(args.paths) != 4):
        parser.error('provide four directories or --demo')
    try:
        report = demo() if args.demo else from_directories(args.paths)
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as error:
        print('candidate-order: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if args.demo:
        return 0 if (not report['ordered']['needs_review'] and
                     report['same_counts_reversed']['needs_review']) else 1
    return 1 if report['needs_review'] else 0


if __name__ == '__main__':
    sys.exit(main())
