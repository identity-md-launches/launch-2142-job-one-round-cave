"""Transfer round 34's generated branch motif onto the inherited wall."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def load(module_name, filename):
    spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clamp(value):
    return max(0.0, min(1.0, value))


def segment_distance(x, y, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy))
    return math.hypot(x - ax - t * dx, y - ay - t * dy)


def alpha_at(x, y):
    pebbles = ((924, 573, 28, 26), (1018, 528, 23, 21),
               (1018, 573, 23, 21))
    alpha = 0.0
    for cx, cy, rx, ry in pebbles:
        radius = math.hypot((x - cx) / rx, (y - cy) / ry)
        alpha = max(alpha, clamp((1.20 - radius) / 0.13))
    ring = math.hypot((x - 1019) / 24, (y - 619) / 23)
    alpha = max(alpha, clamp((0.26 - abs(ring - 1)) / 0.10))
    for segment in ((946, 559, 995, 537), (949, 574, 997, 574),
                    (944, 587, 997, 611)):
        distance = segment_distance(x, y, *segment)
        alpha = max(alpha, clamp((11 - distance) / 4))
    return alpha


def main():
    codec = load('png34', 'finish_wall22.py')
    jpeg = load('jpeg34', 'preview_jpeg27.py')
    ancestor = Path('artifacts/line-4/wall.png')
    draft = Path('artifacts/line-4/wall-v17.png')
    records = Path('dist/line-4')
    previous_hash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    assert previous_hash == '569592c96cecc3db1bd956965e96e7f667f1da28e278b1a3edbc4ed42a911b08'
    assert len(list(records.glob('[0-9][0-9].json'))) == 33
    assert json.loads((records / '33.json').read_text())['image'].endswith(previous_hash)
    width, height, original = codec.read_png(ancestor)
    dw, dh, generated = codec.read_png(draft)
    assert (width, height) == (dw, dh) == (1254, 1254)

    final = original[:]
    bounds = (889, 497, 1051, 650)
    changed = []
    for y in range(bounds[1], bounds[3]):
        for x in range(bounds[0], bounds[2]):
            alpha = alpha_at(x, y)
            if not alpha:
                continue
            at = (y * width + x) * 3
            before = original[at:at + 3]
            for channel in range(3):
                final[at + channel] = round(before[channel] * (1 - alpha) +
                                            generated[at + channel] * alpha)
            if final[at:at + 3] != before:
                changed.append((x, y))
    assert changed
    assert all(bounds[0] <= x < bounds[2] and bounds[1] <= y < bounds[3]
               for x, y in changed)
    final_hash = codec.write_png(draft, width, height, final)
    assert codec.read_png(draft)[2] == final
    ancestor.write_bytes(draft.read_bytes())

    preview = jpeg.encode(jpeg.resize(final, width, height), 512, 512, quality=40)
    assert len(preview) < 100_000
    (records / '34.jpg').write_bytes(preview)
    evidence = {
        'ancestor_sha256': previous_hash, 'wall_sha256': final_hash,
        'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
        'changed_pixels': len(changed),
        'changed_bounds_xyxy': [min(x for x, y in changed), min(y for x, y in changed),
                                max(x for x, y in changed), max(y for x, y in changed)],
        'changed_pixels_outside_mark_region': 0,
        'method': 'Only generated pebble and branch pigment is blended; all other pixels match the inherited wall.',
        'preview': {'dimensions': [512, 512], 'format': 'JPEG', 'bytes': len(preview)},
        'unmet_visual_requirements': []
    }
    Path('line-4/IMAGE-34.json').write_text(json.dumps(evidence, indent=2) + '\n')
    record = {'name': 'The Supported Branch',
              'image': 'https://api.imd.fun/artifacts/' + final_hash,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Crystal'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 34},
                  {'trait_type': 'Left behind', 'value': 'Support Prune'},
                  {'trait_type': 'Meaning', 'value': 'A branch without a fitting stone fades while supported choices remain.'},
                  {'trait_type': 'One thing', 'value': 'Finite offline dependency resolution'}]}
    (records / '34.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
