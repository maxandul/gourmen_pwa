"""Read-only asset provenance survey plus actual rendered HTML asset lists."""
from pathlib import Path
from html.parser import HTMLParser
import json,re,runpy
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'

class Assets(HTMLParser):
    def __init__(self):super().__init__();self.assets=[];self.inline_scripts=0;self.inline_styles=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script':
            if a.get('src'):self.assets.append({'kind':'script','url':a['src'],'defer':'defer' in a})
            else:self.inline_scripts+=1
        if tag=='link' and a.get('rel')=='stylesheet':self.assets.append({'kind':'css','url':a.get('href')})
        if tag=='style':self.inline_styles+=1

rendered=[]
with app.app_context():
    db.create_all()
    for url in ['/','/auth/login','/restaurants','/ueber-uns']:
        r=app.test_client().get(url);parser=Assets();parser.feed(r.get_data(as_text=True))
        local=set()
        for item in parser.assets:
            path=item['url'].split('?')[0]
            if path.startswith('/static/') and (ROOT/path.lstrip('/')).is_file():local.add(path)
        rendered.append({'page':url,'http':r.status_code,'assets':parser.assets,
                         'inline_scripts':parser.inline_scripts,'inline_styles':parser.inline_styles,
                         'local_uncompressed_bytes':sum((ROOT/p.lstrip('/')).stat().st_size for p in local)})
    db.session.remove();db.drop_all()

manifest=json.loads((ROOT/'static/asset-manifest.json').read_text())
runtime_files=list((ROOT/'templates').rglob('*.html'))+list((ROOT/'backend').rglob('*.py'))+[ROOT/'static/sw.js']
runtime_text={p.relative_to(ROOT).as_posix():p.read_text(encoding='utf-8-sig') for p in runtime_files}
assets=[]
asset_paths=sorted(list((ROOT/'static/css').rglob('*.css'))+list((ROOT/'static/js').rglob('*.js')))
asset_text={p.relative_to(ROOT).as_posix():p.read_text(encoding='utf-8-sig') for p in asset_paths}
for p in asset_paths:
    rel=p.relative_to(ROOT).as_posix();short=rel.removeprefix('static/')
    refs=[f for f,t in runtime_text.items() if short in t]
    assets.append({'path':rel,'bytes':p.stat().st_size,'fingerprinted':bool(re.search(r'\.[0-9a-f]{8}\.',p.name)),
                   'manifest_source':rel in manifest,'manifest_target':rel in manifest.values(),'literal_runtime_references':refs,
                   'literal_asset_mentions':[f for f,t in asset_text.items() if f!=rel and (short in t or p.name in t)]})

builder=runpy.run_path(str(ROOT/'scripts/build_css.py'),run_name='audit_build_definition')
expected=builder['build']()
bundle=(ROOT/'static/css/main-v2.css').read_text(encoding='utf-8')
hashed=(ROOT/manifest['static/css/main-v2.css']).read_text(encoding='utf-8')
css=[]
for rel in ['static/css/v2/tokens.css','static/css/v2/base.css','static/css/v2/layout.css','static/css/v2/components.css','static/css/public.css']:
    txt=(ROOT/rel).read_text(encoding='utf-8');clean=re.sub(r'/\*.*?\*/','',txt,flags=re.S)
    css.append({'path':rel,'lines':len(txt.splitlines()),'bytes':(ROOT/rel).stat().st_size,
                'important_occurrences':len(re.findall(r'!important\b',clean)),
                'media_occurrences':len(re.findall(r'@media\b',clean))})
result={'rendered_pages':rendered,'assets':assets,'css_source_metrics':css,
        'controller_hook_checks':{hook:[f for f,t in runtime_text.items() if hook in t]
                                  for hook in ['data-accordion','data-search','new Accordion','new InstantSearch','initAccordions','initSearchFields']},
        'build_sources':['static/css/'+p for p in builder['SOURCES']],
        'normalized_build_matches_bundle':expected==bundle,'normalized_build_matches_active_hash':expected==hashed,
        'limitations':['Literal references are not a complete dependency graph. No deletion clearance.',
                      'Uncompressed bytes on disk are not network transfer or load-time measurements.',
                      'Only four public/login pages rendered; no browser interactions executed.']}
(OUT/'FRONTEND_ASSET_CHECKS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'asset_count':len(assets),'css':css,'bundle_matches':expected==bundle,'hash_matches':expected==hashed,
                  'pages':[{'page':p['page'],'asset_count':len(p['assets']),'bytes':p['local_uncompressed_bytes']} for p in rendered],
                  'no_direct_ref_nonhashed':[a['path'] for a in assets if not a['literal_runtime_references'] and not a['fingerprinted']]},indent=2))
