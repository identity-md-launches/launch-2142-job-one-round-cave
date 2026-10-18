# Support Prune

Remove releases from a finite Offline Resolver catalog when a root excludes
them or one of their dependencies has no release left that satisfies its
constraint. The process propagates through chains. The JSON output includes
an equivalent `reduced_catalog`, root candidates, and removal reasons. Run
this example from the repository root:

```sh
python3 -B line-4/tools/support-prune/prune.py demo
```

The demo uses the line's committed historical Requests metadata projection.
It reads that local file and prints JSON; it makes no network call and writes
nothing. No package code is installed or executed. Python 3.9+ and its standard
library are sufficient. For another catalog, pass a path inside the current
workspace; the inherited loader rejects larger than 1 MB, duplicate JSON keys,
and paths resolving outside that workspace.

I ran the command on the committed historical Requests projection: it removed
Requests 2.31.0 and urllib3 2.5.0 because the roots pin Requests 2.32.5 and
urllib3 below 2. It retained eight releases and reported no empty root domain.
Seven tests passed, including 300 seeded catalogs where original and reduced
catalogs gave the same complete-solver status, selected assignment and exact
solution set under a separate Cartesian reachability checker.

The catalog has `packages` and `roots` objects. Each package maps numeric
release strings to dependency maps; each root or dependency maps a package name
to `*` or comma-conjoined numeric comparisons. This is the Offline Resolver's
finite grammar, not full package-manager syntax. The output preserves every
complete compatible selection: a removed release either violates a root or
has a dependency with no surviving candidate, so no valid selection could
have used it. This follows inductively from the root exclusions and first
removals with no catalog candidate at all.
The tool retains package keys with empty release maps. It does not claim that
surviving releases form one compatible selection: conflicts between branches
or multiple incoming constraints can remain. `proven_unsatisfiable` means at
least one root has no candidate after pruning (exit 1). Otherwise exit 0 means
only that this local check found no such proof. Invalid input exits 2.

The emitted catalog can be supplied directly to Offline Resolver or its audit
tools. Names are canonicalized, while original release spellings and constraint
strings remain. A removal reason gives either the excluding root or one
dependency whose candidate domain was empty at the removal step; it is not a
complete conflict explanation.

Checks run locally: the committed Requests demo and focused propagation,
cycle, branch-conflict, missing-target, and randomized equivalence tests via
`python3 -B -m unittest discover -s line-4/tools/support-prune -p 'test_*.py'`.
