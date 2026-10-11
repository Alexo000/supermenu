#!/usr/bin/env python3
"""Makes research/review.html: a page for choosing among the search candidates.

    python3 research/make_review.py

Needs Pillow (already on the Mac if build tools ran; otherwise: pip3 install pillow).
It makes small copies of the pictures in research/thumbs/ (kept out of git), scores each picture for how plain
its background is (plain grounds cut out cleanly), and writes review.html next to this file.
Open review.html in a browser. Picks are remembered in that browser; "Save my picks" writes picks.csv.
"""
import csv, html, json, pathlib, re, sys
from PIL import Image, ImageOps, ImageStat

HERE = pathlib.Path(__file__).resolve().parent
THUMBS = HERE / 'thumbs'
TARGET = {'seals': 6, 'tools': 10, 'chance': 6, 'keys': 5, 'mended': 4, 'boxes': 6, 'models': 6,
          'regions': 15, 'materials': 6}
LABEL = {'seals': 'Seals and stamps', 'tools': 'Tools and measures', 'chance': 'Dice, lots, games', 'keys': 'Keys, locks, tokens',
         'mended': 'Mended things', 'boxes': 'Boxes, baskets, cases', 'models': 'Models, toys, dolls',
         'regions': 'Missing regions', 'materials': 'Missing materials'}
FLAT = re.compile(r'print|photograph|drawing|book|painting|engraving|etching|lithograph|picture|manuscript|'
                  r'woodcut|poster|map|negative|albumen|postcard|page|letter', re.I)


