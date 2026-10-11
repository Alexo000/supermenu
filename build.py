# Builds Supermenu from its own files. Nothing here reads from the game folder.
#
#   source/objects.json     the objects: an op makes an object appear in the case
#   source/objects/*.webp   their pictures
#   source/tasks.json       the 30 tasks and the chain of operations each carries
#   source/operations.json  the operations, with their place on the map (xy) and family (cat)
#
# Writes:
#   site/index.html  the page for Netlify and ramos-saavedra.com (a whole document, with printing)
#   decoder.html     reads the code on a returned sheet; for Alejandro only, kept off the site
#   supermenu.html   the private preview on claude.ai (no printing)
#
# Run from anywhere:  python3 build.py
import base64, json, pathlib, sys

here = pathlib.Path(__file__).resolve().parent
src = here / 'source'

objects = json.loads((src / 'objects.json').read_text(encoding='utf-8'))['objects']
tasks = json.loads((src / 'tasks.json').read_text(encoding='utf-8'))['tasks']
ops = json.loads((src / 'operations.json').read_text(encoding='utf-8'))

problems = []
used = []
for o in sorted(objects, key=lambda o: o['id']):
    if not o.get('op'):
        continue
    if o['op'] not in ops:
        problems.append(f"object {o['id']}: operation {o['op']} is not in source/operations.json")
        continue
    pic = src / o['file']
    if not pic.exists():
        problems.append(f"object {o['id']}: picture {o['file']} is missing")
        continue
    used.append({'id': o['id'], 'op': o['op'],
                 'img': 'data:image/webp;base64,' + base64.b64encode(pic.read_bytes()).decode('ascii')})
for t in tasks:
    for c in t['chain']:
        if c not in ops:
            problems.append(f"task {t['n']}: operation {c} is not in source/operations.json")
if len(used) < 12:
    problems.append(f'only {len(used)} objects have an operation; the case needs at least 12')
# a code holds three objects and a task in four characters of base 31
if len(used) ** 3 * len(tasks) > 31 ** 4:
    problems.append(f'{len(used)} objects and {len(tasks)} tasks no longer fit in a four-character code: '
                    'time for SM2- codes (see codec.js)')
if problems:
    print('Not built:\n- ' + '\n- '.join(problems)); sys.exit(1)

needed = {o['op'] for o in used} | {c for t in tasks for c in t['chain']}
data = {'objects': used,
        'ops': {k: {'xy': ops[k]['xy'], 'cat': ops[k]['cat']} for k in sorted(needed)},
        'tasks': [{'n': t['n'], 'en': t['en'], 'es': t['es'], 'chain': t['chain']} for t in tasks]}
d = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')

codec = (here / 'codec.js').read_text(encoding='utf-8')
t = (here / 'template.html').read_text(encoding='utf-8').replace('/*__CODEC__*/', codec)
page = t.replace('__DATA__', d)
(here / 'supermenu.html').write_text(page, encoding='utf-8')


def document(html, extra_head=''):
    head, rest = html.split('<style>', 1)
    return ('<!doctype html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            + extra_head + head + '<style>\nbody{margin:0}img{max-width:100%}[hidden]{display:none!important}\n'
            + rest.replace('</style>', '</style>\n</head>\n<body>', 1) + '\n</body>\n</html>\n')


site = page.replace('const PRINT=false;', 'const PRINT=true;', 1)
(here / 'site').mkdir(exist_ok=True)
(here / 'site' / 'index.html').write_text(
    document(site, '<meta name="description" content="Pick three objects. Get one thing to do.">\n'), encoding='utf-8')

dec = ((here / 'decoder_template.html').read_text(encoding='utf-8')
       .replace('/*__CODEC__*/', codec).replace('__DATA__', d).replace('__SAMPLE__', 'SM-AAAA'))
(here / 'decoder.html').write_text(document(dec), encoding='utf-8')

print(f'built: {len(used)} objects in the case, {len(tasks)} tasks, page {len(page) // 1024} KB')
