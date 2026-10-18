"""Check this round's output contract using only workspace files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('check37_png', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
old = Path('artifacts/line-2/wall-v16.png')
wall = Path('artifacts/line-2/wall-v17.png')
w, h, before = png.read_png(old)
nw, nh, after = png.read_png(wall)
assert (w, h) == (nw, nh) == (1254, 1254)
assert Path('artifacts/line-2/wall.png').read_bytes() == wall.read_bytes()
review = json.loads(Path('line-2/REVIEW-37.json').read_text())
assert review['format'] == 'PNG' and review['dimensions'] == [w,h]
digest = hashlib.sha256(wall.read_bytes()).hexdigest()
assert digest == review['wallSha256']
x,y,rw,rh = review['newMarkRectangle']
changed = [i for i in range(w*h) if before[i*3:i*3+3] != after[i*3:i*3+3]]
assert len(changed) == review['changedPixels'] == 3608
assert all(x <= i%w < x+rw and y <= i//w < y+rh for i in changed)
record = json.loads(Path('dist/line-2/37.json').read_text())
assert set(record) == {'name', 'image', 'attributes'}
assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
attributes = record['attributes']
assert len(attributes) == 6
assert all(set(a) == {'trait_type','value'} for a in attributes)
traits = {a['trait_type']:a['value'] for a in attributes}
assert set(traits) == {'Cave','Wall','Number','Left behind','Meaning','One thing'}
assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Line 2'
assert type(traits['Number']) is int and traits['Number'] == 37
assert traits['Left behind'] == 'Receipt Capsule'
assert len(list(Path('dist/line-2').glob('[0-9][0-9].json'))) == 37
thumbnail = Path('dist/line-2/37.jpg').read_bytes()
assert thumbnail[:2] == b'\xff\xd8' and thumbnail[-2:] == b'\xff\xd9'
assert len(thumbnail) == review['preview']['bytes'] < 100000
# Confirm JPEG frame dimensions without decoding or writing another image.
at = 2
while at < len(thumbnail):
    assert thumbnail[at] == 255
    marker = thumbnail[at+1]
    size = int.from_bytes(thumbnail[at+2:at+4], 'big')
    if marker == 0xc0:
        assert int.from_bytes(thumbnail[at+5:at+7], 'big') == 512
        assert int.from_bytes(thumbnail[at+7:at+9], 'big') == 512
        break
    assert marker != 0xda, 'missing frame dimensions'
    at += size+2
else:
    raise AssertionError('missing JPEG frame')
assert subprocess.check_output(['git','show','HEAD:line-2/GOAL.md']) == Path('line-2/GOAL.md').read_bytes()
changed_tracked = subprocess.check_output(['git','diff','HEAD','--name-only'], text=True).splitlines()
assert set(changed_tracked) <= {'line-2/USED.md','artifacts/line-2/wall.png'}
untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard'], text=True).splitlines()
assert all(p.startswith(('line-2/','dist/line-2/','artifacts/line-2/','test/scratch/')) for p in untracked)
for path in untracked:
    if not path.startswith(('artifacts/','test/scratch/')):
        assert Path(path).stat().st_size <= 100000, path
# The named output must remain untracked for the artifact uploader.
assert not subprocess.check_output(['git','ls-files','--','artifacts/line-2/wall-v17.png'])
print(json.dumps({'passed': True, 'dimensions': [w,h], 'format':'PNG',
                  'changedPixels':len(changed), 'changedPixelsOutsideRectangle':0,
                  'recordNumber':37,'goalUnchanged':True,'olderRecordsUnchanged':True,
                  'sourceScopeChecked':True,'namedOutputUntracked':True}, indent=2))
