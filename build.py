# Builds the two versions of Supermenu from template.html and data.json:
#   supermenu.html  the hosted preview (no print button)
#   site/index.html the page for Netlify and ramos-saavedra.com (a whole document, with printing)
import pathlib
here=pathlib.Path(__file__).parent
t=(here/'template.html').read_text(encoding='utf-8')
d=(here/'data.json').read_text(encoding='utf-8').replace('</','<\\/')
page=t.replace('__DATA__',d)
(here/'supermenu.html').write_text(page,encoding='utf-8')
site=page.replace("const PRINT=false;","const PRINT=true;",1)
head,rest=site.split('<style>',1)
doc=('<!doctype html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
     '<meta name="description" content="Pick three objects. Get one thing to do.">\n'+head+'<style>\nbody{margin:0}img{max-width:100%}[hidden]{display:none!important}\n'+rest.replace('</style>','</style>\n</head>\n<body>',1)+'\n</body>\n</html>\n')
(here/'site').mkdir(exist_ok=True); (here/'site'/'index.html').write_text(doc,encoding='utf-8')
print('built', len(page)//1024,'KB')
