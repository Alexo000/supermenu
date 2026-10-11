#!/usr/bin/env python3
"""Supermenu archive search: finds open-access objects for the wanted list.

Run it on your Mac (it needs your own internet connection), from the supermenu folder:

    python3 research/search.py            # search everything, about 10-20 minutes
    python3 research/search.py --dry      # only count what each search would find, no downloads
    python3 research/search.py --row seals --per 4   # one row of the wanted list, 4 per search word

Or open Claude Code in the supermenu folder and ask it to run research/search.py.

What it does: for each row of the wanted list and each search word, it asks three open archives
(the Met, the Cleveland Museum of Art, the Art Institute of Chicago) for objects whose images are
public domain or CC0, downloads a small picture of each, and writes everything it found to
research/candidates.csv. Nothing is sent but the search words. Only Python's standard library is used.

Afterwards Claude lays the pictures out on contact sheets so you can choose.
The museum sites were not reachable from Claude's workspace, so this script has not been run
against them yet: if a source answers in an unexpected way, it is skipped and noted, and the rest carry on.
"""
import argparse, csv, json, pathlib, re, sys, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'candidates'
CSV = HERE / 'candidates.csv'
UA = 'Supermenu research (ramos-saavedra.com) python-urllib'

# The wanted list (see the doc "Supermenu: gaps and archive search plan"). Edit freely.
WANTED = {
    'seals': ['seal', 'stamp seal', 'cylinder seal', 'signet ring'],
    'tools': ['balance weight', 'sundial', 'abacus', 'measuring rod', 'tally stick', 'scale weight'],
    'chance': ['dice', 'astragal', 'game piece', 'gaming counter', 'divination'],
    'keys': ['key', 'padlock', 'token', 'tessera'],
    'mended': ['repaired bowl', 'kintsugi', 'mended'],
    'boxes': ['basket', 'box', 'purse', 'case', 'casket'],
    'models': ['model boat', 'house model', 'toy', 'doll', 'miniature'],
    'regions': ['Papua New Guinea', 'Maori', 'Hawaii', 'Iran', 'Ottoman', 'Islamic', 'Inuit', 'Peru',
                'Maya', 'Aztec', 'Bactria', 'Tibet'],
    'materials': ['glass vessel', 'textile', 'feather', 'basketry', 'bone carving'],
}
# Never kept, whatever the licence: human remains.
SKIP = re.compile(r'\b(skull|cranium|mumm(y|ies)|human remains|tsantsa|shrunken head)\b', re.I)


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'AIC-User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # network trouble: wait and try again
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def getjson(url):
    return json.loads(get(url).decode('utf-8'))


def met(term, per):
    q = urllib.parse.urlencode({'q': term, 'hasImages': 'true'})
    ids = (getjson(f'https://collectionapi.metmuseum.org/public/collection/v1/search?{q}').get('objectIDs') or [])
    out = []
    for oid in ids[:per * 4]:  # some records are not open access; look a little further
        if len(out) >= per:
            break
        o = getjson(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}')
        time.sleep(0.1)
        if not o.get('isPublicDomain') or not o.get('primaryImageSmall'):
            continue
        out.append({'source': 'Met', 'id': oid, 'title': o.get('title', ''), 'kind': o.get('objectName', ''),
                    'culture': o.get('culture', '') or o.get('country', ''), 'date': o.get('objectDate', ''),
                    'material': o.get('medium', ''), 'licence': 'Public domain (Met Open Access)',
                    'credit': 'The Metropolitan Museum of Art, ' + (o.get('creditLine', '') or ''),
                    'page': o.get('objectURL', ''), 'image': o['primaryImageSmall']})
    return out


def cleveland(term, per):
    q = urllib.parse.urlencode({'q': term, 'cc0': '', 'has_image': 1, 'limit': per})
    data = getjson(f'https://openaccess-api.clevelandart.org/api/artworks/?{q}').get('data', [])
    out = []
    for o in data:
        img = ((o.get('images') or {}).get('web') or {}).get('url')
        if not img or o.get('share_license_status') != 'CC0':
            continue
        out.append({'source': 'Cleveland', 'id': o.get('id'), 'title': o.get('title', ''), 'kind': o.get('type', ''),
                    'culture': '; '.join(o.get('culture') or []), 'date': o.get('creation_date', ''),
                    'material': o.get('technique', ''), 'licence': 'CC0 (Cleveland Museum of Art Open Access)',
                    'credit': 'The Cleveland Museum of Art, ' + (o.get('creditline', '') or ''),
                    'page': o.get('url', ''), 'image': img})
    return out


