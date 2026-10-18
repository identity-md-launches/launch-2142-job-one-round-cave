# Image production and review

Used the installed image generation tool under the imagegen skill. The exact
prompt for the single generated insert was:

> A small isolated prehistoric cave pigment motif on perfectly black background: two parallel gently curving cords, one red ochre above and one chalk white below, each passing through three small yellow ochre beads in sequence from left to right. Very wide low horizontal composition occupying middle half of canvas, much empty black space. Worn irregular dry thumb pigment, granular sparse edges, handmade Lascaux cave painting. Only earth pigments red yellow ochre and chalk. No text, letters, numbers, symbols, hands, animals, people, border, frame, watermark, realistic objects or 3D. This is an insert motif for an existing cave wall; black will be removed.

Requested one 1024-square image; the tool returned a wider insert. It was written
at the required wall-v17 path, inspected, then consumed and replaced with the
finished whole wall. No separate insert image is retained. finish_wall35.py
records the pigment-only composition, with the prior wall-v16 as the immutable
ancestor. The PNG codec and FFmpeg thumbnail conversion were used for image
processing, not as substitutes for generated painting.

Chosen review step: inspect both finished PNG and 512-pixel JPEG, count inherited
hand digits, check the new mark for writing/prohibited content, and compare every
pixel against the ancestor. The local review and quantitative results are in
IMAGE-35.json. No unmet visual requirement observed; the new motif is small and
subdued at thumbnail size. No independent visual approval is claimed.
