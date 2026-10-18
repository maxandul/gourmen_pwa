"""Local scoped grants with action proof, revocation and transactional history."""
import pytest
from sqlalchemy.exc import SQLAlchemyError
from backend.extensions import db
from backend.models.member import Member
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.area_permissions import AreaPermissionService
from tests.routes.test_action_confirmation import case, sign_in, intent, PASSWORD, generation


def path(uid): return f'/admin/members/{uid}/area-permissions'


def test_grant_revoke_regrant_preserves_history_and_revokes_identity(app,client,case):
    uid=case[1];old=generation(app,uid)
    data={'scopes':['travel_documents'],'action_password':PASSWORD,'action_token':intent(client,path(uid))}
    assert client.post(path(uid),data=data).status_code==302
    assert generation(app,uid)!=old
    with app.app_context():assert AreaPermissionService.has_scope(db.session.get(Member,uid),'travel_documents')
    # Same proof cannot revoke: generation has changed.
    assert client.post(path(uid),data=dict(data,scopes=[])).status_code==200
    data={'action_password':PASSWORD,'action_token':intent(client,path(uid))}
    assert client.post(path(uid),data=data).status_code==302
    with app.app_context():
        assert not AreaPermissionService.has_scope(db.session.get(Member,uid),'travel_documents')
        grant=MemberAreaGrant.query.one();assert grant.revoked_by==case[0]
    data.update(scopes=['travel_documents'],action_token=intent(client,path(uid)))
    client.post(path(uid),data=data)
    with app.app_context():assert MemberAreaGrant.query.count()==2


@pytest.mark.parametrize('failure',['password','missing','unknown','target','other_action'])
def test_invalid_grant_proof_no_mutation(app,client,case,failure):
    uid=case[1];before=generation(app,uid)
    token=intent(client,path(uid))
    data={'scopes':['travel_documents'],'action_password':PASSWORD,'action_token':token}
    if failure=='password':data['action_password']='wrong'
    if failure=='missing':data.pop('action_token')
    if failure=='unknown':data['scopes']=['admin']
    if failure=='target':data['action_token']=intent(client,path(case[2]))
    if failure=='other_action':data['action_token']=intent(client,f'/admin/members/{uid}/reset-2fa')
    assert client.post(path(uid),data=data).status_code==200
    with app.app_context():assert MemberAreaGrant.query.count()==0
    assert generation(app,uid)==before


def test_member_reads_only_own_grants_and_cannot_write(app,client,case):
    sign_in(client,case[1])
    assert client.get(path(case[1])).status_code==200
    assert client.get(path(case[2])).status_code==403
    assert client.post(path(case[1]),data={'scopes':'travel_documents'}).status_code==403
    with app.app_context():
        member=db.session.get(Member,case[1])
        assert not AreaPermissionService.has_scope(member,'admin')
        assert not AreaPermissionService.has_scope(member,'travel_documents')


def test_commit_failure_rolls_back_grant_and_identity(app,client,case,monkeypatch):
    uid=case[1];before=generation(app,uid);token=intent(client,path(uid))
    def fail():raise SQLAlchemyError('synthetic')
    with monkeypatch.context() as patch:
        patch.setattr(db.session,'commit',fail)
        response=client.post(path(uid),data={'scopes':'travel_documents','action_password':PASSWORD,'action_token':token})
    assert response.status_code==200
    assert generation(app,uid)==before
    with app.app_context():assert MemberAreaGrant.query.count()==0


def test_grant_gives_only_travel_view_and_still_needs_stepup(app,client,case):
    uid=case[1]
    client.post(path(uid),data={'scopes':'travel_documents','action_password':PASSWORD,'action_token':intent(client,path(uid))})
    sign_in(client,uid)
    response=client.get(f'/admin/members/{case[2]}/travel-documents')
    assert response.status_code==302 and '/auth/step-up' in response.location
    assert client.get(f'/admin/members/{case[2]}/sensitive').status_code==403
    assert client.get('/accounting/').status_code==403


def test_grant_change_rejects_old_member_session_and_csrf(app,client,case):
    old_client=app.test_client();sign_in(old_client,case[1])
    token=intent(client,path(case[1]))
    assert client.post(path(case[1]),data={'scopes':'travel_documents','action_password':PASSWORD,'action_token':token}).status_code==302
    assert '/auth/login' in old_client.get(path(case[1])).location
    app.config['WTF_CSRF_ENABLED']=True
    assert client.post(path(case[2]),data={'scopes':'travel_documents','action_password':PASSWORD}).status_code==400