def chicago(term, per):
    q = urllib.parse.urlencode({'q': term, 'limit': per, 'query[term][is_public_domain]': 'true',
                                'fields': 'id,title,image_id,artwork_type_title,place_of_origin,date_display,'
                                          'medium_display,is_public_domain,credit_line'})
    res = getjson(f'https://api.artic.edu/api/v1/artworks/search?{q}')
    base = (res.get('config') or {}).get('iiif_url', 'https://www.artic.edu/iiif/2')
    out = []
    for o in res.get('data', []):
        if not o.get('is_public_domain') or not o.get('image_id'):
            continue
        out.append({'source': 'Chicago', 'id': o.get('id'), 'title': o.get('title', ''),
                    'kind': o.get('artwork_type_title', ''), 'culture': o.get('place_of_origin', ''),
                    'date': o.get('date_display', ''), 'material': o.get('medium_display', ''),
                    'licence': 'CC0 (Art Institute of Chicago)',
                    'credit': 'Art Institute of Chicago, ' + (o.get('credit_line', '') or ''),
                    'page': f"https://www.artic.edu/artworks/{o['id']}",
                    'image': f"{base}/{o['image_id']}/full/400,/0/default.jpg"})
    return out


SOURCES = {'met': met, 'cleveland': cleveland, 'chicago': chicago}
FIELDS = ['row', 'term', 'source', 'id', 'title', 'kind', 'culture', 'date', 'material',
          'licence', 'credit', 'page', 'image', 'file']


def main():
    ap = argparse.ArgumentParser(description='Search open archives for the Supermenu wanted list.')
    ap.add_argument('--per', type=int, default=6, help='objects to keep per search word per archive (default 6)')
    ap.add_argument('--row', choices=sorted(WANTED), help='only this row of the wanted list')
    ap.add_argument('--source', choices=sorted(SOURCES), help='only this archive')
    ap.add_argument('--dry', action='store_true', help='count only; download nothing, write nothing')
    a = ap.parse_args()

    seen, rows, problems = set(), [], []
    if CSV.exists() and not a.dry:  # carry on from an earlier run without repeating it
        with CSV.open(newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                rows.append(r); seen.add((r['source'], str(r['id'])))
    for row, terms in WANTED.items():
        if a.row and row != a.row:
            continue
        for term in terms:
            for name, fn in SOURCES.items():
                if a.source and name != a.source:
                    continue
                try:
                    found = fn(term, a.per)
                except Exception as e:
                    problems.append(f'{name} / {term}: {e}')
                    continue
                new = 0
                for o in found:
                    key = (o['source'], str(o['id']))
                    if key in seen or SKIP.search(' '.join(str(o.get(k, '')) for k in ('title', 'kind', 'material'))):
                        continue
                    seen.add(key); new += 1
                    if a.dry:
                        continue
                    folder = OUT / row; folder.mkdir(parents=True, exist_ok=True)
                    file = folder / f"{o['source'].lower()}-{o['id']}.jpg"
                    try:
                        file.write_bytes(get(o['image']))
                    except Exception as e:
                        problems.append(f"picture {o['source']} {o['id']}: {e}")
                        continue
                    rows.append({**o, 'row': row, 'term': term, 'file': str(file.relative_to(HERE))})
                print(f'{row:10s} {term[:22]:22s} {name:9s} {new} new')
                time.sleep(0.3)
    if not a.dry:
        with CSV.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
        print(f'\n{len(rows)} candidates in {CSV.relative_to(HERE.parent)}, pictures in {OUT.relative_to(HERE.parent)}/')
    if problems:
        print(f'\n{len(problems)} searches or pictures failed (the rest are fine):')
        for p in problems[:30]:
            print('  -', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
