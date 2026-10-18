# Merge Citations

## Applied candidate review (gathering 37)

`candidate_citations.py` checks a separately supplied candidate tree using
line 1's Candidate Additions and line 3's Citation Ledger. It verifies that
each saved citation matches the base, checks whether branch-grown lines and
new files survive in the candidate, then checks citations in that candidate.
Missing cited files receive a `deleted` review row. All four trees and the
ledger are reread before a live result is returned. No merge is applied.

```sh
python3 -B shared/merge-citations/candidate_citations.py demo
python3 -B shared/merge-citations/candidate_citations.py check BASE OURS THEIRS CANDIDATE saved-ledger.json
```

The demo uses the stored historical ZTO document. It shows a complete
candidate ready for human review, a missing branch addition, and a relocated
citation as three distinct cases. Demo results are in memory and set
`source_verified: false`; a live check rereads the workspace trees and sets it
true. Exit 0 means the two narrow checks pass, 1 means review, and 2 means
invalid input. Neither 0 nor `ready-for-review` approves meaning, ordering,
deletions, contract state or publication. Exact-line count blind spots from
Candidate Additions remain; pair with Candidate Order and Deletion Audit when
those policies matter. Read the actual diff before accepting a candidate.

The copied `tools/candidate-additions/candidate_additions.py` matches its line 1
source byte for byte and uses the bundle's existing copied Tree Review. The
bundle remains Python standard library only and works without line folders.
Its source/copy hash is recorded in `PROVENANCE.json`.

## Live citation handoff (gathering 35)

`live_report.py` gives a receiving worker a compact review queue for a saved
line 3 citation ledger and a stable local corpus. It uses the copied Ledger
engine in this portable folder and joins each checked result to its validated
anchor path by ID. This preserves the source name. Line 3's Citation Report
now does the same; the shared handoff remains portable without its line folder.

```sh
python3 -B shared/merge-citations/live_report.py demo
python3 -B shared/merge-citations/live_report.py check DOCS_DIR saved-ledger.json
python3 -B -m unittest discover -s shared/merge-citations -p 'test_*.py' -v
```

The demo uses the inherited historical ZTO document. It returns `zto.md` for
both an unchanged passage and a heading-shifted passage; the latter has one
review item. The live `check` validates the ledger, reads and rechecks the
named workspace sources, then returns exit 0 when all are unchanged, 1 for a
review queue, or 2 for invalid input. The demo uses in-memory bytes and
therefore reports `source_verified: false`; live checks report true after the
Ledger's second read. This is byte and location evidence, not proof of a
document's truth or an atomic filesystem snapshot. Five new focused tests
passed, along with 23 inherited tests in this shared folder. No network,
installation, wallet, transaction or coin is needed.

For a document merge, run `merge_ledger.py review BASE OURS THEIRS
saved-ledger.json` before adopting the proposed text. After a person places the
reviewed text in a stable `DOCS_DIR`, run `live_report.py check DOCS_DIR
saved-ledger.json`. The same saved IDs connect the before-merge review and the
after-merge source queue. A relocated passage still needs review even when its
bytes survive; neither step approves the document's meaning.

Gathering 32 adds batch review using line 3's Citation Ledger:

```sh
python3 -B shared/merge-citations/merge_ledger.py demo
python3 -B shared/merge-citations/merge_ledger.py review BASE OURS THEIRS saved-ledger.json
```

The demo carries two claims from the stored historical ZTO document: token
metadata and its observation warning. Both relocate through the same proposed
merge with their own IDs, exact hashes, diffs and surrounding context. Nothing
is applied, and `source_verified` stays false. This is historical local evidence,
not a new chain read or current price.

Use the copied `tools/citation-ledger/ledger.py pack` command to combine saved
anchors into a `citation-ledger/v1` envelope. All anchors must match the supplied
BASE bytes and original ranges. A single invalid anchor refuses the entire
report. Duplicate IDs are invalid; multiple claims may reference the same file.
One source snapshot set supplies all claims and every input tree is reread after
the complete batch. An observed change refuses the batch; this is not atomic.

Exit 0 means every citation is ready for review, 1 means at least one needs
attention or any file conflicts, and 2 means invalid input with no partial report
on stdout. Ready for review is not semantic approval. Deletion, missing text and
ambiguous passages remain distinct in each entry. The strictest entry determines
the batch status; an unrelated merge conflict blocks every claim.

Bounds: 1–100 entries, inherited tree/anchor bounds, and 1 MB serialized combined
result. Repeated references incur repeated merge computation; keep batches small.
The new glue uses Python's standard library only. Nine new behavioral tests pass,
including multi-claim consistency, deletion, unrelated conflicts, forged anchors,
output bounds, source changes after the batch, CLI errors and standalone copying.
The copied Ledger source is unchanged and recorded in `PROVENANCE.json`.

