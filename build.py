# Builds Supermenu from its own files. Nothing here reads from the game folder.
#
#   source/objects.json     the objects: an op makes an object appear (in the case and the full view)
#   source/objects/*.webp   their pictures
#   source/tasks.json       the tasks and the chain of operations each carries
#   source/operations.json  the operations, with their place on the map (xy) and family (cat)
#   source/codes.json       code versions: which objects and tasks each version of the sheet code counts.
#                           When the objects or tasks change, a new version is added here by itself,
#                           so codes on sheets already printed keep reading correctly.
#
# Writes:
#   site/index.html  the page for Netlify and ramos-saavedra.com (a whole document, with printing)
#   decoder.html     reads the codes on returned sheets; for Alejandro only, kept off the site
#   supermenu.html   the private preview on claude.ai (no printing)
#
# Run from anywhere:  python3 build.py
import base64, json, math, pathlib, sys

here = pathlib.Path(__file__).resolve().parent
src = here / 'source'

objects = json.loads((src / 'objects.json').read_text(encoding='utf-8'))['objects']
tasks = json.loads((src / 'tasks.json').read_text(encoding='utf-8'))['tasks']
ops = json.loads((src / 'operations.json').read_text(encoding='utf-8'))
codes_path = src / 'codes.json'
codes = json.loads(codes_path.read_text(encoding='utf-8'))
by_id = {o['id']: o for o in objects}

problems = []


def picture(o):
    pic = src / o['file']
    if not pic.exists():
        problems.append(f"object {o['id']}: picture {o['file']} is missing")
        return ''
    return 'data:image/webp;base64,' + base64.b64encode(pic.read_bytes()).decode('ascii')


used = []
for o in sorted(objects, key=lambda o: o['id']):
    if not o.get('op'):
        continue
    if o.get('excluded'):
        problems.append(f"object {o['id']} has an operation but is marked excluded")
        continue
    if o['op'] not in ops:
        problems.append(f"object {o['id']}: operation {o['op']} is not in source/operations.json")
        continue
    used.append({'id': o['id'], 'op': o['op'], 'img': picture(o)})
for t in tasks:
    for c in t['chain']:
        if c not in ops:
            problems.append(f"task {t['n']}: operation {c} is not in source/operations.json")
if len(used) < 12:
    problems.append(f'only {len(used)} objects have an operation; the case needs at least 12')

# code versions: the newest must count exactly the objects and tasks in use now
cur_objects = [o['id'] for o in used]
cur_tasks = sorted(t['n'] for t in tasks)
last = codes['versions'][-1]
if last['objects'] != cur_objects or last['tasks'] != cur_tasks:
    n = len(codes['versions']) + 1
    space = math.comb(len(cur_objects), 3) * len(cur_tasks)
    length = 1
    while 31 ** length < space:
        length += 1
    new = {'prefix': f'SM{n}-', 'objects': cur_objects, 'tasks': cur_tasks, 'ordered': False, 'length': length}
    codes['versions'].append(new)
    codes_path.write_text(json.dumps(codes, indent=1) + '\n', encoding='utf-8')
    print(f"The objects or tasks changed, so new sheets now get {new['prefix']} codes "
          f"({length} characters). Older codes still read. Recorded in source/codes.json.")

# objects that old codes name but that are no longer in the case: kept for reading old sheets
named = {i for v in codes['versions'] for i in v['objects']}
archive = []
for i in sorted(named - set(cur_objects)):
    o = by_id.get(i)
    if o is None:
        problems.append(f'object {i} is named by an old code version but is missing from source/objects.json')
        continue
    archive.append({'id': i, 'op': o.get('op') if o.get('op') in ops else None, 'img': picture(o)})

if problems:
    print('Not built:\n- ' + '\n- '.join(problems)); sys.exit(1)

needed = {o['op'] for o in used} | {c for t in tasks for c in t['chain']} | {o['op'] for o in archive if o['op']}
data = {'objects': used, 'archive': archive,
        'ops': {k: {'xy': ops[k]['xy'], 'cat': ops[k]['cat']} for k in sorted(needed)},
        'tasks': [{'n': t['n'], 'en': t['en'], 'es': t['es'], 'chain': t['chain']} for t in tasks]}
d = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
versions = json.dumps([{k: v[k] for k in ('prefix', 'objects', 'tasks', 'ordered', 'length')} for v in codes['versions']],
                      separators=(',', ':'))

codec = (here / 'codec.js').read_text(encoding='utf-8').replace('/*__CODES__*/[]', versions)
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

print(f"built: {len(used)} objects, {len(tasks)} tasks, codes {codes['versions'][-1]['prefix']}, "
      f"page {len(page) // 1024} KB")
