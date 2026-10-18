"""Add a small worn pigment link to the inherited gathering wall."""
import hashlib
import json
from math import atan2, cos, hypot, sin
from pathlib import Path

from finish_wall import read_png, write_png


ANCESTOR = Path('artifacts/gathering/wall-v16.png')
OUTPUT = Path('artifacts/gathering/wall-v17.png')
REGION = (681, 231, 91, 63)


def pigment(pixels, width, x, y, color, opacity):
    at = 3 * (y * width + x)
    for channel in range(3):
        pixels[at + channel] = round(pixels[at + channel] * (1 - opacity) +
                                     color[channel] * opacity)


def main():
    ancestor_hash = hashlib.sha256(ANCESTOR.read_bytes()).hexdigest()
    if ancestor_hash != '189c27d0a370241ed973117808f0b8581027585deaf829dd5d198261021a7077':
        raise ValueError('the inherited gathering wall has changed')
    width, height, original = read_png(ANCESTOR)
    if (width, height) != (1254, 1254):
        raise ValueError('unexpected cave dimensions')
    pixels = original[:]
    x0, y0, span_x, span_y = REGION
    for y in range(y0, y0 + span_y):
        for x in range(x0, x0 + span_x):
            grain = (x * 17041 + y * 7919 + x * y * 13) % 101
            for cx, cy, rx, ry, gap in ((704, 261, 17.5, 13.5, -0.45),
                                        (747, 264, 16.0, 12.5, 2.45)):
                dx, dy = (x - cx) / rx, (y - cy) / ry
                radius = hypot(dx, dy)
                angle = atan2(dy, dx)
                separation = abs(atan2(sin(angle-gap), cos(angle-gap)))
                if 0.84 < radius < 1.16 and separation > 0.21 and grain > 10:
                    strength = min(0.68, (1.16 - radius) * 4.2,
                                   (radius - 0.84) * 4.2)
                    strength *= 0.55 + 0.45 * grain / 100
                    pigment(pixels, width, x, y, (156, 63, 35), strength)
            # A short chalk bridge is rubbed across both loops.
            if 719 <= x <= 732 and 259 <= y <= 266 and grain > 16:
                edge = min(x - 718, 733 - x, y - 258, 267 - y)
                pigment(pixels, width, x, y, (218, 191, 147),
                        min(0.58, edge * 0.14) * (0.5 + grain / 200))
    changed = sum(original[i:i+3] != pixels[i:i+3] for i in range(0, len(pixels), 3))
    digest = write_png(OUTPUT, width, height, pixels)
    pointer = Path('artifacts/gathering/wall.png')
    if pointer.exists() or pointer.is_symlink():
        pointer.unlink()
    pointer.symlink_to(OUTPUT.name)
    result = {'ancestor_sha256': ancestor_hash, 'wall_sha256': digest,
              'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
              'new_mark_rectangle': list(REGION), 'changed_pixels': changed,
              'changed_pixels_outside_rectangle': 0,
              'motif': 'two irregular ochre loops with one chalk bridge; no hands or handprints'}
    Path('gathering/image-preservation-37.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
