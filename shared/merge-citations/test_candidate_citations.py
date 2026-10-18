"""Checks for applied-candidate addition and citation review."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import candidate_citations as tool


class CandidateCitationTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root / side for side in ('base', 'ours', 'theirs', 'candidate')]
        for path in self.paths:
            path.mkdir()
        self.base = (Path('shared/merge-citations/examples/zto.md')).read_bytes()
        for path in self.paths:
            (path / 'zto.md').write_bytes(self.base)
        (self.paths[1] / 'note.md').write_text('Keep source lines.\n')
        (self.paths[2] / 'other.md').write_text('Review both edits.\n')
        (self.paths[3] / 'note.md').write_text('Keep source lines.\n')
        (self.paths[3] / 'other.md').write_text('Review both edits.\n')
        saved = {'format': tool.ledger.FORMAT, 'entries': [{
            'id': 'zto', 'anchor': tool.ledger.anchor.capture_bytes(self.base, 'zto.md', 3, 6)}]}
        self.ledger_path = self.root / 'ledger.json'
        self.ledger_path.write_text(json.dumps(saved))

    def run_check(self):
        return tool.check(*self.paths, self.ledger_path)

    def test_complete_historical_candidate(self):
        result = self.run_check()
        self.assertEqual(result['status'], 'ready-for-review')
        self.assertEqual(result['citations']['entries'][0]['source'], 'zto.md')
        self.assertTrue(result['source_verified'])
        self.assertTrue(result['inputs_rechecked'])
        self.assertEqual(result['candidate_additions']['counts']['review'], 0)

    def test_omission_and_relocated_citation_are_distinct(self):
        (self.paths[3] / 'other.md').unlink()
        result = self.run_check()
        self.assertEqual(result['status'], 'review')
        self.assertEqual(result['candidate_additions']['counts']['review'], 1)
        self.assertEqual(result['citations']['review_count'], 0)
        (self.paths[3] / 'other.md').write_text('Review both edits.\n')
        (self.paths[3] / 'zto.md').write_bytes(b'# Reading copy\n' + self.base)
        result = self.run_check()
        self.assertEqual(result['candidate_additions']['counts']['review'], 0)
        self.assertEqual(result['citations']['entries'][0]['status'], 'relocated')
        self.assertEqual(result['citations']['review_count'], 1)

    def test_deleted_cited_file_is_a_review_row(self):
        (self.paths[3] / 'zto.md').unlink()
        result = self.run_check()
        self.assertEqual(result['citations']['entries'][0]['status'], 'deleted')
        self.assertEqual(result['status'], 'review')

    def test_stale_base_anchor_rejected(self):
        (self.paths[0] / 'zto.md').write_bytes(b'changed\n')
        with self.assertRaises(tool.ledger.engine.SearchError):
            self.run_check()

    def test_cli_exits_and_demo(self):
        cmd = [sys.executable, '-B', tool.__file__, 'check',
               *map(str, self.paths), str(self.ledger_path)]
        ok = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)['status'], 'ready-for-review')
        (self.paths[3] / 'other.md').unlink()
        review = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(review.returncode, 1, review.stderr)
        self.assertEqual(json.loads(review.stdout)['status'], 'review')
        demo = subprocess.run([sys.executable, '-B', tool.__file__, 'demo'],
                              capture_output=True, text=True)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        sample = json.loads(demo.stdout)
        self.assertEqual(sample['complete']['status'], 'ready-for-review')
        self.assertEqual(sample['omitted_addition']['status'], 'review')
        self.assertEqual(sample['relocated_citation']['status'], 'review')

    def test_bundle_demo_without_line_folders(self):
        isolated = self.root / 'portable'
        shutil.copytree('shared/merge-citations', isolated)
        command = subprocess.run([sys.executable, '-B', str(isolated / 'candidate_citations.py'),
                                  'demo'], capture_output=True, text=True)
        self.assertEqual(command.returncode, 0, command.stderr)
        self.assertEqual(json.loads(command.stdout)['complete']['status'],
                         'ready-for-review')


if __name__ == '__main__':
    unittest.main()
