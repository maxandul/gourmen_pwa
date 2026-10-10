"""Audit of original action routes; all external mutations replaced by mocks."""
from pathlib import Path
from unittest.mock import patch
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from itsdangerous import URLSafeTimedSerializer
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.document import Document
from backend.services.drive_storage import DriveStorageService as D, DriveError

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
app.config.update(DRIVE_FEATURE_ENABLED=True, DRIVE_ARCHIVE_FOLDER_ID='audit-archive')
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1, vorname='Audit', nachname='Aktion',
                         email='audit-action@example.test', passwort_hash='unused'))
    db.session.flush()
    db.session.add(Document(id=1, drive_file_id='audit-file', drive_parent_id='audit-source', uploader_id=1))
    db.session.commit()

results = []
actions = [('rename','rename_document',{'title':'Audit-Neuer-Name'}),
           ('move','move_document',{'new_parent_id':'audit-target'}),
           ('archive','archive_document',{}),
           ('restore','restore_document',{'target_folder_id':'audit-target'})]

def probe(action, method, payload, outcome):
    c = app.test_client()
    with c.session_transaction() as session:
        session.update(_user_id='1', _fresh=True, csrf_token='audit')
    token = URLSafeTimedSerializer(app.secret_key, salt='wtf-csrf-token').dumps('audit')
    data = dict(payload, csrf_token=token, next='/docs/folder/audit-source')
    with patch.object(D, method, side_effect=DriveError('Synthetic action failure') if outcome == 'error' else None) as service:
        response = c.post(f'/docs/file/1/{action}', data=data)
    with c.session_transaction() as session:
        flashes = session.get('_flashes', [])
        saved_draft_keys = [key for key in session if any(x in key for x in ('title','parent','target','draft'))]
    assert response.status_code == 302
    expected = '/docs/folder/audit-source'
    if outcome == 'success' and action == 'archive': expected = '/docs/folder/audit-archive'
    if outcome == 'success' and action == 'restore': expected = '/docs/folder/audit-target'
    assert response.location == expected
    assert service.call_count == (0 if outcome == 'missing_target' else 1)
    assert flashes and flashes[-1][0] == ('success' if outcome == 'success' else 'error')
    results.append(dict(action=action, outcome=outcome, status=302, redirect=response.location,
                        service_calls=service.call_count, flashes=flashes,
                        saved_draft_keys=saved_draft_keys))

for action, method, payload in actions:
    probe(action, method, payload, 'success')
    probe(action, method, payload, 'error')
for action, method in [('move','move_document'),('restore','restore_document')]:
    probe(action, method, {}, 'missing_target')
output = dict(date='2026-09-21', groups=10, results=results,
              limits='Original routes with signed manual CSRF tokens; services mocked entirely. No real rename, move, archive, restore or DB mutation performed by action mocks. Success redirects are route contracts, not proof of successful storage operations. No browser or focus test.')
(OUT / 'DOCS_ACTION_CHECKS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, ensure_ascii=True, indent=2))
