#!/usr/bin/env python3
"""Read-only addition-count review of a separately supplied merge candidate."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SPEC = importlib.util.spec_from_file_location(
    'candidate_additions_tree', Path(__file__).resolve().parents[1] / 'tree-review' / 'tree_review.py')
tree = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tree)
SIDES = ('base', 'ours', 'theirs', 'candidate')
LIMITS = [
    'Exact per-path line count increases only; movement, replacement and intent need human review.',
    'Shared additions are required once at the greatest branch count, not summed.',
    'Net-zero moves and additions offset by identical deletions are invisible.',
    'No check of ordering, deletions, conflict markers, syntax, semantics or approval.',
    'Any file/directory collision and its descendants are conservatively blocked.',
    'Stable bounded UTF-8 trees required; reads are not atomic or protected against path races.',
    'Hashes identify bytes, not authors; source text is omitted but hashes can reveal guessable lines.']


def counts(text):
    return Counter((text or '').splitlines(keepends=True))


def audit_candidate(path, base, ours, theirs, candidate):
    original, left, right, result = map(counts, (base, ours, theirs, candidate))
    missing = []
    # Net increases avoid interpreting a mere reordering as an insertion.
    for line in sorted(set(left) | set(right)):
        required = max(left[line], right[line])
        if required > original[line] and result[line] < required:
            missing.append({
                'line_sha256': hashlib.sha256(line.encode('utf-8')).hexdigest(),
                'base_occurrences': original[line],
                'branch_occurrences': {'ours': left[line], 'theirs': right[line]},
                'required_occurrences': required,
                'candidate_occurrences': result[line],
                'added_by': [side for side, inventory in (('ours', left), ('theirs', right))
                             if inventory[line] > original[line]]})
    # Missing and empty differ: an added empty file has no lines to count.
    added_file = base is None and (ours is not None or theirs is not None)
    missing_file = added_file and candidate is None
    return {'path': path, 'status': 'review' if missing or missing_file else 'checked',
            'candidate_present': candidate is not None,
            'candidate_sha256': None if candidate is None else
                hashlib.sha256(candidate.encode('utf-8')).hexdigest(),
            'missing_added_file': missing_file, 'missing_lines': missing}


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
        else:
            rows.append(audit_candidate(path, *(source['files'].get(path) for source in sources)))
    totals = {status: sum(row['status'] == status for row in rows)
              for status in ('checked', 'review', 'blocked')}
    return {'schema': 'candidate-additions/v1',
            'needs_review': bool(totals['review'] or totals['blocked']),
            'inputs': {side: tree.manifest(source) for side, source in zip(SIDES, sources)},
            'counts': totals, 'files': rows, 'limits': LIMITS}


def from_directories(paths):
    if len(paths) != 4:
        raise ValueError('exactly four directories required')
    budget = [0]
    return inspect([tree.snapshot(path, budget) for path in paths])


def demo():
    base = 'Check the source.\n'
    ours = base + 'Keep the receipt.\n'
    theirs = base + 'Review both contributions.\n'
    good = ours + 'Review both contributions.\n'
    return {'complete': audit_candidate('guide.md', base, ours, theirs, good),
            'omitted': audit_candidate('guide.md', base, ours, theirs, ours),
            'missing_empty_addition': audit_candidate('empty.txt', None, '', None, None),
            'limits': LIMITS}


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
        print('candidate-additions: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if args.demo:
        return 0 if (report['complete']['status'] == 'checked' and
                     report['omitted']['status'] == 'review' and
                     report['missing_empty_addition']['status'] == 'review') else 1
    return 1 if report['needs_review'] else 0


if __name__ == '__main__':
    sys.exit(main())
