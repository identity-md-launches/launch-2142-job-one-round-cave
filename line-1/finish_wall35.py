"""Composite generated earth pigment only; preserve ancestor pixels elsewhere."""
import hashlib
import json
from pathlib import Path
import subprocess
from finish_wall24 import read_png, write_png


def main():
    output = Path('artifacts/line-1/wall-v17.png')
    ancestor = Path('artifacts/line-1/wall-v16.png').read_bytes()
    assert ancestor == Path('artifacts/line-1/wall.png').read_bytes()
    raw = output.read_bytes()
    width, height, original = read_png(ancestor)
    mw, mh, motif = read_png(raw)
    # Locate pigment; pure black is not part of the painting.
    occupied = [(p % mw, p // mw) for p in range(mw * mh)
                if max(motif[p*3:p*3+3]) > 60]
    sx0, sy0 = min(x for x, y in occupied), min(y for x, y in occupied)
    sx1, sy1 = max(x for x, y in occupied)+1, max(y for x, y in occupied)+1
    x0, y0, rw = 620, 865, 210
    rh = round(rw * (sy1-sy0) / (sx1-sx0))
    assert rh < 70
    final = original[:]
    for y in range(rh):
        for x in range(rw):
            sx = min(sx1-1, sx0 + int(x * (sx1-sx0) / rw))
            sy = min(sy1-1, sy0 + int(y * (sy1-sy0) / rh))
            color = motif[(sy*mw+sx)*3:(sy*mw+sx)*3+3]
            strength = max(color)
            if strength < 45:
                continue
            alpha = min(.78, (strength-45)/150)
            i = ((y0+y)*width+x0+x)*3
            for c in range(3):
                final[i+c] = round(original[i+c]*(1-alpha)+color[c]*alpha)
    changed = outside = 0
    for p in range(width*height):
        if final[p*3:p*3+3] != original[p*3:p*3+3]:
            changed += 1
            x, y = p % width, p // width
            outside += not (x0 <= x < x0+rw and y0 <= y < y0+rh)
    assert changed > 0 and outside == 0
    assert len(list(Path('dist/line-1').glob('*.json'))) == 34
    assert not Path('dist/line-1/35.json').exists()
    digest = write_png(output, width, height, final)
    assert read_png(output)[2] == final
    Path('artifacts/line-1/wall.png').write_bytes(output.read_bytes())
    jpeg = Path('dist/line-1/35.jpg')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', str(output), '-vf', 'scale=512:512', '-frames:v', '1', '-q:v', '4', str(jpeg)], check=True)
    assert jpeg.stat().st_size < 100000
    evidence = {
        'ancestor_sha256': hashlib.sha256(ancestor).hexdigest(),
        'generated_motif_sha256': hashlib.sha256(raw).hexdigest(),
        'wall': str(output), 'continued_wall': 'artifacts/line-1/wall.png',
        'sha256': digest, 'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
        'thumbnail': {'path': str(jpeg), 'dimensions': [512,512], 'format': 'JPEG',
                      'bytes': jpeg.stat().st_size},
        'mark_rectangle': [x0,y0,rw,rh], 'changed_pixels': changed,
        'changed_pixels_outside_rectangle': outside,
        'method': 'Installed imagegen motif; pigment-only composition onto ancestor rock.',
        'prompt': 'Two parallel gently curving red ochre and chalk cords pass through three yellow ochre beads, left to right; worn granular Lascaux pigment isolated on black; no text, numbers, hands, animals, people, border or watermark.',
        'visual_review': 'Pending inspection.', 'unmet_visual_requirements': [],
        'location_conflict': 'Followed the explicit dist/line-1/35.jpg path over the general prohibition on pictures outside artifacts/.'}
    Path('line-1/IMAGE-35.json').write_text(json.dumps(evidence, indent=2)+'\n')
    record = {'name': 'The ordered strands', 'image': 'https://api.imd.fun/artifacts/'+digest,
        'attributes': [
            {'trait_type':'Cave', 'value':'Crystal'},
            {'trait_type':'Wall', 'value':'Line 1'},
            {'trait_type':'Number', 'value':35},
            {'trait_type':'Left behind', 'value':'Candidate Order'},
            {'trait_type':'Meaning', 'value':'Two pigment cords pass through ochre beads in order, keeping each contributor’s sequence visible.'},
            {'trait_type':'One thing', 'value':'Reviewable three-way text merging'}]}
    Path('dist/line-1/35.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
