"""Bounded GET smoke checks on synthetic in-memory data, never production."""
from pathlib import Path
import runpy
import json
import ast

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from tests.conftest import _seed_member_with_event
from backend.models.event import Event

app = create_app('testing')
assert app.config['TESTING'] and app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
assert 'billbro.index' in app.view_functions, 'Fallback app is not a valid audit target'
result = {'registered_routes': [], 'template_references': [], 'get_smoke': []}
for rule in app.url_map.iter_rules():
    result['registered_routes'].append({'endpoint': rule.endpoint, 'rule': str(rule), 'methods': sorted(rule.methods)})
for file in (ROOT / 'backend').rglob('*.py'):
    tree = ast.parse(file.read_text(encoding='utf-8-sig'))
    for call in ast.walk(tree):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'render_template':
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                name = call.args[0].value
                result['template_references'].append({'path': file.relative_to(ROOT).as_posix(), 'line': call.lineno,
                    'template': name, 'exists': (ROOT / 'templates' / name).is_file()})
with app.app_context():
    db.create_all()
    uid = _seed_member_with_event()
    eid = Event.query.first().id
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(uid)
        session['_fresh'] = True
    urls = ['/', '/ueber-uns', '/restaurants', '/dashboard/', '/events/', '/events/?tab=archiv',
            '/events/?tab=statistik', f'/events/{eid}', f'/events/{eid}?tab=billbro',
            '/ggl/', '/member/', '/member/profile', '/member/security',
            f'/billbro/?event_id={eid}', f'/billbro/{eid}/calculator', '/accounting/', '/health', '/health/db']
    for url in urls:
        try:
            response = client.get(url, follow_redirects=False)
            result['get_smoke'].append({'url': url, 'status': response.status_code,
                                       'location': response.headers.get('Location'),
                                       'html_bytes': len(response.data)})
        except Exception as exc:
            result['get_smoke'].append({'url': url, 'error_type': type(exc).__name__, 'message': str(exc)[:250]})
    db.session.remove()
    db.drop_all()
(OUT / 'RUNTIME_CHECKS.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'registered_route_count': len(result['registered_routes']),
    'missing_template_references': [r for r in result['template_references'] if not r['exists']],
    'get_smoke': result['get_smoke']}, indent=2, ensure_ascii=True))
