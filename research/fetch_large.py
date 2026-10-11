#!/usr/bin/env python3
"""Fetches larger pictures of the objects in research/picks.csv, for cutting out.

Run it on your Mac from the supermenu folder (it needs your own internet connection):

    python3 research/fetch_large.py

It reads picks.csv (saved from review.html) and candidates.csv, asks each museum for a bigger copy of the
same picture, and saves it in research/large/. Where a bigger copy cannot be had, it keeps the small one
and says so. Already-fetched pictures are skipped, so it can be run again. Only the standard library is used.
"""
import csv, pathlib, shutil, sys, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from search import get  # same polite downloader as the search (headers, retries, odd addresses)

OUT = HERE / 'large'


def bigger(source, url):
    """Addresses to try for a bigger copy, best first."""
    s = source.lower()
    if s == 'chicago':
        return [url.replace('/full/400,/', '/full/1686,/'), url.replace('/full/400,/', '/full/843,/')]
    if s == 'met':
        return [url.replace('/web-large/', '/original/')]
    if s == 'cleveland':
        return [url.replace('_web.jpg', '_print.jpg')]
    if s in ('rijksmuseum', 'smk'):
        return [url.replace('/full/400,/', '/full/1600,/').replace('/full/!400,/', '/full/!1600,1600/'),
                url.replace('/full/400,/', '/full/max/').replace('/full/!400,/', '/full/max/')]
    if s == 'europeana':  # the thumbnail service carries the original's address
        uri = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('uri', [''])[0]
        return [uri] if uri else []
    if s == 'smithsonian':
        return [url.replace('max=400', 'max=1600')]
    if s == 'wellcome':
        return [url.replace('/full/400,/', '/full/1600,/').replace('/full/!400,/', '/full/!1600,1600/')]
    return []


def main():
    with (HERE / 'picks.csv').open(encoding='utf-8') as f:
        picks = list(csv.DictReader(f))
    with (HERE / 'candidates.csv').open(encoding='utf-8') as f:
        cand = {f"{r['source']}:{r['id']}": r for r in csv.DictReader(f)}
    OUT.mkdir(exist_ok=True)
    got, small, missing = 0, [], []
    for p in picks:
        r = cand.get(p['key'])
        if not r:
            missing.append(p['key']); continue
        dest = OUT / (pathlib.Path(r['file']).stem + '.jpg')
        if dest.exists():
            got += 1; continue
        data = None
        for u in bigger(r['source'], r['image']):
            if not u or u == r['image']:
                continue
            try:
                d = get(u)
                if len(d) > 20000 or (len(d) > 2000 and d[:4] in (b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\x89PNG')):
                    data = d; break
            except Exception:
                continue
        if data:
            dest.write_bytes(data); got += 1
            print(f"{p['key']:55s} {len(data) // 1024:6d} KB")
        else:
            shutil.copyfile(HERE / r['file'], dest); small.append(p['key'])
            print(f"{p['key']:55s}  kept the small copy")
    print(f'\n{got} bigger pictures in research/large/')
    if small:
        print(f'{len(small)} kept small (no bigger copy found): ' + ', '.join(small))
    if missing:
        print(f'{len(missing)} picks not found in candidates.csv: ' + ', '.join(missing))
    return 0


if __name__ == '__main__':
    sys.exit(main())
