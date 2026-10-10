"""Synthetic commit/audit failures after simulated Drive success; no external I/O."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from copy import deepcopy
import runpy
import json

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.document import Document
from backend.models.audit_event import AuditEvent
from backend.services.drive_storage import DriveStorageService as D, GOOGLE_FOLDER_MIME

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
app.config.update(GOOGLE_DRIVE_ID='root', DRIVE_ARCHIVE_FOLDER_ID='archive')
results = []

def probe(action, audit_failure=False):
    with app.test_request_context('/__audit/failure'):
        db.create_all()
        m = Member(id=1, vorname='Audit', nachname='Failure', email='failure@example.test', passwort_hash='unused')
        db.session.add(m); db.session.flush()
        old = 'archive' if action == 'restore' else 'source'
        d = Document(id=1, drive_file_id='file', drive_parent_id=old, uploader_id=1)
        db.session.add(d); db.session.commit()
        state = {k:dict(id=k, name=k, mimeType=GOOGLE_FOLDER_MIME, parents=['root'])
                 for k in ('source','target','archive')}
        state['root'] = dict(id='root', parents=[], mimeType=GOOGLE_FOLDER_MIME)
        state['file'] = dict(id='file', name='Audit.pdf', parents=[old], mimeType='application/pdf')
        updates = []
        drive = MagicMock()
        drive.files.return_value.get.side_effect = lambda **kw: MagicMock(execute=lambda: deepcopy(state[kw['fileId']]))
        drive.files.return_value.list.return_value.execute.return_value = {'files':[]}
        def update(**kw):
            def execute():
                updates.append(deepcopy(kw))
                state['file'].update(kw.get('body', {}))
                if 'addParents' in kw: state['file']['parents'] = [kw['addParents']]
                return deepcopy(state['file'])
            return MagicMock(execute=execute)
        drive.files.return_value.update.side_effect = update
        def invoke():
            if action == 'rename': D.rename_document(d, 'Audit-Neu', m)
            elif action == 'move': D.move_document(d, 'target', m)
            elif action == 'archive': D.archive_document(d, m)
            else: D.restore_document(d, 'target', m)
        def fail(*args):
            raise OperationalError('synthetic audit insert' if audit_failure else 'synthetic commit', {}, Exception('audit-only failure'))
        with patch.object(D, '_build_drive', return_value=drive):
            if audit_failure: event.listen(AuditEvent, 'before_insert', fail)
            try:
                if audit_failure:
                    invoke()
                    error = None
                else:
                    with patch.object(db.session, 'commit', side_effect=fail): invoke()
                    error = None
            except Exception as exc:
                error = type(exc).__name__
            finally:
                if audit_failure: event.remove(AuditEvent, 'before_insert', fail)
            try:
                db.session.get(Document, 1, populate_existing=True)
                followup_error = None
            except Exception as exc:
                followup_error = type(exc).__name__
            db.session.rollback()
            d = db.session.get(Document, 1)
            before_retry = dict(db_parent=d.drive_parent_id, remote_parent=state['file']['parents'][0],
                                remote_name=state['file']['name'], audit_count=AuditEvent.query.count(), updates=len(updates))
            if not audit_failure: invoke()
            db.session.expire_all()
            result = dict(action=action, failure='audit_insert' if audit_failure else 'document_commit',
                          propagated_error=error, query_before_rollback_error=followup_error,
                          before_retry=before_retry, after_retry_db_parent=db.session.get(Document, 1).drive_parent_id,
                          total_updates=len(updates), audit_actions=[e.action.value for e in AuditEvent.query.all()])
        results.append(result)
        db.session.remove(); db.drop_all()
        return result

for action in ('rename','move','archive','restore'):
    r = probe(action)
    assert r['propagated_error'] == 'OperationalError' and r['before_retry']['updates'] == 1
    if action == 'rename': assert r['before_retry']['remote_name'] == 'Audit-Neu.pdf'
    else:
        assert r['before_retry']['db_parent'] != r['before_retry']['remote_parent']
        if action == 'move': assert r['after_retry_db_parent'] == 'source' and not r['audit_actions']
        else: assert r['after_retry_db_parent'] == r['before_retry']['db_parent'] and len(r['audit_actions']) == 1
r = probe('move', audit_failure=True)
assert r['propagated_error'] is None and r['query_before_rollback_error'] == 'PendingRollbackError'
assert r['before_retry']['db_parent'] == r['before_retry']['remote_parent'] == 'target' and not r['audit_actions']
output = dict(date='2026-09-21', groups=5, results=results,
              limits='Original lifecycle methods, fake Drive transport, SQLite memory. Commit failure injected before commit call; audit failure injected in real ORM flush. Explicit rollback before recovery. No route/browser/production test. Rename collision query always empty in fake, so retry does not validate collision idempotency. Audit failure case performs no second action despite after_retry field names.')
(OUT / 'DOCS_PARTIAL_FAILURE_CHECKS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, indent=2))
