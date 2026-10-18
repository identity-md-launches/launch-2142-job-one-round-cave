"""Check round 37 output bytes, inherited pixels, records, and protected trees."""
import hashlib
import json
from pathlib import Path
import re

from check_deliverable import jpeg_size
from finish_wall import read_png


def protected_fingerprints():
    return {path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for number in range(1, 5)
            for folder in (Path(f'line-{number}'), Path(f'dist/line-{number}'))
            for path in sorted(folder.rglob('*')) if path.is_file()}


def main():
    checks = json.loads(Path('gathering/checks-37.json').read_text())
    fingerprint = protected_fingerprints()
    assert checks['line_files_unchanged'] and len(fingerprint) == checks['protected_files_count']
    assert hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest() == checks['protected_files_sha256']
    assert len(checks['suites']) == 60 and checks['total_tests'] == 784
    assert len(checks['demos']) == 67
    assert all(item['exit'] == item['expected_exit'] for item in checks['suites'] + checks['demos'])
    shared = json.loads(Path('gathering/shared-checks-37.json').read_text())
    assert shared['total_tests'] == 119
    assert all(item['exit'] == 0 for item in shared['suites'])
    assert len(json.loads(Path('gathering/latest-checks-37.json').read_text())) == 8
    for item in json.loads(Path('shared/merge-citations/PROVENANCE.json').read_text()):
        source = Path(item['source']).read_bytes()
        copy = Path('shared/merge-citations', item['copy']).read_bytes()
        assert hashlib.sha256(source).hexdigest() == item['sha256']
        assert source == copy

    ancestor = Path('artifacts/gathering/wall-v16.png')
    wall = Path('artifacts/gathering/wall-v17.png')
    aw, ah, old = read_png(ancestor)
    width, height, pixels = read_png(wall)
    evidence = json.loads(Path('gathering/image-preservation-37.json').read_text())
    assert (aw, ah) == (width, height) == (1254, 1254)
    assert hashlib.sha256(ancestor.read_bytes()).hexdigest() == evidence['ancestor_sha256']
    digest = hashlib.sha256(wall.read_bytes()).hexdigest()
    assert digest == evidence['wall_sha256']
    x0, y0, span_x, span_y = evidence['new_mark_rectangle']
    changed = outside = 0
    for index in range(width * height):
        pos = index * 3
        if pixels[pos:pos + 3] != old[pos:pos + 3]:
            changed += 1
            x, y = index % width, index // width
            outside += not (x0 <= x < x0 + span_x and y0 <= y < y0 + span_y)
    assert changed == evidence['changed_pixels'] == 754 and outside == 0
    assert Path('artifacts/gathering/wall.png').resolve() == wall.resolve()

    record = json.loads(Path('dist/gathering/37.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    traits = {item['trait_type']: item['value'] for item in record['attributes']}
    assert set(traits) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 37
    assert traits['One thing'] == 'Gathering'
    preview = Path('dist/gathering/37.jpg')
    assert jpeg_size(preview.read_bytes()) == (512, 512)
    assert preview.stat().st_size <= 100000

    goals = [{'line': number, 'goal': Path(f'line-{number}/GOAL.md').read_text().strip()}
             for number in range(1, 5)]
    assert json.loads(Path('dist/goals.json').read_text()) == goals
    page = Path('dist/index.html').read_text()
    embedded = re.search(r'<script id="records" type="application/json">(.*?)</script>', page, re.S)
    assert embedded
    groups = json.loads(embedded[1])
    total = pending = 0
    for group, folder in zip(groups, ('line-1', 'line-2', 'line-3', 'line-4', 'gathering')):
        paths = sorted(Path('dist', folder).glob('[0-9][0-9].json'), reverse=True)
        expected = [{'number': int(path.stem), 'path': path.relative_to('dist').as_posix(),
                     **json.loads(path.read_text())} for path in paths]
        assert group['records'] == expected
        total += len(paths)
        for entry in expected:
            if entry['name'] == 'Not painted yet':
                pending += 1
                assert not Path('dist', entry['path']).with_suffix('.jpg').exists()
    assert len(groups) == 5 and total == 179 and pending == 100
    assert groups[-1]['records'][0]['number'] == 37
    gallery = json.loads(Path('gathering/gallery-checks-37.json').read_text())
    assert gallery['passed'] and gallery['records'] == total
    assert Path('gathering/COINS.md').read_text().startswith('none\n')
    for folder in ('gathering', 'shared', 'dist'):
        assert all(path.stat().st_size <= 100000 for path in Path(folder).rglob('*') if path.is_file())

    review = {'number': 37, 'line_files_and_records_unchanged': True,
              'line_suites_passed': 60, 'line_tests_passed': 784,
              'expected_demo_statuses': 67, 'direct_current_demos_passed': 8,
              'shared_tests_passed': 119, 'gallery_records': total,
              'preserved_placeholders': pending,
              'wall': {'path': str(wall), 'dimensions': [width, height],
                       'format': 'PNG', 'mode': 'RGB', 'sha256': digest},
              'preview': {'path': str(preview), 'dimensions': [512, 512],
                          'format': 'JPEG', 'bytes': preview.stat().st_size},
              'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
              'visual_review': {
                  'method': 'Full wall and 512-pixel JPEG inspected locally.',
                  'pepe': 'Inherited wide mouth and heavy-lidded eyes remain visible.',
                  'hands': 'No hands or handprints added; inherited concealed hands unchanged.',
                  'text_or_prohibited_symbols_observed': False,
                  'limitation': 'The small gathering mark is subdued at full-wall scale.'},
              'unmet_visual_requirements': [], 'coins': 'none'}
    Path('gathering/REVIEW-37.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
