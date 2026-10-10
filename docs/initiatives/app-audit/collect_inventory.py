"""Read-only repository inventory; writes audit evidence beside this script.

No application imports, environment-file reads, database access or build steps.
Run from any directory with Python 3.11+; standard library only.
Search matches are inventory hints, never proof of dead code or defects.
"""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', *args], cwd=ROOT
    ).decode('utf-8')


def save_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


tracked = set(git('ls-files', '-z').split('\0')) - {''}
untracked = set(git('ls-files', '--others', '--exclude-standard', '-z').split('\0')) - {''}
paths = sorted(tracked | untracked)
files, routes, templates, css, docs = [], [], [], [], []
parse_errors = []
safe_roots = ('backend/', 'templates/', 'static/', 'scripts/', 'tests/', 'migrations/', 'docs/', '.cursor/')
text_exts = {'.py', '.html', '.css', '.js', '.md', '.mdc', '.txt', '.ini', '.sh'}
patterns = {
    'tabs': r'tabs__nav', 'filter': r'card--filter', 'actions': r'tool-strip__actions',
    'back': r'page-back', 'workflow': r'workflow|cleanup-step-nav',
    'form': r'<form\b', 'card': r'class=["\'][^"\']*\bcard\b',
    'chart': r'<canvas\b', 'dialog': r'<dialog\b', 'custom_modal': r'class=["\'][^"\']*\bmodal\b',
    'inline_style': r'\bstyle\s*=', 'style_block': r'<style\b',
    'inline_script': r'<script(?![^>]*\bsrc=)[^>]*>',
}
for rel in paths:
    if rel.startswith('docs/initiatives/app-audit/'):
        continue
    path = ROOT / rel
    if not path.is_file():
        continue
    # Inventory metadata for tracked files; never include sensitive file contents.
    generated = bool(re.search(r'\.[0-9a-f]{8}\.', rel)) or rel == 'static/css/main-v2.css'
    text = None
    if (rel.startswith(safe_roots) or '/' not in rel) and path.suffix in text_exts:
        if path.name not in {'build_logs.txt', 'vapid_public.txt'} and not path.name.startswith('.env'):
            text = path.read_text(encoding='utf-8-sig', errors='replace')
    row = {'path': rel, 'tracked': rel in tracked, 'bytes': path.stat().st_size,
           'lines': len(text.splitlines()) if text is not None else '',
           'generated_candidate': generated, 'review_status': 'inventoried_only'}
    files.append(row)
    if path.suffix in {'.md', '.mdc'}:
        docs.append({'path': rel, 'historical_path': '/_archive/' in rel,
                     'tracked': rel in tracked, 'validity_status': 'unverified'})
    if rel.startswith('templates/') and path.suffix == '.html':
        templates.append({'path': rel, 'lines': row['lines'],
                          **{key: len(re.findall(pat, text)) for key, pat in patterns.items()},
                          'code_review': 'pending', 'browser_review': 'pending'})
    if rel.startswith('static/') and path.suffix == '.css' and not generated:
        css.append({'path': rel, 'lines': row['lines'], 'bytes': row['bytes'],
                    'important': text.count('!important'),
                    'media_rules': len(re.findall(r'@media\b', text)),
                    'loaded_status': 'unverified'})
    if rel.startswith(('backend/', 'scripts/', 'tests/', 'migrations/')) and path.suffix == '.py':
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as exc:
            parse_errors.append({'path': rel, 'line': exc.lineno, 'reason': exc.msg})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = [ast.unparse(d) for d in node.decorator_list]
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                    continue
                if dec.func.attr not in {'route', 'get', 'post', 'put', 'patch', 'delete'}:
                    continue
                routes.append({'path': rel, 'line': node.lineno, 'function': node.name,
                               'route_declaration': ast.unparse(dec),
                               'decorators': ' | '.join(decorators),
                               'registration': 'unverified', 'review_status': 'pending'})

save_csv('FILE_INVENTORY.csv', files, list(files[0]))
save_csv('ROUTE_INVENTORY.csv', routes, list(routes[0]))
save_csv('TEMPLATE_MATRIX.csv', templates, list(templates[0]))
save_csv('CSS_INVENTORY.csv', css, list(css[0]))
save_csv('DOC_INVENTORY.csv', docs, list(docs[0]))

manifest = json.loads((ROOT / 'static/asset-manifest.json').read_text(encoding='utf-8'))
asset_checks = []
for source, target in manifest.items():
    src, dst = ROOT / source, ROOT / target
    repo_bytes = subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'show', f'HEAD:{target}'], cwd=ROOT
    ) if target in tracked else None
    asset_checks.append({'source': source, 'target': target,
                         'source_exists': src.is_file(), 'target_exists': dst.is_file(),
                         'same_content': src.read_bytes() == dst.read_bytes() if src.is_file() and dst.is_file() else False,
                         'filename_hash_valid': hashlib.sha256(dst.read_bytes()).hexdigest()[:8] in dst.name if dst.is_file() else False,
                         'git_blob_hash_valid': hashlib.sha256(repo_bytes).hexdigest()[:8] in dst.name if repo_bytes is not None else False})
save_csv('ASSET_CHECKS.csv', asset_checks, list(asset_checks[0]))
summary = {
    'commit': git('rev-parse', 'HEAD').strip(),
    'branch': git('branch', '--show-current').strip(),
    'scope': 'git tracked + nonignored untracked, excluding audit outputs; no ignored runtime/user data',
    'files': len(files), 'tracked_files': sum(r['tracked'] for r in files),
    'route_declarations': len(routes), 'templates': len(templates),
    'source_css_files': len(css), 'documents_and_rules': len(docs),
    'template_pattern_counts': {key: sum(r[key] > 0 for r in templates) for key in patterns},
    'python_parse_errors': parse_errors,
    'asset_check_failures': [r for r in asset_checks if not all(r[k] for k in ('source_exists', 'target_exists', 'same_content')) or not (r['filename_hash_valid'] or r['git_blob_hash_valid'])],
    'largest_source_files': sorted([r for r in files if r['lines'] != '' and not r['generated_candidate']], key=lambda r: r['lines'], reverse=True)[:15],
    'route_files': dict(Counter(r['path'] for r in routes)),
}
(OUT / 'INVENTORY_SUMMARY.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(summary, indent=2, ensure_ascii=True))
