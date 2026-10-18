"""Order regressions and bounded filesystem integration; stdlib only."""
from collections import Counter
import contextlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('candidate_order_test',
    Path(__file__).with_name('candidate_order.py'))
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
REAL_README = (Path(__file__).resolve().parents[1] / 'threeway' / 'README.md').read_text()


class OrderTests(unittest.TestCase):
    def check(self, base, branch, candidate):
        return audit.branch_order(base, branch, candidate)

    def test_reversed_steps_with_identical_counts(self):
        branch, candidate = 'prepare\ninspect\n', 'inspect\nprepare\n'
        self.assertEqual(Counter(branch.splitlines()), Counter(candidate.splitlines()))
        row = self.check('', branch, candidate)
        self.assertEqual(row['issue'], 'order_changed')
        self.assertEqual(row['first_unmatched']['branch_line'], 2)

    def test_interleaved_unrelated_lines(self):
        self.assertEqual(self.check('', 'a\nb\n', 'x\na\ny\nb\nz\n')['status'], 'checked')

    def test_duplicate_order(self):
        self.assertEqual(self.check('a\n', 'a\nb\na\n', 'a\na\nb\n')['issue'], 'order_changed')
        self.assertEqual(self.check('a\n', 'a\nb\na\n', 'a\nb\na\n')['status'], 'checked')

    def test_missing_occurrences_distinct_from_order(self):
        row = self.check('', 'a\nb\na\n', 'a\nb\n')
        self.assertEqual(row['issue'], 'missing_occurrences')
        self.assertEqual(row['missing_occurrences'], 1)

    def test_no_growth_and_empty_presence_out_of_scope(self):
        for base, branch, candidate in [('a\nb\n', 'b\na\n', 'a\nb\n'),
                                         (None, '', None), ('x\n', None, None)]:
            self.assertEqual(self.check(base, branch, candidate)['status'], 'checked')

    def test_exact_unicode_and_newlines(self):
        for line in ('é\r\n', 'é\n', 'é', '\n'):
            self.assertEqual(self.check('', line, line)['status'], 'checked')
        self.assertEqual(self.check('', 'é\r\n', 'é\n')['issue'], 'missing_occurrences')

    def test_greedy_subsequence_matches_exhaustive_oracle(self):
        # All tiny repeated sequences: compare against explicit index combinations.
        words = [''.join(x) for n in range(4) for x in itertools.product('ab', repeat=n)]
        for branch in words:
            for candidate in words:
                expected = any(''.join(candidate[i] for i in indexes) == branch
                               for indexes in itertools.combinations(range(len(candidate)), len(branch)))
                row = self.check('', ''.join(x+'\n' for x in branch),
                                 ''.join(x+'\n' for x in candidate))
                self.assertEqual(row['status'] == 'checked', expected)

    def test_independent_branch_order_and_shared_occurrences(self):
        def report(ours, theirs, candidate):
            return audit.inspect([{'files': {'x': s}, 'directories': set()}
                                  for s in ('', ours, theirs, candidate)])
        self.assertFalse(report('a\nb\n', 'c\nd\n', 'c\na\nd\nb\n')['needs_review'])
        self.assertFalse(report('a\nb\n', 'a\nb\n', 'a\nb\n')['needs_review'])
        self.assertTrue(report('a\nb\n', 'b\na\n', 'a\nb\n')['needs_review'])

    def test_collision_blocks_descendants(self):
        report = audit.inspect([{'files': f, 'directories': d} for f, d in
            [({'x': ''}, set()), ({'x/y': 'a'}, {'x'}), ({}, set()), ({}, set())]])
        self.assertEqual(report['counts']['blocked'], 2)

    def test_reports_omit_source_text_and_are_deterministic(self):
        sources = [{'files': {'x': s}, 'directories': set()}
                   for s in ('', 'hidden distinctive source\n', '', '')]
        report = audit.inspect(sources)
        self.assertNotIn('hidden distinctive source', json.dumps(report))
        self.assertEqual(report, audit.inspect(sources))

    def test_real_document_readonly_and_manifest_change(self):
        # A temporary current workspace lets the bounded reader operate under /tmp.
        with tempfile.TemporaryDirectory(prefix='candidate-order-', dir='/tmp') as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                paths = [Path(side) for side in audit.SIDES]
                ours = REAL_README + '\nPrepare a review packet.\nInspect that packet.\n'
                theirs = REAL_README + '\nKeep both contributor receipts.\n'
                candidate = ours + '\nKeep both contributor receipts.\n'
                for path, text in zip(paths, (REAL_README, ours, theirs, candidate)):
                    path.mkdir()
                    (path / 'README.md').write_text(text)
                before = [(path / 'README.md').read_bytes() for path in paths]
                report = audit.from_directories(paths)
                self.assertFalse(report['needs_review'])
                self.assertEqual(before, [(path / 'README.md').read_bytes() for path in paths])
                (paths[3] / 'README.md').write_text(candidate.replace(
                    'Prepare a review packet.\nInspect that packet.\n',
                    'Inspect that packet.\nPrepare a review packet.\n'))
                changed = audit.from_directories(paths)
                self.assertTrue(changed['needs_review'])
                self.assertEqual(changed['files'][0]['branches']['ours']['issue'], 'order_changed')
                self.assertNotEqual(report['inputs']['candidate'], changed['inputs']['candidate'])
                self.assertEqual(before[:3], [(path / 'README.md').read_bytes() for path in paths[:3]])
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(audit.main(list(map(str, paths))), 1)
            finally:
                os.chdir(previous)

    def test_invalid_files_fail_without_partial_report(self):
        with tempfile.TemporaryDirectory(prefix='candidate-order-', dir='/tmp') as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                root = Path('tree')
                root.mkdir()
                bad = root / 'bad'
                for data in (b'\x00', b'\xff', b'x\n' * 4001):
                    bad.write_bytes(data)
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        self.assertEqual(audit.main(['tree'] * 4), 2)
                    self.assertEqual(out.getvalue(), '')
                bad.unlink()
                bad.symlink_to('absent')
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    audit.from_directories(['tree'] * 4)
            finally:
                os.chdir(previous)

    def test_demo_and_argument_counts(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(['--demo']), 0)
        for function in (audit.inspect, audit.from_directories):
            with self.assertRaises(ValueError):
                function([])


if __name__ == '__main__':
    unittest.main()
