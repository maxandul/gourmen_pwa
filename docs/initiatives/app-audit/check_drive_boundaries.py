"""Drive boundaries with synthetic API objects, enforced SQLite FKs, no live files."""
from pathlib import Path
from unittest.mock import patch,MagicMock
import io,json,runpy
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from sqlalchemy import text
from httplib2 import Response
from googleapiclient.errors import HttpError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.document import Document
from backend.services.drive_storage import DriveStorageService as D,GOOGLE_FOLDER_MIME,MAX_FILE_SIZE_BYTES
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]
def err(status):return HttpError(Response({'status':str(status)}),b'{"error":{"message":"synthetic failure"}}')
def run(name,fn):
    with app.app_context():
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        assert db.session.execute(text('PRAGMA foreign_keys')).scalar()==1
        db.create_all()
        m=Member(vorname='Audit',nachname='Drive',email='boundary@example.com',passwort_hash='unused',role=Role.ADMIN)
        db.session.add(m);db.session.commit()
        d=Document(drive_file_id='audit-file',drive_parent_id='folder-old',uploader_id=m.id)
        db.session.add(d);db.session.commit()
        try:results.append({'case':name,'result':fn(m,d)})
        finally:db.session.remove();db.drop_all()

def folders(m,d):
    metas={'root':{'mimeType':GOOGLE_FOLDER_MIME},'inside':{'mimeType':GOOGLE_FOLDER_MIME,'parents':['root']},
           'nested':{'mimeType':GOOGLE_FOLDER_MIME,'parents':['inside']},'outside':{'mimeType':GOOGLE_FOLDER_MIME},
           'cycle':{'mimeType':GOOGLE_FOLDER_MIME,'parents':['cycle']},'trash':{'mimeType':GOOGLE_FOLDER_MIME,'trashed':True},
           'file':{'mimeType':'application/pdf','parents':['root']}}
    drive=MagicMock()
    drive.files.return_value.get.side_effect=lambda **kw:MagicMock(execute=lambda:metas[kw['fileId']])
    rows=[]
    with patch.object(D,'_build_drive',return_value=drive),patch.object(D,'_get_drive_id',return_value='root'):
        for name in metas:
            try:D.assert_is_folder_in_drive(name);error=None
            except Exception as exc:error=type(exc).__name__
            rows.append({'target':name,'error':error})
    return rows
run('folder_target_matrix',folders)

def validation(m,d):
    rows=[]
    for label,size,mime,name in [('valid',20,'application/pdf','Audit'),('empty',0,'application/pdf','Audit'),('large',MAX_FILE_SIZE_BYTES+1,'application/pdf','Audit'),('type',20,'application/x-executable','Audit'),('title',20,'application/pdf','')]:
        try:D.validate_upload(size,mime,name);error=None
        except Exception as exc:error=type(exc).__name__
        rows.append({'case':label,'error':error})
    return rows
run('upload_validation_matrix',validation)

def invalid_event(m,d):
    with patch.object(D,'assert_is_folder_in_drive'),patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_resolve_filename_collision',side_effect=lambda drive,folder,name:name),patch.object(D,'_drive_create_file',return_value={'id':'new-audit-file','parents':['root']}) as create,patch.object(D,'_safe_delete_drive_file') as cleanup:
        try:D.upload_document(io.BytesIO(b'audit'),'Audit','root',m,event_id=999999,original_filename='audit.pdf',mime_type='application/pdf');error=None
        except Exception as exc:error=type(exc).__name__
    return {'error':error,'remote_create_calls':create.call_count,'compensation_calls':cleanup.call_count,'document_count':Document.query.count()}
run('invalid_event_upload_compensation',invalid_event)

def sync_error(m,d):
    with patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_drive_file_meta',side_effect=err(403)):
        result=D.auto_sync_document(d,acting_member=m)
    return {'rows':Document.query.count(),'has_error_note':bool(result.note),'actions':result.actions}
run('sync_permission_error_preserves_cache',sync_error)

def restore(m,d):
    with patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_drive_file_meta',return_value={'trashed':True}):
        D.auto_sync_document(d,acting_member=m)
    removed=Document.query.count()
    drive=MagicMock();drive.files.return_value.list.return_value.execute.return_value={'files':[{'id':'audit-file','mimeType':'application/pdf','parents':['folder-old']}]}
    with patch.object(D,'_build_drive',return_value=drive),patch.object(D,'_get_drive_id',return_value='root'):
        D.admin_full_resync(m)
    return {'rows_while_trashed':removed,'rows_after_restore':Document.query.count(),'uploader_after_restore':Document.query.one().uploader_id}
run('trash_restore_loses_uploader',restore)

def partial(m,d):
    drive=MagicMock();drive.files.return_value.list.return_value.execute.side_effect=[{'nextPageToken':'next','files':[{'id':'new-file','mimeType':'application/pdf','parents':['root']}]},err(403)]
    with patch.object(D,'_build_drive',return_value=drive),patch.object(D,'_get_drive_id',return_value='root'):
        try:D.admin_full_resync(m);error=None
        except Exception as exc:error=type(exc).__name__
    db.session.rollback()
    return {'error':error,'cached_files':sorted(x.drive_file_id for x in Document.query.all())}
run('resync_second_page_failure',partial)

def drift(m,d):
    with patch.object(D,'_build_drive',return_value=MagicMock()),patch.object(D,'_drive_file_meta',return_value={'parents':['folder-new'],'trashed':False}):
        result=D.auto_sync_document(d,acting_member=m)
    return {'parent':d.drive_parent_id,'uploader_preserved':d.uploader_id==m.id,'actions':result.actions}
run('sync_parent_drift_preserves_uploader',drift)
(OUT/'DRIVE_BOUNDARY_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
