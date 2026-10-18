# Candidate Order

Review a separately supplied text merge candidate for lost ordering among
branch-grown lines. Counting retained lines alone misses a candidate that puts
“Inspect the candidate” before “Prepare the candidate”. This tool flags that
case even when every line count is unchanged. It reads only; it never merges,
edits, executes candidate code, or approves a resolution.

From the workspace root, run this offline Python standard-library demo:

```sh
python3 -B line-1/tools/candidate-order/candidate_order.py --demo
```

The demo exits 0 after checking that the ordered candidate passes and that a
candidate with the same counts but reversed steps needs review. For your own
stable UTF-8 directory trees:

```sh
python3 -B line-1/tools/candidate-order/candidate_order.py BASE OURS THEIRS CANDIDATE
```

Exit 0 means the policy checked; 1 means review or a path collision; 2 means
invalid input. JSON includes all four exact-byte tree manifests, per-path and
per-branch results, matched-prefix counts, and the branch line number and hash
of the first unmatched trace item. `missing_occurrences` distinguishes missing
counts from `order_changed` (all required counts exist, but their order fails).
Source text is omitted; paths are JSON escaped. Hashes are not confidentiality
or author authentication.

For each branch separately, compare exact line counts with base. Select each
line identity whose count increased, then take **all occurrences** of those
identities in branch order. Require this trace to be a subsequence of the
candidate. Other lines can freely interleave. Selecting all occurrences ensures
an old identical line cannot hide the loss of a new duplicate. Each branch is
checked independently; shared additions need not be duplicated. Processing is
linear in the input lines apart from sorting paths, with no diff alignment.

This is a conservative review policy. An intended reorder can need review.
Identical occurrences have no individual identity. A trace may match at another
location; its position relative to untouched lines is not checked. Net-zero
moves, deletions, empty-file presence, contributor intent, conflict markers,
syntax and semantics are outside the check. Use Candidate Additions and Deletion
Audit alongside this check and review the actual diff. A passing trace is never
approval. CRLF, LF and a missing final newline are distinct.

Reuses the sibling `tree-review` bounded reader and manifest functions, which
import `merge-review` and `threeway`. Keep those folders alongside this one.
No merger is called. Four trees share an 8 MiB budget; each tree has at most 128
files, 256 directories and depth 16; each file at most 1 MiB and 4,000 lines.
NUL, invalid UTF-8, symlinks, special files, parent traversal and paths outside
the current workspace are refused. File/directory collisions and descendants
are blocked. Reads require stable trusted directories and are not atomic.
Empty directories appear in manifests but are not ordered or merged.

Validation performed: 13 focused tests, including 225 exhaustive tiny repeated
sequence comparisons against an independent index-combination oracle. A real
trial used copies of the inherited Threeway README, kept two contributors'
additions, then reversed two added instructions: pass became review while all
line counts and all source inputs stayed unchanged. The candidate manifest
changed. Invalid UTF-8, NUL, oversized line count and symlinks were refused.

```sh
python3 -B -m unittest discover -s line-1/tools/candidate-order -p 'test_*.py'
```

No network, external dependency, coin, wallet or transaction is needed.
