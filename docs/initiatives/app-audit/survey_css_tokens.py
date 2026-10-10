"""Textual token cross-reference for active CSS sources; not CSS evaluation."""
from pathlib import Path
import json,re
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
paths=[ROOT/'static/css/v2'/n for n in ['tokens.css','base.css','layout.css','components.css']]+[ROOT/'static/css/public.css']
definitions=set()
uses=[]
for p in paths:
    text=p.read_text(encoding='utf-8')
    text=re.sub(r'/\*.*?\*/',lambda m:'\n'*m[0].count('\n'),text,flags=re.S)
    definitions.update(re.findall(r'(--[\w-]+)\s*:',text))
    for m in re.finditer(r'var\(\s*(--[\w-]+)\s*([,)])',text):
        uses.append({'token':m[1],'fallback':m[2]==',','path':p.relative_to(ROOT).as_posix(),'line':text.count('\n',0,m.start())+1})
missing=[u for u in uses if u['token'] not in definitions]
result={'scope':[p.relative_to(ROOT).as_posix() for p in paths], 'definitions':len(definitions),
        'unresolved_in_css_sources':missing,
        'limitations':'Text inventory only; definitions may be injected by JS or templates; fallback flag does not evaluate nested var(). No computed-style or deletion proof.'}
(OUT/'CSS_TOKEN_CHECKS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
