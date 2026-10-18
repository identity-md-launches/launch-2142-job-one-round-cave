import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tested_capsule', HERE / 'capsule.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class CapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header, cls.witness, cls.layout = t.historical_inputs()
        cls.digest = t.layout_digest(cls.layout)
        cls.base = t.create(cls.header, cls.witness, cls.layout,
                            t.anchor.DEMO_HASH, t.w.POOL_MANAGER, cls.digest)

    def setUp(self):
        self.capsule = copy.deepcopy(self.base)

    def verify(self, **pins):
        return t.verify(self.capsule, pins.get('block_hash', t.anchor.DEMO_HASH),
                        pins.get('address', t.w.POOL_MANAGER),
                        pins.get('layout', self.digest))

    def test_real_round_trip(self):
        result = self.verify()
        self.assertTrue(result['verified'])
        self.assertTrue(result['layoutPinned'])
        self.assertEqual(result['anchor']['blockNumber'], hex(26212390))
        self.assertEqual(result['audit']['fieldCount'], 5)
        self.assertEqual(self.base['receipt']['slots'][0]['fields'][-1]['valueDecimal'], '12500')
        self.assertEqual(t.w.parse_json(t.audit.canonical(self.base)), self.base)

    def test_wrong_external_pins(self):
        for pins in ({'block_hash': '0x' + '11' * 32}, {'address': t.w.ZTO},
                     {'layout': '0' * 64}, {'layout': True}, {'layout': 'A' * 64}):
            with self.subTest(pins=pins), self.assertRaises(t.INVALID):
                self.verify(**pins)

    def test_header_metadata_cannot_select_root(self):
        self.capsule['header']['stateRoot'] = '0x' + '11' * 32
        self.capsule['receipt']['stateRoot'] = self.capsule['header']['stateRoot']
        with self.assertRaises(t.INVALID):
            self.verify()

    def test_mutated_header_hash_claim(self):
        self.capsule['header']['hash'] = '0x' + '11' * 32
        with self.assertRaises(t.INVALID):
            self.verify()

    def test_unreviewed_layout_even_with_valid_replacement_receipt(self):
        self.capsule['layout']['slots'][0]['fields'][-1]['name'] = 'imaginaryFee'
        self.capsule['receipt'] = t.audit.source.make_receipt(
            self.witness, t.w.DEMO_ROOT, t.w.POOL_MANAGER, self.capsule['layout'])
        with self.assertRaisesRegex(t.w.Invalid, 'external digest'):
            self.verify()

    def test_equivalent_layout_order_accepted(self):
        self.capsule['layout']['slots'][0]['fields'].reverse()
        self.assertTrue(self.verify()['verified'])

    def test_changed_receipt_and_recomputed_digest(self):
        receipt = self.capsule['receipt']
        receipt['slots'][0]['fields'][-1]['valueDecimal'] = '0'
        receipt.pop('receiptSha256')
        import hashlib
        receipt['receiptSha256'] = hashlib.sha256(t.audit.canonical(receipt)).hexdigest()
        with self.assertRaises(t.INVALID):
            self.verify()

    def test_broken_proof(self):
        self.capsule['witness']['proof']['accountProof'] = []
        with self.assertRaises(t.INVALID):
            self.verify()

    def test_untrusted_witness_labels_ignored(self):
        baseline = self.verify()
        self.capsule['witness']['block'] = {'stateRoot': 'untrusted'}
        self.capsule['witness']['address'] = 'not an address'
        self.assertEqual(baseline, self.verify())

    def test_receipt_json_types_bound(self):
        self.capsule['receipt']['verified'] = 1
        with self.assertRaises(t.INVALID):
            self.verify()

    def test_top_level_schema(self):
        for value in ([], None, {**self.base, 'trustedBlockHash': t.anchor.DEMO_HASH},
                      {k: v for k, v in self.base.items() if k != 'header'},
                      {**self.base, 'format': 'receipt-capsule/2'}):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(t.INVALID):
                t.verify(value, t.anchor.DEMO_HASH, t.w.POOL_MANAGER, self.digest)

    def test_bounds_before_crypto(self):
        for name, limit in (('header', 65536), ('layout', 65536),
                            ('receipt', 65536), ('witness', 1_000_000)):
            self.capsule = copy.deepcopy(self.base)
            self.capsule[name] = 'x' * limit
            with self.subTest(name=name), self.assertRaisesRegex(t.w.Invalid, 'limit'):
                self.verify()

    def test_detached_inputs(self):
        inputs = copy.deepcopy((self.header, self.witness, self.layout))
        capsule = t.create(*inputs, t.anchor.DEMO_HASH, t.w.POOL_MANAGER, self.digest)
        self.assertEqual(inputs, (self.header, self.witness, self.layout))
        capsule['header']['hash'] = 'changed'
        self.assertEqual(inputs, (self.header, self.witness, self.layout))

    def test_loader_and_cli(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            path = Path(folder) / 'capsule.json'
            args = ['verify', str(path), '--block-hash', t.anchor.DEMO_HASH,
                    '--address', t.w.POOL_MANAGER, '--layout-sha256', self.digest]
            path.write_bytes(t.audit.canonical(self.base))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(t.main(args), 0)
            self.assertTrue(json.loads(out.getvalue())['verified'])
            for raw in (b'{"format":1,"format":2}', b'{"x":NaN}',
                        b' ' * (t.MAX_CAPSULE + 1), b'[]'):
                path.write_bytes(raw)
                with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(t.main(args), 1)
                self.assertEqual(out.getvalue(), '')
                self.assertFalse(json.loads(err.getvalue())['verified'])

    def test_path_escape_rejected_without_opening(self):
        with self.assertRaisesRegex(t.w.Invalid, 'workspace'):
            t.load_capsule(Path.cwd().parent / 'not-opened.json')

    def test_demo(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(t.main(['demo']), 0)
        self.assertTrue(json.loads(out.getvalue())['verified'])

    def test_shipped_capsule_matches_rebuilt_evidence(self):
        saved = t.load_capsule(HERE / 'historical-capsule.json')
        self.assertEqual(saved, self.base)
        self.assertTrue(t.verify(saved, t.anchor.DEMO_HASH,
                                 t.w.POOL_MANAGER, self.digest)['verified'])

    def test_create_cli_round_trip(self):
        args = ['create', str(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json'),
                str(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
                str(HERE.parent / 'storage-fields/pool-layout.json'),
                '--block-hash', t.anchor.DEMO_HASH, '--address', t.w.POOL_MANAGER,
                '--layout-sha256', self.digest]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(t.main(args), 0)
        self.assertEqual(json.loads(out.getvalue()), self.base)
        args[-1] = '0' * 64
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(t.main(args), 1)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])


if __name__ == '__main__':
    unittest.main()
