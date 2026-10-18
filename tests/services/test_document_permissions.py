"""Synthetic classification, role matrix and fail-closed aliases."""
import pytest
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.document import Document
from backend.models.document_policy import DocumentPolicy, DocumentPolicyChange
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.document_permissions import DocumentPermissionService as Policy
from tests.routes.test_event_visibility import visibility_data


@pytest.mark.parametrize('role,level,scope,read,write', [
    ('member','club','documents_manage',True,False),
    ('board','board','board_documents_manage',True,False),
    ('member','board','documents_manage',False,False),
    ('travel','club','travel_manage',True,True),
    ('travel','board','travel_manage',False,False),
    ('marketing','club','merch_manage',True,True),
    ('finance','finance','accounting_write',True,True),
    ('reviewer','finance','accounting_write',True,False),
    ('member','finance','documents_manage',False,False),
    ('admin','board','board_documents_manage',True,True),
    ('grant','club','documents_manage',True,True),
    ('grant','board','documents_manage',False,False),
])
def test_policy_matrix(app,visibility_data,role,level,scope,read,write):
    members,_=visibility_data
    with app.app_context():
        member=db.session.get(Member,members[3] if role=='admin' else members[1])
        member.vorstandsmitglied=role=='board'
        member.funktion={'travel':Funktion.REISEKOMMISSAR,'marketing':Funktion.MARKETINGCHEF,
            'finance':Funktion.SCHATZMEISTER,'reviewer':Funktion.RECHNUNGSPRUEFER}.get(role,Funktion.MEMBER)
        if role=='grant':db.session.add(MemberAreaGrant(member_id=member.id,scope='documents_manage',granted_by=members[3]))
        db.session.add(DocumentPolicy(drive_id='synthetic',is_folder=False,access_level=level,maintenance_scope=scope));db.session.flush()
        assert Policy.can_read_item(member,'synthetic',is_folder=False)==read
        assert Policy.can_manage_item(member,'synthetic',is_folder=False)==write
        assert Policy.can_read_item(member,'unknown',is_folder=False)==(role=='admin')
        assert Policy.can_read_item(member,'synthetic',is_folder=True)==(role=='admin')
        member.is_active=False
        assert not Policy.can_read_item(member,'synthetic',is_folder=False)


def test_classify_history_stale_state_validation_and_rollback(app,visibility_data):
    members,_=visibility_data
    with app.app_context():
        admin=db.session.get(Member,members[3]);member=db.session.get(Member,members[1])
        args=dict(is_folder=False,access_level='club',maintenance_scope='documents_manage',reason='Synthetic review',expected_before=None)
        with pytest.raises(PermissionError):Policy.classify(member,'synthetic',**args)
        with pytest.raises(ValueError):Policy.classify(admin,'synthetic',**dict(args,access_level='public'))
        policy=Policy.classify(admin,'synthetic',**args);db.session.commit()
        before=policy.snapshot()
        with pytest.raises(ValueError):Policy.classify(admin,'synthetic',**args)
        Policy.classify(admin,'synthetic',**dict(args,access_level='board',expected_before=before))
        db.session.flush();assert DocumentPolicyChange.query.count()==2
        db.session.rollback()
        assert Policy.policy('synthetic').access_level=='club'
        assert DocumentPolicyChange.query.count()==1
        change=DocumentPolicyChange.query.one()
        assert change.before is None and change.after==before and change.actor_id==admin.id


def test_document_event_parent_and_unknown_boundary(app,visibility_data):
    members,events=visibility_data
    with app.app_context():
        member=db.session.get(Member,members[1])
        doc=Document(drive_file_id='file',drive_parent_id='folder',event_id=events[2])
        db.session.add_all([doc,DocumentPolicy(drive_id='file',is_folder=False,access_level='club',maintenance_scope='documents_manage')]);db.session.flush()
        assert not Policy.can_read_document(member,doc)
        db.session.add(DocumentPolicy(drive_id='folder',is_folder=True,access_level='club',maintenance_scope='documents_manage'));db.session.flush()
        assert not Policy.can_read_document(member,doc)
        doc.event_id=events[0]
        assert Policy.can_read_document(member,doc)
        Policy.policy('folder').access_level='board'
        assert not Policy.can_read_document(member,doc)
        assert Policy.can_read_folder(member,'root',root_id='root')
        assert not Policy.can_manage_item(member,'root',is_folder=True)


def test_receipt_alias_never_bypasses_finance_owner_or_event_rules(app,visibility_data):
    from backend.models.accounting import Receipt
    members,events=visibility_data
    with app.app_context():
        member=db.session.get(Member,members[1])
        doc=Document(drive_file_id='alias',drive_parent_id='root')
        receipt=Receipt(drive_file_id='alias',drive_file_name='synthetic.pdf',drive_folder_id='root',uploader_id=members[0])
        db.session.add_all([doc,receipt,DocumentPolicy(drive_id='alias',is_folder=False,access_level='club',maintenance_scope='documents_manage')]);db.session.flush()
        assert not Policy.can_read_document(member,doc,root_id='root')
        receipt.uploader_id=member.id
        assert Policy.can_read_document(member,doc,root_id='root')
        receipt.suggested_event_id=events[2]
        assert not Policy.can_read_document(member,doc,root_id='root')
