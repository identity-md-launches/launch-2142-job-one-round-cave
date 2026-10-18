"""Preserve ancestors; retain only generated pigment on previously bare rock."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png37', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
old = Path('artifacts/line-2/wall-v16.png')
out = Path('artifacts/line-2/wall-v17.png')
ancestor_sha = hashlib.sha256(old.read_bytes()).hexdigest()
assert ancestor_sha == '1f340760953433c1d770d95fa895d05960223f053d2698571538e293d44d377c'
w, h, ancestor = png.read_png(old)
dw, dh, draft = png.read_png(out)
assert (w, h) == (dw, dh) == (1254, 1254)
final = ancestor[:]
rect = (225, 290, 100, 120)
for y in range(rect[1], rect[1] + rect[3]):
    for x in range(rect[0], rect[0] + rect[2]):
        i = (y*w+x)*3
        r, g, b = draft[i:i+3]
        ellipse = ((x-275)/43)**2 + ((y-350)/53)**2
        dot = (x-260)**2 + (y-363)**2 < 13**2
        dashes = (260 < x < 282 and 325 < y < 357) or (275 < x < 297 and 347 < y < 377)
        alpha = 0
        if .62 < ellipse < 1.3 and r > 1.65*g and r > 2*b and g < 115:
            alpha = .86
        elif dot and r > 150 and g > 125 and b > 95 and r-g < 60:
            alpha = .88
        elif dashes and r < 95 and g < 75 and b < 60:
            alpha = .88
        if alpha:
            for c in range(3):
                final[i+c] = round(ancestor[i+c]*(1-alpha) + draft[i+c]*alpha)
changed = [i for i in range(w*h) if ancestor[3*i:3*i+3] != final[3*i:3*i+3]]
assert len(changed) > 500
assert all(rect[0] <= i%w < rect[0]+rect[2] and rect[1] <= i//w < rect[1]+rect[3] for i in changed)
digest = png.write_png(out,w,h,final)
wall = Path('artifacts/line-2/wall.png')
wall.unlink()
wall.symlink_to('wall-v17.png')
rgba = bytearray()
for y in range(512):
    ya,yb=y*h//512,(y+1)*h//512
    for x in range(512):
        xa,xb=x*w//512,(x+1)*w//512
        n=(yb-ya)*(xb-xa)
        for c in range(3):
            rgba.append(round(sum(final[(sy*w+sx)*3+c] for sy in range(ya,yb) for sx in range(xa,xb))/n))
        rgba.append(255)
subprocess.run(['node','-e',"const fs=require('fs');const enc=require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');const r=enc({data:fs.readFileSync(0),width:512,height:512},78);if(r.data.length>100000)throw Error('preview too large');fs.writeFileSync('dist/line-2/37.jpg',r.data);"],input=rgba,check=True)
review = {'round':37,'ancestorSha256':ancestor_sha,'wallSha256':digest,
          'dimensions':[w,h],'format':'PNG','channels':'RGB','newMarkRectangle':list(rect),
          'changedPixels':len(changed),'changedPixelsOutsideRectangle':0,
          'method':'Built-in imagegen edit of inherited wall; selected only new ochre oval, chalk seed and charcoal pigment on bare rock. All pixels outside the rectangle copied unchanged.',
          'visualReview':'Final PNG and JPEG inspected: new ochre enclosure, chalk seed and charcoal strokes; ancestral Pepe, two five-digit hands, pigments, stone, light and framing preserved. No added hands, text or prohibited symbol observed.',
          'unmetVisualRequirements':[], 'preview':{'path':'dist/line-2/37.jpg','format':'JPEG','dimensions':[512,512],'bytes':Path('dist/line-2/37.jpg').stat().st_size}}
Path('line-2/REVIEW-37.json').write_text(json.dumps(review,indent=2)+'\n')
record={'name':'The Carried Seed','image':'https://api.imd.fun/artifacts/'+digest,'attributes':[
{'trait_type':'Cave','value':'Crystal'}, {'trait_type':'Wall','value':'Line 2'}, {'trait_type':'Number','value':37},
{'trait_type':'Left behind','value':'Receipt Capsule'},
{'trait_type':'Meaning','value':'An ochre enclosure carries a chalk seed with its proof intact.'},
{'trait_type':'One thing','value':'Verify Ethereum account and storage proofs against trusted state roots'}]}
assert not Path('dist/line-2/37.json').exists()
Path('dist/line-2/37.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(review,indent=2))
