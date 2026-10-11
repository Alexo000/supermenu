#!/usr/bin/env python3
"""Supermenu archive search: finds open-access objects for the wanted list.

Run it on your Mac (it needs your own internet connection), from the supermenu folder:

    python3 research/search.py            # search everything, about 10-20 minutes
    python3 research/search.py --dry      # only count what each search would find, no downloads
    python3 research/search.py --row seals --per 4   # one row of the wanted list, 4 per search word

Or open Claude Code in the supermenu folder and ask it to run research/search.py.

What it does: for each row of the wanted list and each search word, it asks three open archives
(the Met, the Cleveland Museum of Art, the Art Institute of Chicago, the Wellcome Collection, and any added later) for objects whose images are
public domain or CC0, downloads a small picture of each, and writes everything it found to
research/candidates.csv. Nothing is sent but the search words. Only Python's standard library is used.

Afterwards Claude lays the pictures out on contact sheets so you can choose.
The museum sites were not reachable from Claude's workspace, so this script has not been run
against them yet: if a source answers in an unexpected way, it is skipped and noted, and the rest carry on.
"""
import argparse, csv, json, os, pathlib, re, sys, time, urllib.parse, urllib.request

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
            h = {'User-Agent': UA, 'AIC-User-Agent': UA}
            if 'artic.edu/iiif' in url:
                h['Referer'] = 'https://www.artic.edu/'  # Chicago's image server asks for it
            url = urllib.parse.quote(url, safe=':/?&=%#,!+;@~')  # some image addresses carry spaces
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # network trouble: wait and try again
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def getjson(url):
    return json.loads(get(url).decode('utf-8'))


def met(term, per):
    # the v1 search was retired on 1 October 2026; v1.1 takes the same filters and pages its results
    q = urllib.parse.urlencode({'q': term, 'hasImages': 'true', 'limit': per * 6})
    ids = (getjson(f'https://collectionapi.metmuseum.org/public/collection/v1.1/search?{q}').get('objectIDs') or [])
    out = []
    for oid in ids[:per * 4]:  # some records are not open access; look a little further
        if len(out) >= per:
            break
        try:  # a few listed objects have no record any more; skip them, not the whole search
            o = getjson(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}')
        except Exception:
            continue
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


def wellcome(term, per):
    # Wellcome Collection images: only those whose licence is the public domain mark or CC0
    q = urllib.parse.urlencode({'query': term, 'locations.license': 'pdm,cc-0', 'pageSize': per})
    res = getjson(f'https://api.wellcomecollection.org/catalogue/v2/images?{q}')
    out = []
    for o in res.get('results', []):
        lic = ''
        for loc in o.get('locations') or []:
            lic = ((loc.get('license') or {}).get('id') or lic)
        thumb = (o.get('thumbnail') or {}).get('url', '')
        if lic not in ('pdm', 'cc-0') or not thumb:
            continue
        img = thumb.replace('/info.json', '/full/400,/0/default.jpg')
        src = o.get('source') or {}
        out.append({'source': 'Wellcome', 'id': o.get('id'), 'title': src.get('title', ''), 'kind': src.get('type', ''),
                    'culture': '', 'date': '', 'material': '',
                    'licence': 'Public domain mark' if lic == 'pdm' else 'CC0', 'credit': 'Wellcome Collection',
                    'page': f"https://wellcomecollection.org/works/{src.get('id', '')}", 'image': img})
    return out


# Dutch words for the Rijksmuseum, whose search answers far better in Dutch; terms not listed go as they are
DUTCH = {'seal': 'zegelstempel', 'stamp seal': 'zegelstempel', 'cylinder seal': 'rolzegel', 'signet ring': 'zegelring',
         'balance weight': 'gewicht', 'sundial': 'zonnewijzer', 'abacus': 'telraam', 'measuring rod': 'maatstok',
         'tally stick': 'kerfstok', 'scale weight': 'muntgewicht', 'dice': 'dobbelsteen', 'astragal': 'bikkel',
         'game piece': 'speelstuk', 'gaming counter': 'speelpenning', 'divination': 'waarzeggerij',
         'key': 'sleutel', 'padlock': 'hangslot', 'token': 'penning', 'tessera': 'tessera',
         'repaired bowl': 'gerepareerd', 'mended': 'gerepareerd', 'basket': 'mand', 'box': 'doos',
         'purse': 'beurs', 'case': 'etui', 'casket': 'kistje', 'model boat': 'scheepsmodel',
         'house model': 'poppenhuis', 'toy': 'speelgoed', 'doll': 'pop', 'miniature': 'miniatuur',
         'glass vessel': 'glas', 'textile': 'textiel', 'feather': 'veer', 'basketry': 'vlechtwerk',
         'bone carving': 'been'}
