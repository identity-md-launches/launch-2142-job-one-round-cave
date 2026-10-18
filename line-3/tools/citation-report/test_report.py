"""Source-path regression checks using real ledger and reanchor validation."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("citation_report", Path(__file__).with_name("report.py"))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        Path("test/scratch").mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir="test/scratch")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        self.sources = {"docs/zto.md": b"intro\nZTO\n18 decimals\nend\n",
                        "pool.txt": b"pool\nIMD\n"}
        for name, raw in self.sources.items():
            (self.root / name).write_bytes(raw)
        self.saved = {"format": report.ledger.FORMAT, "entries": [
            {"id": "token", "anchor": report.ledger.anchor.capture_bytes(
                self.sources["docs/zto.md"], "docs/zto.md", 2, 3)},
            {"id": "pool", "anchor": report.ledger.anchor.capture_bytes(
                self.sources["pool.txt"], "pool.txt", 1, 1)},
        ]}
        self.path = self.root / "ledger.json"
        self.path.write_text(json.dumps(self.saved), encoding="utf-8")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", report.__file__, *map(str, args)],
                              capture_output=True, text=True)

    def test_sources_survive_every_matching_status(self):
        variants = [
            (self.sources["docs/zto.md"], "unchanged"),
            (b"intro\nZTO\n18 decimals\nchanged\n", "same_lines_changed_source"),
            (b"new heading\n" + self.sources["docs/zto.md"], "relocated"),
            (b"ZTO\n18 decimals\n" * 2, "ambiguous"),
            (b"the quoted passage was removed\n", "missing"),
        ]
        for raw, status in variants:
            with self.subTest(status=status):
                (self.root / "docs/zto.md").write_bytes(raw)
                result = report.report(self.root, self.path)
                self.assertEqual(result["entries"], [
                    {"id": "token", "status": status, "needs_review": status != "unchanged",
                     "source": "docs/zto.md"},
                    {"id": "pool", "status": "unchanged", "needs_review": False,
                     "source": "pool.txt"},
                ])
                self.assertEqual(result["entry_count"], 2)
                self.assertEqual(result["review_count"], int(status != "unchanged"))
                self.assertEqual(result["all_unchanged"], status == "unchanged")

    def test_sources_join_by_id_when_checked_order_changes(self):
        check_live = report.ledger.check_live
        def reversed_check(root, saved):
            result = check_live(root, saved)
            result["entries"].reverse()
            return result
        with patch.object(report.ledger, "check_live", side_effect=reversed_check):
            result = report.report(self.root, self.path)
        self.assertEqual([(row["id"], row["source"]) for row in result["entries"]],
                         [("pool", "pool.txt"), ("token", "docs/zto.md")])

    def test_same_source_can_have_multiple_ids(self):
        saved = copy.deepcopy(self.saved)
        saved["entries"][1]["anchor"] = saved["entries"][0]["anchor"]
        result = report.review(self.root, saved)
        self.assertEqual([row["source"] for row in result["entries"]],
                         ["docs/zto.md", "docs/zto.md"])
        self.assertEqual([row["id"] for row in result["entries"]], ["token", "pool"])

    def test_invalid_or_duplicate_ids_and_unsafe_paths_are_refused(self):
        cases = []
        duplicate = copy.deepcopy(self.saved)
        duplicate["entries"][1]["id"] = "token"
        cases.append(duplicate)
        invalid_id = copy.deepcopy(self.saved)
        invalid_id["entries"][0]["id"] = "not an id"
        cases.append(invalid_id)
        unsafe = copy.deepcopy(self.saved)
        unsafe["entries"][0]["anchor"]["path"] = "../escape.md"
        cases.append(unsafe)
        forged = copy.deepcopy(self.saved)
        forged["entries"][0]["anchor"]["text"] = "invented\npassage"
        cases.append(forged)
        for saved in cases:
            with self.subTest(saved=saved):
                self.path.write_text(json.dumps(saved), encoding="utf-8")
                with self.assertRaises(report.ledger.engine.SearchError):
                    report.report(self.root, self.path)

    def test_missing_file_refuses_entire_report(self):
        (self.root / "pool.txt").unlink()
        with self.assertRaises(report.ledger.engine.SearchError):
            report.report(self.root, self.path)
        result = self.run_cli(self.root, self.path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("error", json.loads(result.stderr))

    def test_sources_and_saved_ledger_are_not_rewritten(self):
        before = copy.deepcopy(self.saved)
        saved_bytes = self.path.read_bytes()
        report.review(self.root, self.saved)
        report.report(self.root, self.path)
        self.assertEqual(self.saved, before)
        self.assertEqual(self.path.read_bytes(), saved_bytes)
        for name, raw in self.sources.items():
            self.assertEqual((self.root / name).read_bytes(), raw)

    def test_cli_preserves_success_exit_for_changed_review(self):
        (self.root / "docs/zto.md").write_bytes(b"new heading\n" + self.sources["docs/zto.md"])
        result = self.run_cli(self.root, self.path)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["entries"][0]["source"], "docs/zto.md")
        self.assertEqual(value["entries"][0]["status"], "relocated")
        self.assertEqual(value["review_count"], 1)

    def test_malformed_json_refuses_without_partial_output(self):
        for raw in [b'{"format":1,"format":2}', b'{"value":NaN}', b'\xff', b'[]']:
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                result = self.run_cli(self.root, self.path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error", json.loads(result.stderr))

    def test_demo_reports_historical_source_paths(self):
        result = report.demo()
        self.assertEqual(result["format"], "citation-review/v1")
        self.assertEqual([(row["id"], row["source"]) for row in result["entries"]],
                         [("zto", "zto.md"), ("pool", "pool.md")])
        self.assertTrue(result["all_unchanged"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["review_count"], 0)
        command = self.run_cli("demo")
        self.assertEqual(command.returncode, 0, command.stderr)
        self.assertEqual(json.loads(command.stdout), result)


if __name__ == "__main__":
    unittest.main()
