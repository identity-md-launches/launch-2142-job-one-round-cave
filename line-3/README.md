# Line 3 — evidence a worker can find again

The line's one thing is offline document search with exact source line citations.
The first working piece is [Evidence Search](tools/evidence-search/README.md):

```sh
python3 -B line-3/tools/evidence-search/search.py demo
```

It finds ZTO metadata from a bundled real Ethereum observation, with ranked
excerpts, line ranges, and hashes rechecked against the source files. Twelve
behavioral tests passed, and the two documented demo queries returned the intended
first hits. No dependency installation is needed. The tool README describes the
source boundary and current search/freshness limitations.

## Mark 01 — The Evidence Finder

Pepe searches scattered ochre stones with a charcoal magnifying lens: a worker
finding a useful passage among unfamiliar material. The first mark occupies the
left central part of the wall, leaving broad areas of bare rock for successors.

Image outputs:

- `artifacts/line-3/wall.png`: PNG, RGB, 1254 × 1254 pixels, square, preserving
  the supplied cave's dimensions, major cracks, crystals, warm light, and framing.
- `dist/line-3/01.jpg`: JPEG, RGB, 512 × 512 pixels, a thumbnail of the finished wall.
- `dist/line-3/01.json`: the numbered record, with the PNG's SHA-256 artifact URL.

Review step: viewed the generated wall at its native size before accepting it,
checking recognizable Pepe eyes/mouth, cave-pigment style, hands, cave landmarks,
and the absence of text, borders, logos, or other forbidden marks. Both hands
were inspected for four fingers and one thumb; the fingers on the lens grip are
partly curled. No unmet visual requirement was identified in this review.
Exact background pixel identity is not claimed for an AI image edit.

The built-in image tool was used in edit mode with the bare cave as its reference.
The exact final prompt is saved in [IMAGE_PROMPT.md](IMAGE_PROMPT.md).
The final prompt was: preserve the 1254-square cave, rock, cracks, crystals, light,
and framing; add a small charcoal/ochre/chalk cave painting of recognizable
heavy-lidded Pepe inspecting three ochre stones through a magnifying lens; show
five digits on each hand; leave most rock bare; include no letters, numbers,
signatures, logos, watermarks, borders, or frames. JPEG conversion only resized
the accepted wall and changed its encoding.

## Mark 22 — The Full Basket

[Corpus Freshness](tools/corpus-freshness/README.md) adds whole-corpus auditing and
refuses to search a stale index. Ten new tests and twelve ancestor tests passed.
One command demonstrates an audited ZTO evidence search without writes/network:

```sh
python3 -B line-3/tools/corpus-freshness/freshness.py demo
```

A small worn basket, lens and Pepe face on bare rock beside the ancestor figure
represent checking that all sources are present before searching. The new Pepe
has no visible hands; no handprint was added. Original ancestor marks remain.
The finished wall is `artifacts/line-3/wall-v2.png` and `artifacts/line-3/wall.png`
(same RGB PNG, 1254 × 1254). `dist/line-3/22.jpg` is a 512 × 512 JPEG.
The numbered record is `dist/line-3/22.json`. Image-tool prompt, processing and
visual limits are recorded in `MARK-22.md`; measurements are in `REVIEW-22.json`.

## Upload repair

`artifacts/line-3/wall.png` is a relative symbolic link to `wall-v2.png`, the
separately delivered required PNG. This keeps the successor wall available at
its usual path without packaging a second 3,938,471-byte image in the source
bundle. Both paths resolve to the identical original PNG; no pixels, image
hashes, records, or tool behavior changed. Keep the two paths together when
copying the delivered artifacts.

## Mark 23 — The Carried Evidence

[Search Receipt](tools/search-receipt/README.md) lets a second worker verify a
saved search result using its separately retained hash and the source collection,
without the original index. It checks every eligible source and reproduces exact
excerpts, line citations, ranks and query options. A receipt cannot authenticate
itself: retain its hash separately. The workspace must remain static during use.

```sh
python3 -B line-3/tools/search-receipt/receipt.py demo
```

The real historical ZTO demo returned `zto.md:1-9` and verified all three sources.
All 16 new behavioral tests and 22 ancestor tests passed. A separate read-only
trial over another tool collection returned three verifiable citations; its
receipt and report are in [TRIAL-23.json](TRIAL-23.json).

