#!/usr/bin/env python3
"""Turn a citation-ledger check into a compact review queue."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ledger", HERE / "citation-ledger" / "ledger.py")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


def review(root, saved):
    """Keep each source attached to its validated ledger ID, in every status."""
    saved = ledger.validate(saved)
    checked = ledger.check_live(Path(root), saved)
    sources = {entry["id"]: entry["anchor"]["path"] for entry in saved["entries"]}
    rows = []
    for item in checked["entries"]:
        result = item["result"]
        rows.append({"id": item["id"], "status": result["status"],
                     "needs_review": item["needs_review"],
                     "source": sources[item["id"]]})
    return {"format": "citation-review/v1", "all_unchanged": checked["all_unchanged"],
            "entry_count": len(rows), "review_count": sum(r["needs_review"] for r in rows),
            "entries": rows}


def report(root, ledger_path):
    return review(root, ledger.load(Path(ledger_path)))


def demo():
    root = HERE / "evidence-search" / "examples" / "docs"
    sample = {"format": ledger.FORMAT, "entries": [
        {"id": "zto", "anchor": ledger.anchor.capture(root, "zto.md", 3, 6)},
        {"id": "pool", "anchor": ledger.anchor.capture(root, "pool.md", 1, 10)},
    ]}
    return review(root, sample)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?")
    parser.add_argument("ledger", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.root == "demo" and args.ledger is None:
            result = demo()
        elif args.root and args.ledger:
            result = report(args.root, args.ledger)
        else:
            parser.error("provide ROOT LEDGER, or use demo")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ledger.engine.SearchError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
