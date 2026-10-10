"""Structural survey of every template, not a full semantic/visual review.

Parses literal HTML tags in Jinja source; conditional branches remain unresolved.
Exact CSS class tokens avoid counting docs-action-modal as generic .modal and
hamburg-tabs__nav as standard .tabs__nav. Read-only application source access.
"""
from pathlib import Path
from html.parser import HTMLParser
import re
import csv
import json
import difflib

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append({'tag': tag, 'line': self.getpos()[0], 'attrs': dict(attrs)})


rows, detail = [], {}
for file in sorted((ROOT / 'templates').rglob('*.html')):
    source = file.read_text(encoding='utf-8-sig')
    parser = Tags()
    parser.feed(source)
    tags = parser.tags
    has_class = lambda tag, cls: cls in (tag['attrs'].get('class') or '').split()
    rel = file.relative_to(ROOT).as_posix()
    selected = [t for t in tags if t['tag'] in ('details', 'dialog', 'form', 'canvas') or
                has_class(t, 'tabs__nav') or has_class(t, 'hamburg-tabs__nav') or has_class(t, 'modal')]
    detail[rel] = selected
    row = {
        'path': rel,
        'category': 'email' if '/emails/' in rel else 'partial' if file.name.startswith('_') else 'page_or_layout',
        'standard_tab_nav': sum(has_class(t, 'tabs__nav') for t in tags),
        'custom_tab_nav': sum(has_class(t, 'hamburg-tabs__nav') for t in tags),
        'details': sum(t['tag'] == 'details' for t in tags),
        'native_dialog': sum(t['tag'] == 'dialog' for t in tags),
        'custom_modal': sum(has_class(t, 'modal') for t in tags),
        'filter_surface': sum(has_class(t, 'card--filter') for t in tags),
        'collapsible_card': sum(has_class(t, 'card--collapsible') for t in tags),
        'forms': sum(t['tag'] == 'form' for t in tags),
        'canvas': sum(t['tag'] == 'canvas' for t in tags),
        'literal_style_attributes': sum('style' in t['attrs'] for t in tags),
        'local_lucide_macro': bool(re.search(r'{%\s*macro\s+lucide_icon', source)),
        'uses_shared_form_macros': 'partials/_form_macros.html' in source,
        'bindDisclosure': 'function bindDisclosure(' in source,
        'source_review_status': 'structural_survey_only',
        'workflow_review_status': 'pending',
    }
    rows.append(row)
with (OUT / 'UI_PATTERN_SURVEY.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(OUT / 'UI_PATTERN_LOCATIONS.json').write_text(json.dumps(detail, indent=2, ensure_ascii=False), encoding='utf-8')
summary = {'templates_surveyed': len(rows), 'files_with_pattern': {
    k: sum(bool(r[k]) for r in rows) for k in list(rows[0])[2:-2]},
    'standard_tab_files': [r['path'] for r in rows if r['standard_tab_nav']],
    'custom_modal_files': [r['path'] for r in rows if r['custom_modal']],
    'native_dialog_files': [r['path'] for r in rows if r['native_dialog']],
    'filter_files': [r['path'] for r in rows if r['filter_surface']]}
for left, right in [('templates/admin/create_event.html', 'templates/events/edit.html')]:
    a, b = [(ROOT / p).read_text(encoding='utf-8-sig').splitlines() for p in (left, right)]
    matching = sum(block.size for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    summary['event_form_similarity'] = {'left': left, 'right': right, 'identical_lines_in_matching_blocks': matching,
                                       'left_lines': len(a), 'right_lines': len(b)}
(OUT / 'UI_SURVEY_SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(summary, indent=2))
