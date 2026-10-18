/* Preserve ancestor pixels; transfer only the image tool's new earth pigment. */
'use strict';
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
const assert = require('assert');
const encodeJPEG = require('./tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const crcTable = Array.from({length:256}, (_, n) => {
  for(let k=0;k<8;k++)n=(n&1)?0xedb88320^(n>>>1):n>>>1;
  return n>>>0;
});
function crc32(bytes) {
  let crc=0xffffffff;
  for(const b of bytes)crc=crcTable[(crc^b)&255]^(crc>>>8);
  return (crc^0xffffffff)>>>0;
}
function readPNG(bytes) {
  assert(bytes.subarray(0,8).equals(Buffer.from('89504e470d0a1a0a','hex')));
  let width,height,channels;const parts=[];
  for(let at=8;at<bytes.length;) {
    const n=bytes.readUInt32BE(at),kind=bytes.toString('ascii',at+4,at+8);
    const body=bytes.subarray(at+8,at+8+n);
    assert.equal(crc32(bytes.subarray(at+4,at+8+n)),bytes.readUInt32BE(at+8+n));
    if(kind==='IHDR') {
      width=body.readUInt32BE(0);height=body.readUInt32BE(4);
      assert.equal(body[8],8);assert([2,6].includes(body[9]));
      assert.equal(body[10]+body[11]+body[12],0);channels=body[9]===2?3:4;
    }else if(kind==='IDAT')parts.push(body);
    else if(kind==='IEND')break;
    at+=n+12;
  }
  const stride=width*channels,packed=zlib.inflateSync(Buffer.concat(parts));
  assert.equal(packed.length,height*(stride+1));
  const unpacked=Buffer.alloc(width*height*channels);
  for(let y=0;y<height;y++)for(let x=0;x<stride;x++) {
    const at=y*stride+x,left=x>=channels?unpacked[at-channels]:0;
    const above=y?unpacked[at-stride]:0,diagonal=y&&x>=channels?unpacked[at-stride-channels]:0;
    const filter=packed[y*(stride+1)],v=packed[y*(stride+1)+x+1];let p=0;
    if(filter===1)p=left;
    if(filter===2)p=above;
    if(filter===3)p=(left+above)>>>1;
    if(filter===4){const q=left+above-diagonal,a=Math.abs(q-left),b=Math.abs(q-above),c=Math.abs(q-diagonal);p=a<=b&&a<=c?left:b<=c?above:diagonal;}
    assert(filter<=4);unpacked[at]=(v+p)&255;
  }
  const pixels=Buffer.alloc(width*height*3);
  for(let i=0;i<width*height;i++) {
    unpacked.copy(pixels,i*3,i*channels,i*channels+3);
    if(channels===4)assert.equal(unpacked[i*4+3],255);
  }
  return {width,height,pixels};
}
function writePNG(width,height,pixels) {
  function chunk(kind,body){const data=Buffer.concat([Buffer.from(kind),body]),a=Buffer.alloc(4),b=Buffer.alloc(4);a.writeUInt32BE(body.length);b.writeUInt32BE(crc32(data));return Buffer.concat([a,data,b]);}
  const header=Buffer.alloc(13);header.writeUInt32BE(width,0);header.writeUInt32BE(height,4);header[8]=8;header[9]=2;
  const raw=Buffer.alloc(height*(width*3+1));
  for(let y=0;y<height;y++)pixels.copy(raw,y*(width*3+1)+1,y*width*3,(y+1)*width*3);
  return Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(raw,{level:9})),chunk('IEND',Buffer.alloc(0))]);
}
function finish(draftBytes) {
  const ancestorPath='artifacts/line-3/wall-v15.png',outputPath='artifacts/line-3/wall-v17.png';
  const oldBytes=fs.readFileSync(ancestorPath);
  assert.equal(hash(oldBytes),'9a7bef978ad6fc15f7815417034551c43b7c3e1dceea68bc84ac32eb770fc0a5');
  assert(!fs.existsSync('dist/line-3/36.json'),'new record must not overwrite an existing record');
  const old=readPNG(oldBytes),draft=readPNG(draftBytes);
  assert.deepEqual([old.width,old.height],[1254,1254]);
  assert.deepEqual([draft.width,draft.height],[1254,1254]);
  const rect=[38,385,160,115],final=Buffer.from(old.pixels);
  for(let y=rect[1];y<rect[1]+rect[3];y++)for(let x=rect[0];x<rect[0]+rect[2];x++) {
    const at=(y*old.width+x)*3;
    const [r,g,b]=draft.pixels.subarray(at,at+3),[or,og,ob]=old.pixels.subarray(at,at+3);
    if(Math.abs(r-or)+Math.abs(g-og)+Math.abs(b-ob)<45)continue;
    let color;
    if(r>80&&r>g*1.75&&g>b*1.2)color=[145,53,26];
    else if(r<72&&g<62&&b<53&&or-r>30&&og-g>20)color=[36,28,21];
    else if(r>145&&g>130&&b>100&&g>og*1.3&&b>ob*1.3)color=[205,192,164];
    else continue;
    for(let c=0;c<3;c++)final[at+c]=Math.round(old.pixels[at+c]*.22+color[c]*.78);
  }
  let changed=0,outside=0;
  for(let i=0;i<old.width*old.height;i++)if(!final.subarray(i*3,i*3+3).equals(old.pixels.subarray(i*3,i*3+3))){
    changed++;const x=i%old.width,y=Math.floor(i/old.width);
    if(x<rect[0]||x>=rect[0]+rect[2]||y<rect[1]||y>=rect[1]+rect[3])outside++;
  }
  assert(changed>0);assert.equal(outside,0);
  const png=writePNG(old.width,old.height,final);assert(readPNG(png).pixels.equals(final));
  const rgba=Buffer.alloc(512*512*4);
  for(let y=0;y<512;y++)for(let x=0;x<512;x++) {
    const xa=Math.floor(x*old.width/512),xb=Math.floor((x+1)*old.width/512),ya=Math.floor(y*old.height/512),yb=Math.floor((y+1)*old.height/512);
    for(let c=0;c<3;c++){let sum=0;for(let sy=ya;sy<yb;sy++)for(let sx=xa;sx<xb;sx++)sum+=final[(sy*old.width+sx)*3+c];rgba[(y*512+x)*4+c]=Math.round(sum/((xb-xa)*(yb-ya)));}
    rgba[(y*512+x)*4+3]=255;
  }
  const jpeg=encodeJPEG({data:rgba,width:512,height:512},77).data;assert(jpeg.length<100000);
  fs.writeFileSync(outputPath,png,{flag:'wx'});
  fs.unlinkSync('artifacts/line-3/wall.png');
  fs.symlinkSync('wall-v17.png','artifacts/line-3/wall.png');
  fs.writeFileSync('dist/line-3/36.jpg',jpeg,{flag:'wx'});
  const sha=hash(png),report={wall:outputPath,format:'PNG',dimensions:[1254,1254],mode:'RGB',bytes:png.length,sha256:sha,
    ancestor_path:ancestorPath,ancestor_sha256:hash(oldBytes),generated_draft_sha256:hash(draftBytes),new_mark_rectangle:rect,
    changed_pixels:changed,changed_pixels_outside_rectangle:outside,
    thumbnail:{path:'dist/line-3/36.jpg',format:'JPEG',dimensions:[512,512],bytes:jpeg.length},
    visual_review:'pending',unmet_visual_requirements:['An inherited, partly occluded gripping hand remains unchanged; its complete five-digit count cannot be confirmed.']};
  fs.writeFileSync('line-3/IMAGE-36.json',JSON.stringify(report,null,2)+'\n');
  const record={name:'The Rejoined Trail',image:'https://api.imd.fun/artifacts/'+sha,attributes:[
    ['Cave','Crystal'],['Wall','Line 3'],['Number',36],['Left behind','Citation Report and Citation Trail'],
    ['Meaning','Two ochre stones joined by a charcoal trail reconnect a checked passage to its source.'],
    ['One thing','Offline document search with exact source line citations']].map(([trait_type,value])=>({trait_type,value}))};
  fs.writeFileSync('dist/line-3/36.json',JSON.stringify(record,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(report,null,2));
}
if(require.main===module) {
  let input='';
  if(process.stdin.isTTY)process.stdin.setRawMode(true);
  process.stdin.on('data',chunk=>{input+=chunk.toString('ascii');const end=input.indexOf('\x04');if(end>=0){finish(Buffer.from(input.slice(0,end),'base64'));process.exit(0);}});
}
module.exports={readPNG,writePNG};
