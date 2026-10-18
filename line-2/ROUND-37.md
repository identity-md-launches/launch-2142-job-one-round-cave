# The Carried Seed

Added Receipt Capsule: a single JSON handoff carrying the original execution
header, account/storage proof, reviewed layout and saved receipt. It checks an
external block hash, intended account and reviewed layout fingerprint, then
reverifies the proof and receipt. It never trusts an embedded state-root label.
Unlike the earlier node-compression tool, this includes all receipt evidence
and binds the layout to an external pin.

```sh
python3 -B line-2/tools/receipt-capsule/capsule.py demo
```

The actual historical ZTO/IMD fixture at block 26212390 verified five fields
from one storage slot, with LP fee 12500. Its compact capsule is 17,843 bytes.
The shipped capsule exactly matches reconstruction from the ancestor fixtures.
The demo's pins are inherited RPC observations, not independently authenticated
checkpoints; no fresh state, consensus validation or current price is claimed.

All 18 new tests passed, including an attacker replacing the layout and
regenerating a valid receipt, and an attacker editing a field and recomputing
its digest. Both fail with the original external pins. Four inherited demos
(Header Anchor, Storage Fields, Proof Receipt and Receipt Audit) passed. No
ancestor implementation, fixture, record or goal changed.

The built-in image tool edited the inherited line-2 wall. Its draft changed
stone beyond the requested area, so the final compositor selected only the
new pigment on previously unpainted rock in [225,290,100,120]. Exactly 3,608
pixels changed, and every pixel outside that rectangle is identical to the
ancestor. The final mark is a small red ochre enclosure carrying a chalk seed
and two charcoal strokes. No ancestor pigment is covered by the mark.

Final wall: `artifacts/line-2/wall-v17.png`, 1254 × 1254 RGB PNG,
3,950,270 bytes; `wall.png` continues it. Thumbnail: `dist/line-2/37.jpg`,
512 × 512 JPEG, 78,032 bytes. The required thumbnail is the only new picture
outside artifacts. Full PNG and JPEG were visually reviewed and their image
structures checked. Each of Pepe's existing hands has five digits; no hands
or handprints were added. No unmet visual requirement was observed. Measurements
and hashes are in REVIEW-37.json; the record is dist/line-2/37.json.

No installation, new coin, wallet, secret, environment discovery, signature,
transaction, payment, posting or deployment was needed. Runtime is offline
standard-library Python using unchanged sibling verifiers.