LD = {'Accept': 'application/ld+json'}


def _ld(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **LD})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def _L(x):
    # Linked Art gives one value or a list of them; always hand back a list of dicts
    x = x if isinstance(x, list) else [x] if x else []
    return [v if isinstance(v, dict) else {'@value': v, 'id': v, 'content': v} for v in x]


def _en(notes):
    # the English label of a Linked Art notation, else the first one
    notes = _L(notes)
    for n in notes:
        if n.get('@language') == 'en':
            return n.get('@value', '')
    return notes[0].get('@value', '') if notes else ''


def rijks(term, per):
    # keyless Linked Art search: the word as an object type (Dutch, then English), then in titles, then descriptions
    word = DUTCH.get(term, term)
    items = []
    for field, w in (('type', word), ('type', term), ('title', word), ('description', word)):
        q = urllib.parse.urlencode({field: w, 'imageAvailable': 'true'})
        items = getjson(f'https://data.rijksmuseum.nl/search/collection?{q}').get('orderedItems') or []
        if items:
            break
    out = []
    for it in items[:per * 3]:
        if len(out) >= per:
            break
        try:  # one odd record is skipped, not the whole search
            o = _ld(it['id'])
            rights = [c.get('id', '') for s in _L(o.get('subject_of')) for r in _L(s.get('subject_to'))
                      for c in _L(r.get('classified_as'))]
            if not any('publicdomain/zero' in r or 'publicdomain/mark' in r for r in rights):
                continue
            vis = _ld(_L(o.get('shows'))[0]['id'])
            dig = _ld(_L(vis.get('digitally_shown_by'))[0]['id'])
            img = _L(dig.get('access_point'))[0].get('id', '').replace('/full/max/', '/full/400,/')
            if not img:
                continue
            ids = _L(o.get('identified_by'))
            names = [n for n in ids if n.get('type') == 'Name']
            title = next((n.get('content', '') for n in names
                          if any('300388277' in l.get('id', '') for l in _L(n.get('language')))),
                         names[0].get('content', '') if names else '')
            num = next((n.get('content', '') for n in ids if n.get('type') == 'Identifier'), '')
            prod = _L(o.get('produced_by'))[:1] or [{}]
            prod = prod[0]
            date = next((n.get('content', '') for t in _L(prod.get('timespan')) for n in _L(t.get('identified_by'))), '')
            page = next((a.get('id') for s in _L(o.get('subject_of')) for d in _L(s.get('digitally_carried_by'))
                         for a in _L(d.get('access_point'))), f'https://www.rijksmuseum.nl/en/collection/{num}')
            out.append({'source': 'Rijksmuseum', 'id': it['id'].rsplit('/', 1)[-1], 'title': title,
                        'kind': '; '.join(_en(c.get('notation')) for c in _L(o.get('classified_as')) if c.get('notation')),
                        'culture': '; '.join(p.get('_label', '') for p in _L(prod.get('took_place'))), 'date': date,
                        'material': '; '.join(_en(m.get('notation')) for m in _L(o.get('made_of'))),
                        'licence': 'Public domain / CC0 (Rijksmuseum)', 'credit': f'Rijksmuseum, Amsterdam, {num}',
                        'page': page, 'image': img})
        except Exception:
            continue
        time.sleep(0.1)
    return out


def smk(term, per):
    # Statens Museum for Kunst, Copenhagen: mostly paintings and prints; only public-domain images
    q = urllib.parse.urlencode({'keys': term, 'rows': per, 'filters': '[has_image:true],[public_domain:true]'})
    res = getjson(f'https://api.smk.dk/api/v1/art/search/?{q}')
    out = []
    for o in res.get('items') or []:
        thumb = o.get('image_thumbnail') or ''
        if not o.get('public_domain') or not thumb:
            continue
        num = o.get('object_number', '')
        title = next((t.get('title', '') for t in o.get('titles') or [] if t.get('language') == 'engelsk'),
                     ((o.get('titles') or [{}])[0]).get('title', ''))
        out.append({'source': 'SMK', 'id': num, 'title': title,
                    'kind': '; '.join(n.get('name', '') for n in o.get('object_names') or []),
                    'culture': '; '.join(p.get('creator', '') for p in o.get('production') or []),
                    'date': ((o.get('production_date') or [{}])[0]).get('period', ''),
                    'material': '; '.join((o.get('techniques') or []) + (o.get('materials') or [])),
                    'licence': 'Public domain (SMK Open)', 'credit': 'SMK, Statens Museum for Kunst, ' + num,
                    'page': o.get('frontend_url') or f'https://open.smk.dk/artwork/image/{num}',
                    'image': re.sub(r'/full/![0-9]+,/', '/full/!400,/', thumb)})
    return out


