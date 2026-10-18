#!/usr/bin/env python3
"""Carry receipt evidence in one JSON document; verify against external pins."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent


def sibling(name, relative):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = sibling('capsule_audit', 'receipt-audit/audit.py')
anchor = sibling('capsule_anchor', 'header-anchor/anchor.py')
w = audit.w
INVALID = (w.Invalid, anchor.w.Invalid)
MAX_CAPSULE = 1_200_000
KEYS = {'format', 'header', 'witness', 'layout', 'receipt'}


def layout_digest(layout):
    normalized = audit.source.storage.validate_layout(layout)
    return hashlib.sha256(audit.canonical(normalized)).hexdigest()


def load_capsule(path):
    with w.workspace_path(path).open('rb') as stream:
        raw = stream.read(MAX_CAPSULE + 1)
    w.require(len(raw) <= MAX_CAPSULE, 'capsule exceeds 1.2 MB')
    return w.parse_json(raw)


def verify(capsule, block_hash, address, expected_layout_sha256):
    """No trust anchor or intended layout is selected from capsule contents."""
    w.require(isinstance(capsule, dict) and set(capsule) == KEYS,
              'capsule has missing or unknown fields')
    w.require(capsule['format'] == 'receipt-capsule/1', 'unsupported capsule format')
    w.require(len(audit.canonical(capsule)) <= MAX_CAPSULE, 'capsule exceeds 1.2 MB')
    for name, limit in (('header', 65536), ('layout', 65536),
                        ('receipt', 65536), ('witness', w.MAX_FILE)):
        w.require(len(audit.canonical(capsule[name])) <= limit,
                  name + ' exceeds component limit')
    w.require(isinstance(expected_layout_sha256, str) and
              re.fullmatch('[0-9a-f]{64}', expected_layout_sha256) is not None,
              'external layout digest must be 64 lowercase hex digits')
    digest = layout_digest(capsule['layout'])
    w.require(digest == expected_layout_sha256, 'layout differs from external digest')
    checked_header = anchor.verify_header(capsule['header'], block_hash)
    checked = audit.audit(capsule['receipt'], capsule['witness'],
                          checked_header['stateRoot'], address, capsule['layout'])
    return {
        'format': 'receipt-capsule-result/1', 'verified': True,
        'anchor': checked_header, 'audit': checked,
        'layoutPinned': True,
        'trust': 'Header, receipt and proof match the externally supplied block hash, address and layout digest. Authenticate those pins independently. Consensus, chain identity, finality, freshness and layout meaning are not verified.',
    }


def create(header, witness, layout, block_hash, address, expected_layout_sha256):
    checked_header = anchor.verify_header(header, block_hash)
    receipt = audit.source.make_receipt(witness, checked_header['stateRoot'], address, layout)
    capsule = {'format': 'receipt-capsule/1', 'header': header,
               'witness': witness, 'layout': layout, 'receipt': receipt}
    verify(capsule, block_hash, address, expected_layout_sha256)
    # Detach all returned data from caller-owned mutable inputs.
    return w.parse_json(audit.canonical(capsule))


def historical_inputs():
    return (anchor.load_header(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json'),
            w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
            audit.source.storage.load_layout(HERE.parent / 'storage-fields/pool-layout.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='offline historical ZTO/IMD capsule round trip')
    check = sub.add_parser('verify')
    check.add_argument('capsule')
    build = sub.add_parser('create', help='print capsule JSON without writing files')
    build.add_argument('header')
    build.add_argument('witness')
    build.add_argument('layout')
    for command in (check, build):
        command.add_argument('--block-hash', required=True)
        command.add_argument('--address', required=True)
        command.add_argument('--layout-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            header, witness, layout = historical_inputs()
            digest = layout_digest(layout)
            capsule = create(header, witness, layout, anchor.DEMO_HASH, w.POOL_MANAGER, digest)
            result = verify(w.parse_json(audit.canonical(capsule)), anchor.DEMO_HASH,
                            w.POOL_MANAGER, digest)
            result['capsuleBytes'] = len(audit.canonical(capsule))
            result['demo'] = 'Real historical ZTO/IMD block 26212390. Pins are inherited RPC observations, not independently authenticated checkpoints. No current-state claim.'
        elif args.command == 'verify':
            result = verify(load_capsule(args.capsule), args.block_hash,
                            args.address, args.layout_sha256)
        else:
            result = create(anchor.load_header(args.header), w.load_bundle(args.witness),
                            audit.source.storage.load_layout(args.layout), args.block_hash,
                            args.address, args.layout_sha256)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except INVALID as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
    except (OSError, ValueError, TypeError, KeyError, RecursionError, OverflowError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed capsule input.'}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
