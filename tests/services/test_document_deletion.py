"""Synthetic trash journal: forbidden references, uncertain I/O and failed commits."""
from unittest.mock import Mock
import pytest
from sqlalchemy.exc import SQLAlchemyError
from backend.extensions import db
from backend.models.document import Document
from backend.models.document_policy import DocumentPolicy
from backend.models.document_deletion import DocumentDeletionRequest
from backend.models.member import Member
from backend.models.accounting import Receipt
from backend.models.audit_event import AuditEvent, AuditAction
from backend.services.drive_storage import DriveStorageService as Drive, DriveValidationError, DriveError
from tests.routes.test_document_access import document_case
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def deletion_case(app,document_case,monkeypatch):
    members,docs=document_case
    drive=Mock()
    monkeypatch.setattr(Drive,'_build_drive',lambda:drive)
    monkeypatch.setattr(Drive,'_drive_file_meta',lambda *args:{'name':'test.pdf','parents':['archive']})
    monkeypatch.setattr(Drive,'_folder_has_ancestor',lambda *args:True)
    with app.app_context():
        db.session.get(Document,docs[0]).drive_parent_id='archive';db.session.commit()
    return members,docs[0],drive


def execute(mid,did,**overrides):
    args={'confirm_filename':'test.pdf','retention_confirmed':True,'retention_reason':'Synthetic retention review'}
    args.update(overrides)
    Drive.permanently_delete_document(db.session.get(Document,did),db.session.get(Member,mid),**args)


@pytest.mark.parametrize('block',['member','inactive','unknown','event','receipt','retention','reason','name','not_archive','repeat'])
def test_delete_guards(app,deletion_case,block,monkeypatch):
    members,did,drive=deletion_case
    with app.app_context():
        actor=members[3];extra={}
        doc=db.session.get(Document,did)
        if block=='member':actor=members[1]
        if block=='inactive':db.session.get(Member,actor).is_active=False
        if block=='unknown':db.session.delete(db.session.get(DocumentPolicy,'club'))
        if block=='event':doc.event_id=1
        if block=='receipt':db.session.add(Receipt(drive_file_id='club',drive_file_name='test.pdf',drive_folder_id='archive',uploader_id=actor))
        if block=='retention':extra['retention_confirmed']=False
        if block=='reason':extra['retention_reason']=''
        if block=='name':extra['confirm_filename']='old.pdf'
        if block=='not_archive':monkeypatch.setattr(Drive,'_folder_has_ancestor',lambda *args:False)
        if block=='repeat':db.session.add(DocumentDeletionRequest(drive_file_id='club',document_id=did,actor_id=actor,filename='test.pdf',reason='prior'))
        db.session.commit()
        with pytest.raises(DriveValidationError):execute(actor,did,**extra)
        drive.files.return_value.update.assert_not_called()
        assert db.session.get(Document,did) is not None


def test_success_preserves_review_and_atomic_audit(app,deletion_case):
    members,did,drive=deletion_case
    with app.app_context():
        execute(members[3],did)
        drive.files.return_value.update.assert_called_once_with(fileId='club',body={'trashed':True},supportsAllDrives=True)
        assert db.session.get(Document,did) is None
        record=db.session.get(DocumentDeletionRequest,'club')
        assert record.status=='completed' and record.completed_at and record.reason=='Synthetic retention review'
        event=AuditEvent.query.filter_by(action=AuditAction.DOCUMENT_PERMANENTLY_DELETED).one()
        assert event.extra_json['retention_reviewed'] is True
        assert db.session.get(DocumentPolicy,'club') is not None


@pytest.mark.parametrize('failure',['remote','initial_commit','completion_commit'])
def test_uncertain_outcome_blocks_repeat(app,deletion_case,monkeypatch,failure):
    members,did,drive=deletion_case
    with app.app_context():
        if failure=='remote':drive.files.return_value.update.return_value.execute.side_effect=RuntimeError('synthetic lost response')
        original=db.session.commit;calls=[]
        def commit():
            calls.append(True)
            if len(calls)==(1 if failure=='initial_commit' else 2):raise SQLAlchemyError('synthetic commit failure')
            return original()
        if failure!='remote':monkeypatch.setattr(db.session,'commit',commit)
        with pytest.raises(DriveError):execute(members[3],did)
        assert db.session.get(Document,did) is not None
        record=db.session.get(DocumentDeletionRequest,'club')
        if failure=='initial_commit':
            assert record is None;drive.files.return_value.update.assert_not_called()
        else:
            assert record.status=='pending'
            assert AuditEvent.query.filter_by(action=AuditAction.DOCUMENT_PERMANENTLY_DELETED).count()==0
            with pytest.raises(DriveValidationError):execute(members[3],did)
            assert drive.files.return_value.update.call_count==1


def test_journal_is_admin_only(app,client,deletion_case):
    members,did,drive=deletion_case
    with app.app_context():execute(members[3],did)
    login(client,members[1]);assert client.get('/docs/admin/deletions').status_code==403
    login(client,members[3]);response=client.get('/docs/admin/deletions')
    assert response.status_code==200 and 'Synthetic retention review' in response.get_data(as_text=True)


def test_delete_route_requires_review_and_keeps_csrf(app,client,deletion_case,monkeypatch):
    members,did,drive=deletion_case;login(client,members[3])
    monkeypatch.setattr(Drive,'fetch_drive_filename',lambda doc:'test.pdf')
    data={'confirm_filename':'test.pdf','retention_confirmed':'on','retention_reason':'Synthetic checked'}
    assert client.post(f'/docs/file/{did}/delete',data=data).status_code==403
    monkeypatch.setattr('backend.routes.docs._validate_csrf_or_403',lambda:None)
    assert client.post(f'/docs/file/{did}/delete',data={'confirm_filename':'test.pdf'}).status_code==302
    drive.files.return_value.update.assert_not_called()
    assert client.post(f'/docs/file/{did}/delete',data=data).status_code==302
    with app.app_context():assert db.session.get(DocumentDeletionRequest,'club').status=='completed'