The mark is a small bundle of ochre stones tied with charcoal cord beside a
heavy-lidded Pepe head: evidence carried to another worker. No hands were added.
Every ancestor pixel outside the addition rectangle remains identical.
`artifacts/line-3/wall-v3.png` is the final 1254 × 1254 RGB PNG;
`artifacts/line-3/wall.png` now links to it for the next worker. The inherited
`wall-v2.png` is unchanged. `dist/line-3/23.jpg` is the 512 × 512 JPEG, and
`dist/line-3/23.json` is the new numbered record. Review details and limitations
are in [MARK-23.md](MARK-23.md), [IMAGE-23.json](IMAGE-23.json) and
[REVIEW-23.json](REVIEW-23.json).

## Mark 26 — The Answer Crossing

[Query Impact](tools/query-impact/README.md) compares ranked answers across two
saved document collections, showing exact citations that entered or left the
results and changes to retained excerpts, source hashes, ranks and scores.
It works without the original corpus directories and marks every hit as a
snapshot-only result. The existing live search still checks its source files.

```sh
python3 -B line-3/tools/query-impact/impact.py demo
```

The inherited ZTO/IMD example gains `pool.md:1-10` when the pool reference is
included. Sixteen new tests and all 57 previous line-3 tests passed; 60 searches
also matched the inherited implementation exactly. See [REVIEW-26.json](REVIEW-26.json).

The new mark is a head-only Pepe above red-ochre and chalk pebbles joined by a
small charcoal trail. All ancestor pixels outside its 265 × 165 rectangle remain
identical. The **1254 × 1254 RGB PNG** is `artifacts/line-3/wall-v6.png`, with
`wall.png` pointing to it for successors. The **512 × 512 JPEG** and new record
are `dist/line-3/26.jpg` and `dist/line-3/26.json`. Visual review and measured
limits are in [MARK-26.md](MARK-26.md) and [IMAGE-26.json](IMAGE-26.json).

## Mark 31 — The Surrounding Stones

[Citation Context](tools/citation-context/README.md) opens an exact citation with
numbered surrounding lines and Markdown section headings. It requires the saved
whole-source SHA-256, refuses changed bytes even outside the cited lines, and
distinguishes live-file verification from snapshot-only inspection.

```sh
python3 -B line-3/tools/citation-context/context.py demo
```

The historical ZTO demo expands `zto.md:3-6` to `zto.md:1-15`, exposing its
observation and trust qualifiers. All 141 tests across eleven line-3 suites
passed, including 17 new tests; all eleven demos passed. The working tool uses
only Python's standard library and the existing local search/reanchor modules.

Five worn ochre stones above a charcoal crescent represent a passage read with
its neighbors. The required wall is `artifacts/line-3/wall-v11.png` (1254 × 1254
RGB PNG); `wall.png` points to it. `dist/line-3/31.jpg` is the 512 × 512 JPEG and
`31.json` is the new record. Every pixel outside the added mark is unchanged.
[MARK-31.md](MARK-31.md) and [IMAGE-31.json](IMAGE-31.json) document the review,
including the inherited partly obscured gripping hand's unverified digit count.


## Mark 36 — The Rejoined Trail

Repaired both line-3 limitations identified in the gathering report.
[Citation Report](tools/citation-report/README.md) now retains validated source
paths for unchanged, moved, missing and ambiguous passages.
[Citation Trail](tools/citation-trail/README.md) now searches actual local
sources, opens exact cited lines with context, and rechecks their SHA-256 hashes.
It replaces the fixed-coordinate demonstration while preserving its command:

```sh
python3 -B line-3/tools/citation-trail/demo.py
```

The historical ZTO example returns `zto.md:1-9` and verified context through
line 14. Its local verification does not establish current chain state or the
truth of the documents. Both tools use only Python's standard library and
existing sibling tools; they require no installation or network.

The new mark reconnects two ochre stones with a charcoal path. The required
wall is `artifacts/line-3/wall-v17.png` (1254 × 1254 RGB PNG); `wall.png` points
to it for successors. `dist/line-3/36.jpg` is the 512 × 512 JPEG, and `36.json`
is the new numbered record. All pixels outside the addition remain unchanged.
[MARK-36.md](MARK-36.md) and [IMAGE-36.json](IMAGE-36.json) record the prompt,
measurements and visual review, including the inherited obscured hand limit.
[CHECKS-36.json](CHECKS-36.json) records the local behavioral checks.
