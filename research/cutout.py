#!/usr/bin/env python3
"""Cuts the picked objects out of their backgrounds, in the Supermenu's look (black and white, 300 px tall).

    python3 research/cutout.py               # uses research/large/ where a picture is there, else the small copy
    python3 research/cutout.py --small       # small copies only (a quick preview)

Needs Pillow and rembg (pip3 install "rembg[cpu]"); the first run downloads the cutting model (about 180 MB).
Writes research/cutouts/<name>.webp and research/cutouts.html, a check page: each original beside its cut-out,
numbered, on the case's pink. Nothing goes into source/ until the cut-outs are accepted.
"""
import argparse, csv, html, pathlib, sys
from PIL import Image, ImageOps, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'cutouts'
HEIGHT = 300          # every object in source/objects is 300 px tall
MODEL = 'isnet-general-use'


def harden(alpha):
    """Drops faint haze (strings, shadows) and keeps edges soft: below 30 -> clear, above 225 -> solid."""
    return alpha.point(lambda a: 0 if a < 30 else 255 if a > 225 else int((a - 30) * 255 / 195))


def cut(im, session):
    from rembg import remove
    rgba = remove(im.convert('RGB'), session=session)
    a = harden(rgba.getchannel('A'))
    box = a.point(lambda v: 255 if v > 8 else 0).getbbox()
    if not box:
        return None
    grey = ImageOps.grayscale(rgba.convert('RGB'))
    grey = ImageOps.autocontrast(grey, cutoff=1, mask=a.point(lambda v: 255 if v > 128 else 0))
    grey, a = grey.crop(box), a.crop(box)
    w = max(1, round(grey.width * HEIGHT / grey.height))
    grey = grey.resize((w, HEIGHT), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
    a = a.resize((w, HEIGHT), Image.LANCZOS)
    out = Image.merge('RGBA', (grey, grey, grey, a))
    return out, (box[2] - box[0], box[3] - box[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--small', action='store_true', help='use the small search copies only')
    ap.add_argument('--only', help='comma-separated picture names to redo')
    a = ap.parse_args()
    from rembg import new_session
    session = new_session(MODEL)
    with (HERE / 'picks.csv').open(encoding='utf-8') as f:
        picks = list(csv.DictReader(f))
    with (HERE / 'candidates.csv').open(encoding='utf-8') as f:
        cand = {f"{r['source']}:{r['id']}": r for r in csv.DictReader(f)}
    OUT.mkdir(exist_ok=True)
    rows = []
    for n, p in enumerate(picks, 1):
        r = cand[p['key']]
        stem = pathlib.Path(r['file']).stem
        big = HERE / 'large' / (stem + '.jpg')
        src = HERE / r['file'] if a.small or not big.exists() else big
        dest = OUT / (stem + '.webp')
        if not a.only or stem in a.only.split(','):
            res = cut(Image.open(src), session)
            if not res:
                print(f'{n:3d} {stem}: nothing found'); continue
            img, size = res
            img.save(dest, 'WEBP', quality=88, method=6)
            low = ' (small source: object only %dx%d px)' % size if size[1] < HEIGHT else ''
            print(f'{n:3d} {stem} {img.width}x{img.height}{low}')
        rows.append((n, p, r, src, dest))
    page = ['<!doctype html><meta charset="utf-8"><title>Supermenu: check the cut-outs</title>',
            '<style>body{font:14px system-ui,sans-serif;color:#000033;margin:16px}'
            '.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}'
            '.c{border:1px solid #ccc;padding:8px}.p{display:flex;gap:6px;align-items:end;height:200px}'
            '.p img{max-height:200px;max-width:50%;object-fit:contain}.p .o{background:#FFCCCC}'
            '.n{font-weight:700;font-size:18px}.t{color:#5A5A73;font-size:12px}</style>',
            '<h1>Supermenu: check the cut-outs</h1><p>Each original beside its cut-out on the case\'s pink. '
            'Reply with the numbers to drop or redo.</p><div class="g">']
    for n, p, r, src, dest in rows:
        page.append(f'<div class="c"><div class="p"><img src="{html.escape(str(src.relative_to(HERE)))}" alt="">'
                    f'<img class="o" src="cutouts/{html.escape(dest.name)}" alt=""></div>'
                    f'<span class="n">{n}</span> {html.escape(p["title"])}'
                    f'<div class="t">{html.escape(p["row"])} · {html.escape(p["archive"])}</div></div>')
    page.append('</div>')
    (HERE / 'cutouts.html').write_text('\n'.join(page), encoding='utf-8')
    print(f'\n{len(rows)} cut-outs in research/cutouts/, check page research/cutouts.html')
    return 0


if __name__ == '__main__':
    sys.exit(main())
