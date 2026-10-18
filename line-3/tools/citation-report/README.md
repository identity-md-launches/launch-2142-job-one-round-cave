# Citation Report

This is a small handoff layer for the existing Citation Ledger. It checks every
hash-pinned citation against the current local corpus, then emits only the
review queue: citation id, source, status, and whether the passage needs review.
It uses Python 3.9+ and the standard library, and delegates validation to the
workspace-local ledger without rewriting either input.

Try the inherited real historical ZTO-first example from the repository root:

```sh
python3 -B line-3/tools/citation-report/report.py demo
```

When tried, this reports two unchanged citations with sources `zto.md` and
`pool.md`, and a zero-item review queue. These are inherited historical
ZTO/IMD observations, not current chain state. A changed source is reported as
`needs_review: true`; this is a warning, not a claim that the underlying source
is true.

Check your own saved `citation-ledger/v1` file against its local corpus:

```sh
python3 -B line-3/tools/citation-report/report.py path/to/corpus path/to/ledger.json
```

Keep sibling `citation-ledger/`, `citation-reanchor/`, and `evidence-search/`
folders with this tool. All input paths must remain inside the current working
directory. Validation and source-change detection come from Citation Ledger;
unsafe paths, duplicate IDs, malformed JSON, missing files and invalid anchors
fail the whole check. No files are rewritten and no network request is made.

Each row's `source` is the relative `anchor.path` from its validated ledger
entry, joined by citation ID. It remains available for `unchanged`,
`same_lines_changed_source`, `relocated`, `missing` and `ambiguous` results.
In particular, a missing passage or an ambiguous match still names the file
to review. `source` does not claim a passage exists or supply a replacement
line range; use Citation Ledger's full result for those details. File renames
are not discovered. A missing file is an error, distinct from a missing passage.

Successful output keeps the original CLI exit code **0**, including when
`review_count` is positive. Inspect the count or `needs_review` to identify
changed citations. Invalid input or I/O errors return **2** with JSON on stderr
and no partial report on stdout.

## Checks actually run

```sh
python3 -B line-3/tools/citation-report/test_report.py -v
```

Nine regression tests passed: all five citation statuses retain their source,
IDs still match sources if checked results are reordered, shared source files
work, malformed/unsafe inputs fail, inputs remain unchanged, the CLI preserves
its behavior, and the real historical ZTO demo reports both source paths.
Temporary fixtures are written only under `test/scratch/`.
