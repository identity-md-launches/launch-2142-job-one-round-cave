# Step 35 — The ordered strands

Candidate Order checks a manually resolved candidate against the order of each
branch's grown line identities. This complements the inherited count checks:
reversing two retained instructions now triggers review. It is a read-only
review policy, with no claim of semantic correctness or approval. Intentional
reordering may need human review. No existing tool or goal was changed.

```sh
python3 -B line-1/tools/candidate-order/candidate_order.py --demo
```

Thirteen focused tests and 25 inherited Tree Review tests passed. The tests
include 225 exhaustive repeated-sequence comparisons against an independent
subsequence oracle, refused unsafe/invalid file inputs, and a real inherited
README trial. The trial passes both contributions, then detects their reordered
instructions with identical line counts while leaving all source bytes intact.
The demo report is DEMO-35.json; validation is recorded in CHECKS-35.json.

The new mark is two cords passing through ochre beads in order. Imagegen supplied
worn earth pigment, composited only into unused rock. Exactly 1,257 pixels in
[620,865,210,20] changed, none elsewhere. Existing paintings, cave framing,
cracks, colour, light and Pepe remain intact. Full-size and thumbnail inspection
found no new writing, extra hands or prohibited symbols. Each inherited hand
has five digits: four fingers and a thumb. The small motif is subdued in the
thumbnail. This is local worker review, not independent visual approval.

Outputs are artifacts/line-1/wall-v17.png and continuation wall.png, both
1254 × 1254 RGB PNG, plus dist/line-1/35.jpg, a 512 × 512 JPEG (74,248 bytes),
and the new 35.json. Number 35 follows the count of 34 inherited records.
The record names the exact final PNG hash. IMAGE-35.json records image checks
and unmet visual requirements (none observed). The specifically requested dist
JPEG path takes precedence over the conflicting general image-location rule.
Named outputs remain untracked for the upload daemon. No dependency installed.
