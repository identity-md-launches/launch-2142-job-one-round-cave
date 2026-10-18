#!/usr/bin/env python3
"""Prune releases excluded by roots or lacking local dependency support."""
import argparse
from collections import defaultdict, deque
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
RESOLVER = HERE.parent / 'offline-resolver' / 'resolve.py'
spec = importlib.util.spec_from_file_location('line4_offline_resolver_prune', RESOLVER)
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def prune(catalog):
    """Return an equivalent reduced catalog and a one-step reason per removal.

    A release is removed when a root excludes it or one dependency has no
    remaining allowed release. Valid complete selections can never include a
    removed release, by induction over removal order. Surviving releases may
    still be mutually incompatible; this is not a solver.
    """
    packages, roots = resolver.validate(catalog)
    ordered = {
        package: sorted(releases, key=resolver.version)
        for package, releases in sorted(packages.items())
    }
    requirements = {}
    supports = {}
    reverse = defaultdict(list)
    alive = {(package, release) for package, releases in ordered.items()
             for release in releases}
    queue = deque()
    reasons = {}

    for package, releases in ordered.items():
        for release in releases:
            source = (package, release)
            deps = list(packages[package][release].items())
            requirements[source] = deps
            for index, (target, constraint) in enumerate(deps):
                count = sum(resolver.accepts(candidate, constraint)
                            for candidate in ordered.get(target, ()))
                supports[source, index] = count
                reverse[target].append((source, index, constraint))

    def remove(source, reason):
        if source not in alive:
            return
        alive.remove(source)
        reasons[source] = {'package': source[0], 'release': source[1], **reason}
        queue.append(source)

    for source in sorted(requirements):
        package, release = source
        if package in roots and not resolver.accepts(release, roots[package]):
            remove(source, {'source': 'root', 'constraint': roots[package]})

    for source in sorted(requirements):
        for index in range(len(requirements[source])):
            if supports[source, index] == 0:
                target, constraint = requirements[source][index]
                remove(source, {'source': 'dependency', 'dependency': target,
                                'constraint': constraint})
                break

    while queue:
        target_package, lost_release = queue.popleft()
        for source, index, constraint in reverse[target_package]:
            if source not in alive or not resolver.accepts(lost_release, constraint):
                continue
            key = source, index
            supports[key] -= 1
            if supports[key] == 0:
                target, constraint = requirements[source][index]
                remove(source, {'source': 'dependency', 'dependency': target,
                                'constraint': constraint})

    reduced = {
        'packages': {
            package: {release: packages[package][release]
                      for release in releases if (package, release) in alive}
            for package, releases in ordered.items()
        },
        'roots': roots,
    }
    root_candidates = {
        package: [release for release in ordered.get(package, ())
                  if (package, release) in alive and resolver.accepts(release, constraint)]
        for package, constraint in roots.items()
    }
    report = {
        'status': ('proven_unsatisfiable' if any(not candidates for candidates
                                                 in root_candidates.values())
                   else 'not_proven_unsatisfiable'),
        'original_releases': len(requirements),
        'retained_releases': len(alive),
        'removed': [reasons[source] for source in sorted(reasons)],
        'root_candidates': root_candidates,
        'reduced_catalog': reduced,
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace-local catalog JSON, or demo')
    args = parser.parse_args(argv)
    try:
        path = (HERE.parent / 'offline-resolver' / 'examples' / 'requests.json'
                if args.catalog == 'demo' else args.catalog)
        result = prune(resolver.load(path))
    except (resolver.Invalid, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'invalid', 'error': str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result['status'] == 'proven_unsatisfiable' else 0


if __name__ == '__main__':
    sys.exit(main())
