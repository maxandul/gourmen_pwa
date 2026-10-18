"""Fake Drive metadata only; verify every presentation boundary before transport."""
from datetime import datetime
from io import BytesIO
from unittest.mock import Mock
import pytest
from backend.extensions import db
from backend.models.document import Document
from backend.models.document_policy import DocumentPolicy, DocumentPolicyChange
from backend.models.member import Member
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.drive_storage import DriveStorageService as Drive, FolderListing, FolderMeta, FolderRef, FileRow, SearchHit, DriveValidationError
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def document_case(app,visibility_data,monkeypatch):
    members,events=visibility_data
    app.config.update(GOOGLE_DRIVE_ID='root',DRIVE_ARCHIVE_FOLDER_ID='archive')
    with app.app_context():
        docs=[]
        for key,level,event in [('club','club',None),('board','board',None),('unknown',None,None),('event','club',events[2])]:
            doc=Document(drive_file_id=key,drive_parent_id='folder',event_id=event);db.session.add(doc);db.session.flush();docs.append(doc.id)
            if level:db.session.add(DocumentPolicy(drive_id=key,is_folder=False,access_level=level,maintenance_scope='documents_manage'))
        db.session.add_all([DocumentPolicy(drive_id='folder',is_folder=True,access_level='club',maintenance_scope='documents_manage'),
            DocumentPolicy(drive_id='secret-folder',is_folder=True,access_level='board',maintenance_scope='board_documents_manage'),
            DocumentPolicy(drive_id='archive',is_folder=True,access_level='club',maintenance_scope='documents_manage')]);db.session.commit()
    def listing(folder):
        return FolderListing(folder,[FolderMeta('folder','Allowed-folder',997),FolderMeta('secret-folder','SECRET-FOLDER',998)],
            [FileRow(key,key+'-MARKER','application/pdf',datetime.now(),'https://example.test/'+key,did,None,10)
             for key,did in zip(['club','board','unknown','event'],docs)])
    monkeypatch.setattr(Drive,'list_folder',listing)
    monkeypatch.setattr(Drive,'list_subfolders_only',lambda folder:[FolderRef('folder','Allowed-folder'),FolderRef('secret-folder','SECRET-FOLDER')])
    monkeypatch.setattr(Drive,'search_files',lambda *a,**k:[SearchHit(key,key+'-MARKER','application/pdf','folder',[FolderRef('secret-folder','SECRET-PATH')]) for key in ['club','board','unknown','event']])
    monkeypatch.setattr(Drive,'get_folder_breadcrumb',lambda folder:[FolderRef('secret-folder','SECRET-PATH'),FolderRef(folder,'Allowed-folder')])
    monkeypatch.setattr(Drive,'get_web_view_link_for_folder_id',lambda folder:'')
    monkeypatch.setattr(Drive,'auto_sync_document',lambda *a,**k:None)
    monkeypatch.setattr(Drive,'fetch_drive_filename',lambda doc:doc.drive_file_id+'-MARKER')
    monkeypatch.setattr(Drive,'get_web_view_link',lambda doc:'')
    monkeypatch.setattr(Drive,'document_is_under_archive',lambda doc:doc.drive_parent_id=='archive')
    return members,docs


def test_lists_search_picker_and_direct_urls(app,client,document_case,monkeypatch):
    members,docs=document_case;login(client,members[1])
    for path in ['/docs/','/docs/?q=marker','/docs/folder/folder','/docs/folder/folder?q=marker','/docs/api/folder/root/children']:
        response=client.get(path);assert response.status_code==200
        body=response.get_data(as_text=True)
        for secret in ['SECRET-FOLDER','SECRET-PATH','board-MARKER','unknown-MARKER','event-MARKER','997','998']:
            assert secret not in body
        assert response.headers['Cache-Control']=='private, no-store'
    assert client.get('/docs/api/root').json['can_select'] is False
    assert client.get('/docs/api/folder/root/children').json['folders'][0]['can_select'] is False
    monkeypatch.setattr(Drive,'download_document',lambda *a,**k:(b'synthetic','application/pdf','test.pdf'))
    assert client.get(f'/docs/file/{docs[0]}').status_code==200
    assert client.get(f'/docs/file/{docs[0]}/download').data==b'synthetic'
    for did in docs[1:]:
        assert client.get(f'/docs/file/{did}').status_code==403
        assert client.get(f'/docs/file/{did}/download').status_code==403
    assert client.get('/docs/folder/secret-folder').status_code==403
    assert client.get('/docs/api/folder/secret-folder/children').status_code==403
    assert 'data-drive-quick-rename data-doc-id' not in client.get(f'/docs/file/{docs[0]}').get_data(as_text=True)


@pytest.mark.parametrize('grant',[False,True])
def test_mutations_and_target_guards(app,client,document_case,monkeypatch,grant):
    members,docs=document_case;login(client,members[1])
    if grant:
        with app.app_context():
            db.session.add(MemberAreaGrant(member_id=members[1],scope='documents_manage',granted_by=members[3]));db.session.commit()
    monkeypatch.setattr('backend.routes.docs._validate_csrf_or_403',lambda:None)
    for action in ['rename','move','archive','restore']:
        fake=Mock();monkeypatch.setattr(Drive,action+'_document',fake)
        data={'title':'new','new_parent_id':'folder','target_folder_id':'folder'}
        assert client.post(f'/docs/file/{docs[0]}/{action}',data=data).status_code==(302 if grant else 403)
        assert fake.call_count==int(grant)
        fake.reset_mock()
        assert client.post(f'/docs/file/{docs[1]}/{action}',data=data).status_code==403
        fake.assert_not_called()
    assert client.post(f'/docs/file/{docs[0]}/move',data={'new_parent_id':'secret-folder'}).status_code==403
    fake=Mock();monkeypatch.setattr(Drive,'upload_document',fake)
    assert client.post('/docs/upload',data={'file':(BytesIO(b'x'),'test.pdf'),'drive_folder_id':'secret-folder'}).status_code==403
    fake.assert_not_called()