def ground(im):
    """0-1: how much of the picture's edge is one even tone (1 = a clean studio ground)."""
    g = ImageOps.grayscale(im)
    w, h = g.size
    b = max(2, int(min(w, h) * 0.06))
    strips = [g.crop((0, 0, w, b)), g.crop((0, h - b, w, h)), g.crop((0, 0, b, h)), g.crop((w - b, 0, w, h))]
    px = [p for s in strips for p in s.tobytes()]
    px.sort()
    med = px[len(px) // 2]
    near = sum(1 for p in px if abs(p - med) <= 14) / len(px)
    return round(near, 3)


def main():
    with (HERE / 'candidates.csv').open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    THUMBS.mkdir(exist_ok=True)
    items, bad = [], 0
    for r in rows:
        src = HERE / r['file']
        th = THUMBS / (src.stem + '.jpg')
        try:
            if not th.exists():
                im = Image.open(src).convert('RGB')
                im.thumbnail((360, 360))
                im.save(th, quality=78)
            score = ground(Image.open(th))
        except Exception:
            bad += 1
            continue
        flat = bool(FLAT.search(' '.join([r.get('kind', ''), r.get('title', '')])))
        items.append({'k': f"{r['source']}:{r['id']}", 'row': r['row'], 'src': r['source'], 't': r.get('title', ''),
                      'kind': r.get('kind', ''), 'cul': r.get('culture', ''), 'date': r.get('date', ''),
                      'mat': r.get('material', ''), 'lic': r.get('licence', ''), 'page': r.get('page', ''),
                      'img': 'thumbs/' + th.name, 'g': score, 'flat': flat})
    page = TEMPLATE.replace('__DATA__', json.dumps(items, ensure_ascii=False).replace('</', '<\\/')) \
                   .replace('__ROWS__', json.dumps([{'key': k, 'label': LABEL[k], 'target': TARGET[k]} for k in TARGET]))
    (HERE / 'review.html').write_text(page, encoding='utf-8')
    print(f'review.html: {len(items)} candidates' + (f', {bad} pictures could not be read' if bad else ''))


TEMPLATE = r"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Supermenu: choose new objects</title>
<style>
:root{--ground:#fff;--case:#FFCCCC;--ink:#000033;--mark:#FF5E39;--rule:#ccc;--soft:#5A5A73;
  --f-num:"VT323",ui-monospace,Menlo,monospace;--f-text:system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;font-family:var(--f-text);font-size:14px;color:var(--ink);background:var(--ground)}
header{position:sticky;top:0;z-index:2;background:var(--ground);border-bottom:1px solid var(--rule);padding:12px 16px;display:grid;gap:10px}
h1{margin:0;font-size:20px;font-weight:600}
.tabs{display:flex;flex-wrap:wrap;gap:6px}
.tabs button{font:inherit;border:1px solid var(--rule);background:var(--ground);color:var(--ink);padding:5px 10px;cursor:pointer}
.tabs button[aria-pressed="true"]{border-color:var(--ink);background:var(--ink);color:#fff}
.tabs .n{font-variant-numeric:tabular-nums;opacity:.8;margin-left:4px}
.tabs .full{color:var(--mark)}
.tools{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;color:var(--soft)}
.tools label{display:flex;gap:5px;align-items:center;cursor:pointer}
#arch{display:flex;flex-wrap:wrap;gap:4px 12px}
@media (max-width:700px){header{position:static}}
.btn{font:inherit;font-weight:600;border:1px solid var(--ink);background:var(--ink);color:#fff;padding:6px 12px;cursor:pointer}
.btn.q{background:var(--ground);color:var(--ink)}
main{padding:12px 16px 60px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.c{position:relative;border:2px solid transparent;background:#f6f6f6;cursor:pointer;display:grid;grid-template-rows:150px auto;padding:0;text-align:left;font:inherit;color:inherit}
.c img{width:100%;height:150px;object-fit:contain;background:#fff;filter:grayscale(1)}
.c .m{padding:4px 6px 6px;font-size:11.5px;line-height:1.3;display:grid;gap:2px}
.c .tt{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.c .s{color:var(--soft)}
.c[aria-pressed="true"]{border-color:var(--mark);background:#fff1ec}
.c[aria-pressed="true"]::after{content:"✓";position:absolute;top:6px;right:6px;width:22px;height:22px;border-radius:50%;background:var(--mark);color:#fff;font-weight:700;text-align:center;line-height:22px}
.c a{color:var(--soft)}
.c:focus-visible{outline:2px solid var(--ink)}
.empty{color:var(--soft);padding:30px 0}
#out{width:100%;min-height:80px;font-family:Menlo,monospace;font-size:12px;margin-top:8px}
</style></head><body>
<header>
  <h1>Supermenu: choose new objects</h1>
  <div class="tabs" id="tabs"></div>
  <div class="tools">
    <label><input type="checkbox" id="plain" checked> Plain backgrounds first</label>
    <label><input type="checkbox" id="noflat"> Hide prints and photographs</label>
    <label><input type="checkbox" id="mine"> Show only my picks</label>
    <span id="arch"></span>
    <button class="btn" id="save">Save my picks</button>
    <button class="btn q" id="copy">Show picks as text</button>
    <span id="total"></span>
  </div>
</header>
<main><div class="grid" id="grid"></div><textarea id="out" hidden readonly></textarea></main>
<script>
const ITEMS=__DATA__, ROWS=__ROWS__;
const KEY='supermenu.review.picks';
let picks=new Set();try{picks=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify([...picks]))}catch(e){}};
let row=ROWS[0].key;const off=new Set();
const $=id=>document.getElementById(id);
const archives=[...new Set(ITEMS.map(i=>i.src))].sort();
$('arch').innerHTML=archives.map(a=>`<label><input type="checkbox" data-a="${a}" checked> ${a}</label>`).join(' ');
$('arch').addEventListener('change',e=>{const a=e.target.dataset.a;if(!a)return;e.target.checked?off.delete(a):off.add(a);draw()});
for(const id of ['plain','noflat','mine'])$(id).addEventListener('change',draw);
function count(k){return ITEMS.filter(i=>i.row===k&&picks.has(i.k)).length}
function tabs(){
  $('tabs').innerHTML='';
  for(const r of ROWS){const b=document.createElement('button');const n=count(r.key);
    b.innerHTML=`${r.label}<span class="n ${n>=r.target?'full':''}">${n}/${r.target}</span>`;
    b.setAttribute('aria-pressed',r.key===row);b.onclick=()=>{row=r.key;window.scrollTo(0,0);draw()};$('tabs').append(b)}
  $('total').textContent=`${picks.size} picked in all`;
}
function draw(){
  tabs();
  let list=ITEMS.filter(i=>i.row===row&&!off.has(i.src));
  if($('noflat').checked)list=list.filter(i=>!i.flat);
  if($('mine').checked)list=list.filter(i=>picks.has(i.k));
  if($('plain').checked)list=list.slice().sort((a,b)=>b.g-a.g);
  const g=$('grid');g.innerHTML='';
  if(!list.length){g.innerHTML='<p class="empty">Nothing here with these settings.</p>';return}
  for(const i of list){
    const c=document.createElement('button');c.type='button';c.className='c';c.setAttribute('aria-pressed',picks.has(i.k));
    c.title=[i.t,i.kind,i.cul,i.date,i.mat,i.src+' · '+i.lic].filter(Boolean).join('\n');
    c.innerHTML=`<img loading="lazy" src="${i.img}" alt=""><span class="m"><span class="tt"></span><span class="s"></span></span>`;
    c.querySelector('.tt').textContent=i.t||'(untitled)';
    c.querySelector('.s').textContent=[i.cul,i.date].filter(Boolean).join(', ').slice(0,60)+' · '+i.src;
    if(i.page){const a=document.createElement('a');a.href=i.page;a.target='_blank';a.rel='noopener';a.textContent='museum page';a.onclick=e=>e.stopPropagation();c.querySelector('.m').append(a)}
    c.onclick=()=>{picks.has(i.k)?picks.delete(i.k):picks.add(i.k);save();c.setAttribute('aria-pressed',picks.has(i.k));tabs()};
    g.append(c);
  }
}
function picksCsv(){
  const esc=v=>'"'+String(v??'').replace(/"/g,'""')+'"';
  const lines=['key,row,archive,title,culture,date,page'];
  for(const i of ITEMS)if(picks.has(i.k))lines.push([i.k,i.row,i.src,i.t,i.cul,i.date,i.page].map(esc).join(','));
  return lines.join('\n')+'\n';
}
$('save').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([picksCsv()],{type:'text/csv'}));a.download='picks.csv';a.click()};
$('copy').onclick=()=>{const o=$('out');o.hidden=false;o.value=picksCsv();o.select()};
draw();
</script></body></html>
"""

if __name__ == '__main__':
    sys.exit(main())
