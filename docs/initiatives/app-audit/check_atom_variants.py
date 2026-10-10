"""Lexical variant inventory; evidence aid, not a CSS parser or browser test."""
import json
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
css_paths = [p for p in (ROOT / 'static/css/v2').glob('*.css')
             if not re.search(r'\.[0-9a-f]{8}\.css$', p.name)]
css = '\n'.join(p.read_text(encoding='utf-8') for p in css_paths)
parser = argparse.ArgumentParser()
parser.add_argument('--structural', action='store_true')
args = parser.parse_args()
families = ('card', 'card-section', 'form-field', 'form-actions', 'data-table', 'info-row') if args.structural else ('btn', 'alert', 'empty-state')
results = {}
for family in families:
    pattern = family + r'(?:__|--)[a-zA-Z0-9_-]+'
    definitions = set(re.findall(r'\.(' + pattern + ')', css))
    uses = {}
    paths = list((ROOT / 'templates').rglob('*.html')) + list((ROOT / 'static/js/v2').glob('*.js'))
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            for token in set(re.findall(r'(?<![\w-])(' + pattern + ')', line)):
                uses.setdefault(token, []).append(f'{path.relative_to(ROOT).as_posix()}:{line_number}')
    results[family] = {
        'defined': sorted(definitions), 'lexical_uses_including_comments': dict(sorted(uses.items())),
        'used_without_v2_definition': sorted(set(uses) - definitions),
        'defined_without_scanned_use': sorted(definitions - set(uses)),
    }
filename = 'STRUCTURAL_VARIANTS.json' if args.structural else 'ATOM_VARIANTS.json'
(OUT / filename).write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
for family, result in results.items():
    print(family, 'missing:', result['used_without_v2_definition'],
          'no lexical consumer:', result['defined_without_scanned_use'])