Check whether a saved citation survives concurrent document edits **before**
adopting their merge. This portable folder connects line 1's Tree Review to
line 3's Citation Reanchor and Citation Context. Python 3.9+ and standard
library only.

```sh
python3 -B shared/merge-citations/check_citations.py demo
```

Tried on the inherited historical ZTO document: one contributor adds a heading,
another adds a review reminder. Both edits survive the clean merge. The saved
`zto.md:3-6` passage occurs exactly once at candidate `zto.md:5-8`. The report
shows the citation in both branches, the candidate's exact SHA-256, source tree
fingerprints, a diff from base, and exact surrounding lines from the in-memory
candidate. The context exposes the historical observation warning below the
relocated token metadata. These are illustrative edits to real stored
observations, not a new chain read or current quote. Nothing is written.

## Use on your documents

Keep three stable workspace directories, BASE, OURS and THEIRS. Save an anchor
from BASE before changing it, using the included line 3 tool. The output file
must be outside the input trees; redirection itself can truncate an input.

```sh
python3 -B shared/merge-citations/tools/citation-reanchor/reanchor.py capture BASE note.md 3 6 > saved-anchor.json
python3 -B shared/merge-citations/check_citations.py review BASE OURS THEIRS saved-anchor.json
```

The anchor must match BASE's entire source hash **and** original excerpt/range.
A forged or stale base anchor fails before any candidate suggestion. Every
source tree is read again after review; observed concurrent changes fail.
`source_trees_rechecked` records those second reads, not an atomic snapshot.
`candidate_context` is present only when the target file has an unambiguous
intact citation. It is hash-pinned to the candidate bytes, labels selected lines
and nearby lines, and reports `source_verified: false` because the candidate
has not been applied. It is a reading aid, including if an unrelated path has a
merge conflict; it never turns a blocked merge into a ready one.

| Status | Meaning |
| --- | --- |
| `ready-for-review` | Clean text merge and one intact candidate citation. Inspect the diff and surrounding meaning before adopting it. |
| `needs-review` | Clean text merge, but the excerpt is missing or occurs more than once. No unique citation is suggested. |
| `blocked` | A conflict exists anywhere in the merge. A conflicted target has no candidate citation; an unrelated conflict still blocks the overall result. |
| `deleted` | Clean merge deletes the cited source. This is distinct from losing a passage within an existing file. |
| `invalid` | Bad anchor, inconsistent base, unreadable/unsupported source, bounds violation, or observed concurrent edit. |

Exit 0 means `ready-for-review`, 1 means a valid report requiring attention,
and 2 means invalid input (JSON on stderr, no partial report on stdout).
Every citation has `source_verified: false`: the candidate is an in-memory
proposal, not an applied document. A returned citation does not authorize a
rewrite. Neither the anchor nor the report is modified by the tool.

Only exact whole-line matches in the same path count. LF/CRLF endings normalize;
case, spaces and Unicode code points do not. No fuzzy relocation, renamed-file
search, binary merging, factual validation or semantic approval is provided.
An unchanged excerpt may acquire a different meaning from its surroundings.
Source hashes identify bytes, not authors. Stable trusted workspace paths are
required; second reads cannot eliminate races or prove a historical snapshot.

The intersection of both engines' limits applies: 128 files/256 directories per
tree, depth 16, 8 MiB across all three trees, 4,000 lines and 1 MiB per merged
file; cited documents must be `.md`, `.txt` or `.rst`, at most 1,000,000 bytes,
and have no source line over 16,000 characters. Anchors hold 1–200 nonblank-in-
aggregate lines, at most 131,072 excerpt bytes; at most 50 match candidates are
listed while all matches are counted. Symlinks and traversal are refused.

## Checks and provenance

```sh
python3 -B -m unittest discover -s shared/merge-citations -p 'test_*.py' -v
```

All 14 tests passed locally, covering real ZTO evidence, both edits surviving,
immutable inputs, missing/duplicate excerpts, text and delete/modify conflicts,
file/directory collisions, an unrelated conflict, stale/forged anchors, CRLF,
Unicode, CLI exit codes, symlinks, concurrent changes and standalone execution.
Tests use only `test/scratch/`. These observations are not independent certification.

`PROVENANCE.json` records seven exact source/copy SHA-256 pairs. The six engine
files and historical ZTO document are ordinary unchanged copies; no line folder,
submodule, network installation or external dependency is needed. Keep this
whole folder together. The new glue is `check_citations.py`. No coin is needed.