def test_services_reject_before_drive_and_archiving_keeps_classification(app,document_case,monkeypatch):
    members,docs=document_case
    monkeypatch.setattr(Drive,'_build_drive',lambda:pytest.fail('Unauthorized transport'))
    with app.app_context():
        actor=db.session.get(Member,members[1]);doc=db.session.get(Document,docs[0])
        for operation in [lambda:Drive.rename_document(doc,'new',actor),lambda:Drive.move_document(doc,'folder',actor),
                          lambda:Drive.archive_document(doc,actor),lambda:Drive.restore_document(doc,'folder',actor),
                          lambda:Drive.upload_document(BytesIO(b'x'),'new','folder',actor)]:
            with pytest.raises(DriveValidationError):operation()
        doc=db.session.get(Document,docs[1])
        with pytest.raises(DriveValidationError):Drive.download_document(doc,reader=actor)
        doc.drive_parent_id='archive';db.session.flush()
        from backend.services.document_permissions import DocumentPermissionService as Policy
        assert not Policy.can_read_document(actor,doc,root_id='root')


def test_admin_classification_csrf_history_and_stale_form(app,client,document_case,monkeypatch):
    members,docs=document_case
    monkeypatch.setattr(Drive,'_build_drive',lambda:object())
    monkeypatch.setattr(Drive,'_drive_file_meta',lambda *args:{'name':'Synthetic','mimeType':'application/pdf','parents':['folder']})
    monkeypatch.setattr(Drive,'_folder_reachable_from_root',lambda *args:True)
    login(client,members[1]);assert client.get('/docs/classify/unknown').status_code==403
    login(client,members[3]);assert client.get('/docs/classify/unknown').status_code==200
    data={'access_level':'club','maintenance_scope':'documents_manage','reason':'Synthetic review','expected_before':'null'}
    assert client.post('/docs/classify/unknown',data=data).status_code==403
    monkeypatch.setattr('backend.routes.docs._validate_csrf_or_403',lambda:None)
    assert client.post('/docs/classify/unknown',data=data).status_code==302
    assert client.post('/docs/classify/unknown',data=data).status_code==200
    with app.app_context():assert DocumentPolicyChange.query.count()==1
    login(client,members[1]);assert client.get(f'/docs/file/{docs[2]}').status_code==200


def test_upload_inherits_policy_and_move_preserves_it(app,document_case,monkeypatch):
    members,docs=document_case
    monkeypatch.setattr(Drive,'_build_drive',lambda:object())
    monkeypatch.setattr(Drive,'assert_is_folder_in_drive',lambda *args:None)
    monkeypatch.setattr(Drive,'_resolve_filename_collision',lambda d,f,n:n)
    monkeypatch.setattr(Drive,'_drive_create_file',lambda *args:{'id':'new-upload','parents':['folder']})
    moved=Mock();monkeypatch.setattr(Drive,'_move_drive_file',moved)
    monkeypatch.setattr(Drive,'_drive_file_meta',lambda *args:{'parents':['folder']})
    with app.app_context():
        actor=db.session.get(Member,members[1])
        db.session.add(MemberAreaGrant(member_id=actor.id,scope='documents_manage',granted_by=members[3]));db.session.commit()
        doc=Drive.upload_document(BytesIO(b'synthetic'),'test','folder',actor,original_filename='test.pdf',mime_type='application/pdf')
        policy=db.session.get(DocumentPolicy,doc.drive_file_id)
        assert policy.access_level=='club' and not policy.is_folder
        assert DocumentPolicyChange.query.filter_by(drive_id='new-upload').count()==1
        Drive.move_document(doc,'archive',actor)
        moved.assert_called_once()
        assert doc.drive_parent_id=='archive' and policy.access_level=='club'


def test_download_rechecks_live_parent_before_bytes(app,document_case,monkeypatch):
    members,docs=document_case
    monkeypatch.setattr(Drive,'_build_drive',lambda:object())
    monkeypatch.setattr(Drive,'_drive_file_meta',lambda *args:{'parents':['secret-folder']})
    with app.app_context():
        with pytest.raises(DriveValidationError):
            Drive.download_document(db.session.get(Document,docs[0]),reader=db.session.get(Member,members[1]))


def test_area_maintainer_can_archive_without_general_folder_write(app,document_case,monkeypatch):
    from backend.models.member import Funktion
    members,docs=document_case
    monkeypatch.setattr(Drive,'_build_drive',lambda:object())
    monkeypatch.setattr(Drive,'assert_is_folder_in_drive',lambda *args:None)
    monkeypatch.setattr(Drive,'_drive_file_meta',lambda *args:{'parents':['folder']})
    move=Mock();monkeypatch.setattr(Drive,'_move_drive_file',move)
    with app.app_context():
        actor=db.session.get(Member,members[1]);actor.funktion=Funktion.REISEKOMMISSAR
        db.session.get(DocumentPolicy,'club').maintenance_scope='travel_manage';db.session.commit()
        doc=db.session.get(Document,docs[0])
        with pytest.raises(DriveValidationError):Drive.move_document(doc,'folder',actor)
        Drive.archive_document(doc,actor)
        move.assert_called_once()
        assert doc.drive_parent_id=='archive'
        assert db.session.get(DocumentPolicy,'club').maintenance_scope=='travel_manage'
