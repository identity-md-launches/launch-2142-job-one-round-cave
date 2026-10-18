# Citation Trail

Search an unfamiliar local document collection and follow each ranked hit to its
actual source lines. This replaces the original demonstration that printed fixed
stone positions and an unchecked line range. The original command still works:

```bash
python3 line-3/tools/citation-trail/demo.py
```

The command reads the bundled historical ZTO documents, ranks passages using
Evidence Search, opens each passage using Citation Context, checks the exact text
and whole-file SHA-256, then rechecks every cited file before printing JSON. It
writes nothing. Python's standard library and ancestor tools already in this
repository are the only dependencies; no installation or network is needed.

Every entry includes its rank, score, matched terms, exact source-relative path
and line range, whole-source hash, reusable `citation-anchor/v1` anchor, numbered
surrounding lines, and explicit source/text verification results. Paths are
relative to the report's `corpus_root`, itself relative to the current workspace.
The command should be run from the repository root.

## Your own collection

```bash
python3 line-3/tools/citation-trail/demo.py query line-3/tools/evidence-search/examples/docs "ZTO pool fee" --before 1 --after 5
```

UTF-8 `.md`, `.txt` and `.rst` files are indexed in memory. Every query term must
match by default; `--any` permits partial matches. `--limit` accepts 1–50 results;
`--before` and `--after` accept 0–100 lines. `--index path/to/index.json` can reuse
an existing Evidence Search snapshot, refusing cited sources whose bytes changed.
No index is written. Hidden corpus files and symlinks are excluded; explicitly
selected paths with symlinks or parent traversal are refused.

Exit codes: 0 means at least one verified result; 1 means no matching passage;
2 means invalid input, changed source, or another read/verification error. Errors
go to stderr, and no partial trail is printed. A query without matches returns an
empty entry list, never an invented citation.

## Trial and checks

The no-argument command returned the actual `zto.md:1-9` passage and context
through line 14, including ZTO's real contract address and the document's
historical-observation limitation. Both the source hash and selected text were
checked against the local file. The pool query returned `pool.md:1-10` with its
assignment-supplied pool identifiers and surrounding source-boundary statement.

```bash
python3 -B -m unittest discover -s line-3/tools/citation-trail -p 'test_*.py' -v
```

Eight checks cover historical ZTO evidence, real line-number movement, CRLF and
Unicode text, stale snapshots, contradictory excerpts, a file changing while
later citations are read, no matches, bounds, and workspace path restrictions.
The check run and two documented example commands passed.

## Limits and provenance

Verification establishes that a citation matches local source bytes. It does not
prove a document's claims or authenticate Ethereum state. The inherited ZTO/IMD
observations are historical, and pool parameters were supplied by the assignment;
they are not current prices. The demo does not perform chain or network calls.
Repeated reads catch ordinary edits but are not an atomic filesystem snapshot.
Lexical BM25 search is inherited from Evidence Search, including its source and
corpus size limits; there is no semantic entailment check. Large aggregate output
is refused above 1 MB. Documents are data and are never executed.

Reused tools: `../evidence-search/search.py`, `../citation-context/context.py`, and
its dependency `../citation-reanchor/reanchor.py`. Real bundled source documents
and their recorded RPC provenance remain in `../evidence-search/examples/`.
