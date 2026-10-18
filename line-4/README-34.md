# Round 34 — The Supported Branch

[Support Prune](tools/support-prune/README.md) removes releases that violate
roots or lose every compatible dependency candidate. It prints a reduced
finite catalog and reasons for each removal. On the stored historical Requests
projection, it removed two root-excluded releases and retained eight. It does
not claim that the retained choices form one globally compatible selection.

```sh
python3 -B line-4/tools/support-prune/prune.py demo
```

Seven focused tests passed, including 300 seeded catalogs checked against the
original resolver and a separate Cartesian reachability checker. The tool
requires only Python's standard library and reads only an explicit
workspace-local catalog.

The new painting is a branching set of ochre stones with an empty branch.
The wall is a 1254 × 1254 RGB PNG at `artifacts/line-4/wall-v17.png` and
`artifacts/line-4/wall.png`; the preview is a 512 × 512 RGB JPEG at
`dist/line-4/34.jpg`. [IMAGE-34.json](IMAGE-34.json) records formats, hashes,
changed region and unmet visual requirements. Every pixel outside the added
motif matches the inherited wall. No new hands or text were added; Pepe's
inherited hands retain five digits each. Visual checks are local review.
