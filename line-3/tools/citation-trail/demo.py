#!/usr/bin/env python3
"""Search local documents and follow each ranked hit to verified source lines."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

# Running the documented command must not write caches into ancestor tools.
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location(
    "trail_context", Path(__file__).absolute().parents[1] / "citation-context/context.py")
context = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(context)
engine = context.engine

FORMAT = "citation-trail/v1"
MAX_REPORT_BYTES = 1_000_000


def follow(root, query, *, index=None, limit=5, require_all=True, before=2, after=5):
    """Return a complete trail only after every cited file has been rechecked.

    An optional Evidence Search index pins the source version. With no index,
    the tool builds an in-memory snapshot of the selected local corpus.
    """
    root = engine.workspace_path(root)
    context.validate_margins(before, after)
    if type(limit) is not int or not 1 <= limit <= 50:
        raise engine.SearchError("limit must be an integer from 1 to 50")
    if type(require_all) is not bool:
        raise engine.SearchError("require_all must be boolean")
    built_now = index is None
    if built_now:
        index = engine.build_index(root)
    results = engine.search(index, query, root, limit=limit, require_all=require_all)
    entries = []
    for rank, hit in enumerate(results["hits"], 1):
        anchor = {"format": context.anchor_tool.FORMAT,
                  **{key: hit[key] for key in
                     ("path", "line_start", "line_end", "sha256", "text")}}
        # inspect_live checks the exact excerpt as well as the whole-file hash.
        opened = context.inspect_live(root, anchor, before=before, after=after)
        entries.append({
            "rank": rank, "score": hit["score"],
            "matched_terms": hit["matched_terms"], "citation": hit["citation"],
            "anchor": anchor, "source_verified": opened["source_verified"],
            "saved_text_checked": opened["selection"]["saved_text_checked"],
            "context": opened["context"], "section_headings": opened["section_headings"],
        })
    # Recheck early entries after later contexts have been opened. This catches
    # ordinary concurrent edits; it is not an atomic filesystem snapshot.
    checked = set()
    for entry in entries:
        anchor = entry["anchor"]
        if anchor["path"] in checked:
            continue
        raw = context.anchor_tool.read_source(root, anchor["path"])
        if engine.digest(raw) != anchor["sha256"]:
            raise engine.SearchError("source changed during trail; retry with static files")
        checked.add(anchor["path"])
    report = {
        "format": FORMAT, "query": query, "terms": results["terms"],
        "corpus_root": root.relative_to(Path.cwd()).as_posix(),
        "index_mode": "built_in_memory" if built_now else "supplied_snapshot",
        "require_all": require_all, "indexed_documents": results["indexed_documents"],
        "indexed_passages": results["indexed_passages"], "hit_count": len(entries),
        "verified_source_count": len(checked),
        "verification_scope": "exact local source bytes and selected lines; not factual accuracy or current chain state",
        "entries": entries,
    }
    if len(json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")) > MAX_REPORT_BYTES:
        raise engine.SearchError("trail exceeds output byte limit; request fewer hits or context lines")
    return report


def demo(query="ZTO token decimals"):
    root = Path(__file__).absolute().parents[1] / "evidence-search/examples/docs"
    report = follow(root, query)
    report["example"] = "Historical ZTO-first documents; no network request or current chain claim."
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    sample = commands.add_parser("demo", help="read the bundled historical ZTO documents")
    sample.add_argument("query", nargs="?", default="ZTO token decimals")
    query = commands.add_parser("query", help="search a workspace corpus and verify each cited passage")
    query.add_argument("root")
    query.add_argument("query")
    query.add_argument("--index", help="optional saved Evidence Search index; stale citations fail")
    query.add_argument("--limit", type=int, default=5)
    query.add_argument("--any", action="store_true", help="allow partial query-term matches")
    query.add_argument("--before", type=int, default=2)
    query.add_argument("--after", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        if args.command in (None, "demo"):
            result = demo(getattr(args, "query", "ZTO token decimals"))
        else:
            result = follow(args.root, args.query,
                            index=engine.load_index(args.index) if args.index else None,
                            limit=args.limit, require_all=not args.any,
                            before=args.before, after=args.after)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["entries"] else 1
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
