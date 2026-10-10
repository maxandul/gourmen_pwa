"""Original lifecycle and audit methods against a stateful fake Drive and memory DB."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from copy import deepcopy
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
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

def probe(name, action, db_parent, remote_parent, target=None):
    with app.test_request_context('/__audit/lifecycle'):
        db.create_all()
        m = Member(vorname='Audit', nachname='Lifecycle', email='lifecycle@example.test', passwort_hash='unused')
        db.session.add(m); db.session.flush()
        d = Document(drive_file_id='file', drive_parent_id=db_parent, uploader_id=m.id)
        db.session.add(d); db.session.commit()
        did = d.id
        state = {key:dict(id=key, name=key, mimeType=GOOGLE_FOLDER_MIME, parents=parents)
                 for key, parents in [('root',[]),('source',['root']),('target',['root']),
                                      ('archive',['root']),('archive-child',['archive'])]}
        state['file'] = dict(id='file', name='Audit.pdf', mimeType='application/pdf', parents=[remote_parent])
        updates = []
        drive = MagicMock()
        drive.files.return_value.get.side_effect = lambda **kw: MagicMock(execute=lambda: deepcopy(state[kw['fileId']]))
        drive.files.return_value.list.return_value.execute.return_value = {'files':[]}
        def update(**kw):
            def execute():
                updates.append(deepcopy(kw))
                obj = state[kw['fileId']]
                obj.update(kw.get('body', {}))
                if 'addParents' in kw: obj['parents'] = [kw['addParents']]
                return deepcopy(obj)
            return MagicMock(execute=execute)
        drive.files.return_value.update.side_effect = update
        with patch.object(D, '_build_drive', return_value=drive):
            if action == 'rename': D.rename_document(d, 'Audit-Neu', m)
            elif action == 'move': D.move_document(d, target, m)
            elif action == 'archive': D.archive_document(d, m)
            elif action == 'restore': D.restore_document(d, target, m)
            db.session.expire_all()
            fresh = db.session.get(Document, did)
            result = dict(case=name, db_parent=fresh.drive_parent_id,
                          remote_parent=state['file']['parents'][0], remote_name=state['file']['name'],
                          update_count=len(updates), remains_in_archive=D.document_is_under_archive(fresh),
                          audit=[{'action':e.action.value, 'extra':e.extra_json} for e in AuditEvent.query.all()])
        results.append(result)
        db.session.remove(); db.drop_all()
        return result

renamed = probe('rename_success','rename','source','source')
assert renamed['remote_name'] == 'Audit-Neu.pdf' and renamed['audit'][0]['action'] == 'DOCUMENT_RENAMED'
for name, action, parent, target, expected in [
    ('move_success','move','source','target','target'),
    ('archive_success','archive','source',None,'archive'),
    ('restore_success','restore','archive','target','target')]:
    r = probe(name,action,parent,parent,target)
    assert r['db_parent'] == r['remote_parent'] == expected and r['update_count'] == 1 and len(r['audit']) == 1
same = probe('same_parent_noop','move','target','target','target')
assert same['update_count'] == 0 and same['audit'] == []
drift = probe('same_remote_target_stale_db','move','source','target','target')
assert drift['db_parent'] == 'source' and drift['remote_parent'] == 'target' and drift['update_count'] == 0
for destination in ('archive','archive-child'):
    r = probe('restore_into_' + destination,'restore','archive','archive',destination)
    assert r['remains_in_archive'] and r['audit'][0]['action'] == 'DOCUMENT_RESTORED'
output = dict(date='2026-09-21', groups=8, results=results,
              limits='Original lifecycle, target validation, archive ancestry, collision-check logic and audit writer. Only Drive builder replaced by stateful fake transport. SQLite in memory, successful DB commits; no production, browser, real Drive or partial DB/API failures.')
(OUT / 'DOCS_LIFECYCLE_CHECKS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, ensure_ascii=True, indent=2))
