# Receipt Capsule

Hand another worker one JSON file containing an execution header, an Ethereum
account/storage witness, a reviewed field layout and its saved receipt. The
receiver rehashes the header, verifies the original proof and regenerates the
receipt before accepting it. Block hash, intended contract and layout digest
must arrive separately from a trusted source; the capsule cannot select them.

From the repository root, Python 3.9+ with standard library only:

```sh
python3 -B line-2/tools/receipt-capsule/capsule.py demo
```

When tried, the real historical ZTO/IMD PoolManager proof at Ethereum block
26212390 survived a JSON round trip and verified one slot and five fields,
including LP fee 12500. The compact capsule is 17,843 bytes. The demo's pins
are inherited RPC observations, not independently authenticated checkpoints.
This is historical evidence, not a current quote. Original public source:
https://ethereum-rpc.publicnode.com. No fresh chain observation was made.

Verify the included single-file example offline:

```sh
python3 -B line-2/tools/receipt-capsule/capsule.py verify \
  line-2/tools/receipt-capsule/historical-capsule.json \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc \
  --address 0x000000000004444c5dc75cb358380d2e3de08a90 \
  --layout-sha256 6d3bbc017f81f66d785f895fe1cffaa65c9ec4351f8043fb92b93e3ed331fd0a
```

To prepare a capsule from other inputs use `create HEADER WITNESS LAYOUT` with
the same three required flags. It prints capsule JSON to stdout only after
verification. Redirect it to a new workspace file, never onto an input file.
`verify CAPSULE` needs no separate evidence files. Obtain the intended layout
fingerprint by calling `layout_digest(reviewed_layout)` from this module after
reviewing its names, offsets, sizes, signedness and unused-bit requirements.
The digest is SHA-256 of the normalized `storage-fields/1` layout serialized
with sorted keys, ASCII escapes and compact separators; field and slot order
normalize as in Storage Fields. It is identical to the receipt's layout hash.
Copying a digest from an untrusted capsule does not constitute layout review.

Format `receipt-capsule/1` has exactly `format`, `header`, `witness`, `layout`
and `receipt`. These embed the unchanged sibling tools' input formats. Unknown
top-level keys fail, including attempted embedded trust anchors. Witness labels
remain untrusted metadata; the header hash and actual trie proofs bind the
state. Receipt Audit ignores only the receipt producer's optional text `demo`
annotation. There is no archive extraction, path reference or network fetch.

Capsules are bounded to 1,200,000 bytes. Components are bounded to 64 KiB each
for header, layout and receipt, and 1,000,000 bytes for witness, with inherited
proof/layout bounds. Duplicate JSON keys, non-finite constants, paths escaping
the working directory and symlinks resolving outside it fail. Exit 0 prints
the verified result (or a verified capsule for `create`); invalid evidence exits
1 with error JSON on stderr and no success stdout. Argument errors exit 2.

Eighteen tests passed, covering real evidence, detached inputs, layout ordering,
external pins, a malicious replacement layout plus freshly generated receipt,
rehashed receipt tampering, proof corruption, header substitution, JSON types,
metadata isolation, schema/size limits, path confinement and CLI loading:

```sh
python3 -B -m unittest discover -s line-2/tools/receipt-capsule -v
```

Carry the sibling `receipt-audit/`, `proof-receipt/`, `storage-fields/`,
`header-anchor/` and `state-witness/` folders with this tool. Only the demo and
tests need their historical fixtures; verification of a received capsule needs
the Python sources. No installed dependencies, wallet, key, environment access,
signature, transaction, payment or posting. Unlike Proof Pack this does not
compress trie nodes; it closes the handoff between the header and receipt
verifiers in a single evidence document with externally pinned layout meaning.
Authenticate chain identity, canonicality, consensus, finality and freshness
separately. A layout fingerprint binds a reviewed interpretation, not the truth
of that interpretation.
