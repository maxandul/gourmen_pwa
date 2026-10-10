"""Document route/service audit with synthetic remote responses only."""
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import runpy,json
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from itsdangerous import URLSafeTimedSerializer
from httplib2 import Response
from googleapiclient.errors import HttpError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.document import Document
from backend.models.event import Event,EventType,EventAudience
from backend.services.drive_storage import DriveStorageService as D,DriveError
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]

def client(m):
    g.pop('_login_user',None)
    c=app.test_client()
    with c.session_transaction() as s:s['_user_id']=str(m.id);s['_fresh']=True;s['csrf_token']='audit'
    return c

def token():return URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('audit')
def denied():return HttpError(Response({'status':'403'}),b'{"error":{"message":"synthetic permission failure"}}')

def run(name,fn):
    with app.app_context():
        app.config['DRIVE_FEATURE_ENABLED']=True
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'docs{i}@example.com',passwort_hash='unused') for i in range(2)]
        ms[0].role=Role.ADMIN
        db.session.add_all(ms);db.session.commit()
        d=Document(drive_file_id='audit-file',drive_parent_id='audit-folder',uploader_id=ms[1].id)
        db.session.add(d);db.session.commit()
        try:results.append({'case':name,'result':fn(ms,d)})
        finally:db.session.remove();db.drop_all()

def gates(ms,d):
    with patch.object(D,'rename_document') as rename:
        missing=client(ms[1]).post(f'/docs/file/{d.id}/rename',data={'title':'Audit'})
        app.config['DRIVE_FEATURE_ENABLED']=False
        disabled=client(ms[1]).post(f'/docs/file/{d.id}/rename',data={'title':'Audit','csrf_token':token()})
    return {'missing_csrf':missing.status_code,'feature_off':disabled.status_code,'service_calls':rename.call_count}
run('csrf_and_feature_guards',gates)

def delete_guards(ms,d):
    with patch.object(D,'permanently_delete_document') as delete,patch.object(D,'document_is_under_archive',return_value=False) as archived,patch.object(D,'fetch_drive_filename',return_value='audit.pdf'):
        member=client(ms[1]).post(f'/docs/file/{d.id}/delete',data={'csrf_token':token(),'confirm_filename':'audit.pdf'})
        active=client(ms[0]).post(f'/docs/file/{d.id}/delete',data={'csrf_token':token(),'confirm_filename':'audit.pdf'})
        archived.return_value=True
        wrong=client(ms[0]).post(f'/docs/file/{d.id}/delete',data={'csrf_token':token(),'confirm_filename':'wrong'})
    return {'member':member.status_code,'outside_archive':active.status_code,'wrong_name':wrong.status_code,'delete_calls':delete.call_count,'documents':Document.query.count()}
run('delete_role_archive_confirmation_guards',delete_guards)

def redirect(ms,d):
    with patch.object(D,'rename_document',side_effect=DriveError('synthetic')):
        r=client(ms[1]).post(f'/docs/file/{d.id}/rename',data={'csrf_token':token(),'title':'Audit','next':'https://example.invalid/audit'})
    return {'http':r.status_code,'location':r.headers.get('Location')}
run('rename_error_external_redirect',redirect)

def rename_failure(ms,d):
    drive=MagicMock();drive.files.return_value.update.return_value.execute.side_effect=denied()
    with patch.object(D,'_build_drive',return_value=drive),patch.object(D,'_drive_file_meta',return_value={'name':'audit.pdf','parents':['audit-folder']}),patch.object(D,'_resolve_filename_collision',side_effect=lambda drive,folder,name:name):
        try:r=client(ms[1]).post(f'/docs/file/{d.id}/rename',data={'csrf_token':token(),'title':'New'});error=None;status=r.status_code
        except Exception as exc:error=type(exc).__name__;status=None
    return {'http':status,'error':error,'documents':Document.query.count()}
run('remote_rename_http_error',rename_failure)

def detail_failure(ms,d):
    with patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_drive_file_meta',side_effect=denied()):
        try:r=client(ms[1]).get(f'/docs/file/{d.id}');error=None;status=r.status_code
        except Exception as exc:error=type(exc).__name__;status=None
    return {'http':status,'error':error,'documents':Document.query.count()}
run('detail_metadata_error_after_sync',detail_failure)

def move_failure(ms,d):
    with patch.object(D,'assert_is_folder_in_drive'),patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_drive_file_meta',return_value={'parents':['audit-folder']}),patch.object(D,'_move_drive_file',side_effect=DriveError('synthetic')):
        r=client(ms[1]).post(f'/docs/file/{d.id}/move',data={'csrf_token':token(),'new_parent_id':'other-folder'})
    return {'http':r.status_code,'parent_unchanged':d.drive_parent_id=='audit-folder'}
run('move_failure_preserves_db_parent',move_failure)

def events(ms,d):
    e=Event(organisator_id=ms[0].id,datum=datetime.now(),season=datetime.now().year,event_typ=EventType.VORSTANDSSITZUNG,audience=EventAudience.BOARD,restaurant='AUDIT_BOARD_DOCS')
    db.session.add(e);db.session.commit()
    with patch.object(D,'get_root_id',return_value='audit-root'),patch.object(D,'list_folder',return_value=SimpleNamespace(subfolders=[])):
        r=client(ms[1]).get('/docs/')
    return {'http':r.status_code,'board_event_label_exposed':'AUDIT_BOARD_DOCS' in r.get_data(as_text=True),'event_visible':e.is_visible_to(ms[1])}
run('docs_upload_event_choices_visibility',events)
(OUT/'DOCS_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
