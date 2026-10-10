"""Literal template class families absent by name from the UI registry: candidates only."""
import csv
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
paths = subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}',
                                 'ls-files', 'templates'], cwd=ROOT, text=True).splitlines()
doc = (ROOT / 'docs/UI.md').read_text(encoding='utf-8').split('## 5. Component Registry')[1].split('## 6.')[0]
families = defaultdict(list)
for path in paths:
    if not path.endswith('.html'):
        continue
    source = (ROOT / path).read_text(encoding='utf-8')
    # Jinja expressions are masked first, preserving line numbers. Dynamically emitted
    # attributes/classes and macro argument strings are intentionally not resolved.
    masked = re.sub(r'{{.*?}}|{%.*?%}|{#.*?#}', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), source, flags=re.S)
    for match in re.finditer(r'\bclass\s*=\s*([\'"])(.*?)\1', masked, re.S):
        line = masked.count('\n', 0, match.start()) + 1
        for token in match[2].split():
            if not re.fullmatch(r'[a-z][a-z0-9_-]*', token):
                continue
            block = token.split('__')[0].split('--')[0]
            if not re.search(r'(?<![a-z0-9_-])' + re.escape(block) + r'(?![a-z0-9_-])', doc):
                families[block].append({'class': token, 'path': path, 'line': line})
result = {'method': 'Literal class attributes in tracked templates, Jinja masked. Missing block name in UI.md section 5 is a candidate, not proof of missing CSS or reachable runtime use. Macro strings, JS generation, assembled tokens and HTML comments need manual review.',
          'families': dict(sorted(families.items()))}
(OUT / 'UI_REGISTRY_REVERSE.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
with (OUT / 'UI_REGISTRY_REVERSE.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['family', 'template_count', 'classes', 'sample', 'status'])
    for block, hits in sorted(families.items()):
        w.writerow([block, len({h['path'] for h in hits}), '; '.join(sorted({h['class'] for h in hits})),
                    f"{hits[0]['path']}:{hits[0]['line']}", 'candidate_only'])
print(json.dumps({'candidate_families': len(families), 'largest': sorted(
    [(b, len({h['path'] for h in hs})) for b, hs in families.items()], key=lambda x: -x[1])[:25]}))