def europeana(term, per):
    # many smaller European museums; the public demo key works, your own goes in EUROPEANA_KEY
    key = os.environ.get('EUROPEANA_KEY', 'api2demo')
    q = urllib.parse.urlencode([('wskey', key), ('query', term), ('rows', per * 2), ('media', 'true'),
                                ('thumbnail', 'true'), ('qf', 'TYPE:IMAGE'), ('qf', 'RIGHTS:*publicdomain*')])
    res = getjson(f'https://api.europeana.eu/record/v2/search.json?{q}')
    out = []
    for o in res.get('items') or []:
        if len(out) >= per:
            break
        rights = ' '.join(o.get('rights') or [])
        prev = (o.get('edmPreview') or [''])[0]
        if not prev or not ('publicdomain/mark' in rights or 'publicdomain/zero' in rights):
            continue
        first = lambda k: (o.get(k) or [''])[0]
        out.append({'source': 'Europeana', 'id': o.get('id', '').strip('/').replace('/', '_'),
                    'title': first('title'), 'kind': first('edmConceptLabel') if isinstance(first('edmConceptLabel'), str)
                    else (first('edmConceptLabel') or {}).get('def', ''),
                    'culture': first('country'), 'date': first('year'), 'material': '',
                    'licence': 'CC0' if 'publicdomain/zero' in rights else 'Public domain mark',
                    'credit': f"{first('dataProvider')} via Europeana",
                    'page': (o.get('guid') or '').split('?')[0], 'image': prev + '&size=w400'})
    return out


def smithsonian(term, per):
    # Smithsonian Open Access; needs SI_API_KEY (free at api.data.gov), keeps only CC0 images
    key = os.environ.get('SI_API_KEY')
    if not key:
        raise RuntimeError('skipped: no SI_API_KEY set')
    q = urllib.parse.urlencode({'api_key': key, 'rows': per * 2,
                                'q': f'"{term}" AND online_media_type:"Images" AND media_usage:"CC0"'})
    rows = (getjson(f'https://api.si.edu/openaccess/api/v1.0/search?{q}').get('response') or {}).get('rows') or []
    out = []
    for o in rows:
        if len(out) >= per:
            break
        c = o.get('content') or {}
        dn, ix = c.get('descriptiveNonRepeating') or {}, c.get('indexedStructured') or {}
        media = [m for m in (dn.get('online_media') or {}).get('media') or []
                 if m.get('type') == 'Images' and (m.get('usage') or {}).get('access') == 'CC0' and m.get('idsId')]
        if not media:
            continue
        mat = next((f.get('content', '') for f in (c.get('freetext') or {}).get('physicalDescription') or []
                    if f.get('label') == 'Medium'), '')
        out.append({'source': 'Smithsonian', 'id': o.get('id', ''), 'title': o.get('title', ''),
                    'kind': '; '.join((ix.get('object_type') or [])[:2]),
                    'culture': '; '.join((ix.get('culture') or []) + (ix.get('place') or [])[:1]),
                    'date': '; '.join(ix.get('date') or []), 'material': mat, 'licence': 'CC0 (Smithsonian Open Access)',
                    'credit': f"Smithsonian Institution, {dn.get('data_source', '')}",
                    'page': dn.get('record_link') or dn.get('guid', ''),
                    'image': f"https://ids.si.edu/ids/deliveryService?id={media[0]['idsId']}&max=400"})
    return out


# More sources go here, each a function (term, per) -> list of dicts with the same keys as above,
# keeping only public-domain or CC0 images. See research/ADD_SOURCES.md.
SOURCES = {'met': met, 'cleveland': cleveland, 'chicago': chicago, 'wellcome': wellcome, 'rijks': rijks, 'smk': smk, 'europeana': europeana, 'smithsonian': smithsonian}
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
    if not os.environ.get('SI_API_KEY') and a.source in (None, 'smithsonian'):
        problems.append('smithsonian: skipped, no SI_API_KEY set (free at api.data.gov)')
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
                if name == 'smithsonian' and not os.environ.get('SI_API_KEY'):
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
                    file = folder / (f"{o['source'].lower()}-" + re.sub(r'[^A-Za-z0-9._-]', '_', str(o['id'])) + '.jpg')
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
    if rows and not a.dry:
        from collections import Counter
        by = Counter((r['row'], r['source']) for r in rows)
        srcs = sorted({s for _, s in by})
        print('\nCandidates by row and archive:')
        print('  ' + 'row'.ljust(11) + ''.join(s[:10].ljust(11) for s in srcs))
        for row in WANTED:
            print('  ' + row.ljust(11) + ''.join(str(by.get((row, s), 0)).ljust(11) for s in srcs))
    if problems:
        print(f'\n{len(problems)} searches or pictures failed (the rest are fine):')
        for p in problems[:30]:
            print('  -', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
