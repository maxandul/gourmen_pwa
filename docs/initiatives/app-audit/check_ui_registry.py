"""Read-only lexical registry map; hits are evidence locations, not runtime coverage."""
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
tracked = subprocess.check_output(
    ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'ls-files',
     'templates', 'static/css', 'static/js'], cwd=ROOT, text=True).splitlines()
sources = {}
for name in tracked:
    p = Path(name)
    if p.suffix not in {'.html', '.css', '.js'}:
        continue
    if re.search(r'\.[a-f0-9]{8}\.', name) or p.name == 'main-v2.css':
        continue
    sources[name] = (ROOT / name).read_text(encoding='utf-8').splitlines()

rows = []
section = ''
inside = False
for number, line in enumerate((ROOT / 'docs/UI.md').read_text(encoding='utf-8').splitlines(), 1):
    if line.startswith('## 5.'):
        inside = True
    elif line.startswith('## 6.'):
        inside = False
    if not inside:
        continue
    if line.startswith('#'):
        section = line.lstrip('# ')
    if not line.startswith('|') or re.match(r'^\|[- ]+\|', line):
        continue
    cells = [c.strip() for c in line.strip('|').split('|')]
    if cells[0] in {'Klasse', 'Bestandteil'}:
        continue
    literals = re.findall(r'`([^`]+)`', line)
    tokens = set()
    bases = re.findall(r'(?<![\w/])\.([a-z][a-z0-9_-]+)(\*)?', cells[0])
    for token, wildcard in bases:
        tokens.add(token + wildcard)
    blocks = {t.split('__')[0].split('--')[0] for t, _ in bases}
    for literal in literals:
        if re.fullmatch(r'\.?[a-z][a-z0-9_-]+\*?', literal) and '-' in literal:
            tokens.add(literal.lstrip('.'))
        elif re.fullmatch(r'__[a-z0-9_-]+\*?', literal) and len(blocks) == 1:
            tokens.add(next(iter(blocks)) + literal)
        elif (re.fullmatch(r'--[a-z0-9_-]+', literal) and len(bases) == 1
              and len(cells) == 3 and f'`{literal}`' in cells[1]):
            tokens.add(bases[0][0] + literal)
    evidence = {}
    for token in sorted(tokens):
        pattern = re.compile(r'(?<![a-zA-Z0-9_-])' + re.escape(token.rstrip('*')) +
                             (r'[a-zA-Z0-9_-]*' if token.endswith('*') else r'(?![a-zA-Z0-9_-])'))
        hits = []
        for name, lines in sources.items():
            for n, source in enumerate(lines, 1):
                if pattern.search(source):
                    hits.append({'path': name, 'line': n, 'text': source.strip()})
        evidence[token] = hits
    rows.append({'id': f'UIR-{len(rows)+1:03}', 'doc_line': number,
                 'section': section, 'row': line, 'tokens': evidence,
                 'review': 'lexical_map_only'})

result = {'baseline': subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}',
          'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
          'method': 'Every table data row in section 5; literal tokens and unambiguous BEM shorthand. '
          'Hits can be comments, CSS, selectors or markup; not definitions/use proof. '
          'No dynamic concatenation resolution. Non-class rows and ambiguous shorthand require manual review. '
          'Tracked source files only; hashed copies and main-v2 bundle excluded.',
          'source_files': len(sources), 'row_count': len(rows), 'rows': rows}
(OUT / 'UI_REGISTRY_LOCATIONS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
with (OUT / 'UI_REGISTRY_REVIEW.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'doc_line', 'section', 'row', 'tokens', 'tokens_without_hits', 'review'])
    for row in rows:
        writer.writerow([row['id'], row['doc_line'], row['section'], row['row'],
                         '; '.join(row['tokens']), '; '.join(t for t,h in row['tokens'].items() if not h), row['review']])
print(json.dumps({'rows': len(rows), 'sources': len(sources),
                  'rows_without_any_hit': [r['id'] for r in rows if r['tokens'] and not any(r['tokens'].values())]}))
