"""Primary-address binding and legacy links, synthetic identities only."""
from datetime import timedelta
import pytest
from backend.extensions import db
from backend.models.member import Member
from backend.models.auth_token import AuthToken, AuthTokenPurpose as Purpose
from backend.services.security import SecurityService
def _issue_auth_token(*args, **kwargs):
    from backend.routes.auth import _issue_auth_token as issue_token
    return issue_token(*args, **kwargs)


def _resolve_auth_token(*args, **kwargs):
    from backend.routes.auth import _resolve_auth_token as resolve_token
    return resolve_token(*args, **kwargs)

from tests.routes.test_event_visibility import visibility_data, login

PURPOSES=[Purpose.PASSWORD_RESET,Purpose.MFA_RESET,Purpose.ONBOARDING]


def issue(app,mid):
    with app.app_context():
        tokens={p:_issue_auth_token(mid,p,timedelta(hours=1),None) for p in PURPOSES}
        db.session.commit()
        return tokens


@pytest.mark.parametrize('purpose',PURPOSES)
def test_address_binding_and_legacy_denial(app,visibility_data,purpose):
    members,_=visibility_data;tokens=issue(app,members[1])
    with app.app_context():
        assert _resolve_auth_token(tokens[purpose],purpose)[1] is None
        member=db.session.get(Member,members[1]);old=member.email
        member.email='changed@example.test';db.session.commit()
        assert _resolve_auth_token(tokens[purpose],purpose)[1]=='missing'
        member.email=old;db.session.commit()
        row=AuthToken.query.filter_by(member_id=member.id,purpose=purpose).one()
        row.recipient_email=None;row.issued_generation=None;db.session.commit()
        assert _resolve_auth_token(tokens[purpose],purpose)[1]=='missing'
        wrong=Purpose.MFA_RESET if purpose!=Purpose.MFA_RESET else Purpose.PASSWORD_RESET
        assert _resolve_auth_token(tokens[purpose],wrong)[1]=='missing'


@pytest.mark.parametrize('entry',['profile','admin'])
def test_address_change_and_back_permanently_revokes_links(app,client,visibility_data,entry):
    members,_=visibility_data
    with app.app_context():
        db.session.get(Member,members[1]).email='Reader@example.com';db.session.commit()
    tokens=issue(app,members[1])
    login(client,members[1] if entry=='profile' else members[3])
    for email in ['new@example.com','Reader@example.com']:
        if entry=='profile':
            response=client.post('/member/profile',data={'active_tab':'profile','profile-vorname':'Reader',
                'profile-nachname':'Synthetic','profile-email':email})
        else:
            response=client.post(f'/admin/members/{members[1]}/edit',data={'vorname':'Reader','nachname':'Synthetic',
                'email':email,'role':'MEMBER','funktion':'MEMBER','is_active':'y','beitritt':'2020-01-01'})
        assert response.status_code==302
    with app.app_context():
        for purpose,raw in tokens.items():assert _resolve_auth_token(raw,purpose)[1]=='used'


def test_address_and_revocation_rollback_together(app,visibility_data):
    members,_=visibility_data;tokens=issue(app,members[1])
    with app.app_context():
        member=SecurityService.lock_credential_member(members[1]);old=member.email
        SecurityService.update_primary_email(member,'new@example.test');db.session.flush();db.session.rollback()
        assert db.session.get(Member,members[1]).email==old
        for purpose,raw in tokens.items():assert _resolve_auth_token(raw,purpose)[1] is None


@pytest.mark.parametrize('purpose,path',[(Purpose.PASSWORD_RESET,'reset-password'),(Purpose.ONBOARDING,'activate'),(Purpose.MFA_RESET,'2fa/reset')])
def test_legacy_links_never_mutate_and_responses_not_cached(app,client,visibility_data,purpose,path):
    members,_=visibility_data;tokens=issue(app,members[1])
    with app.app_context():
        row=AuthToken.query.filter_by(member_id=members[1],purpose=purpose).one()
        row.recipient_email=None;row.issued_generation=None;db.session.commit()
    response=client.post(f'/auth/{path}/{tokens[purpose]}',data={'new_password':'Synthetic-New-password','confirm_password':'Synthetic-New-password','confirm':'y'})
    assert response.status_code==302
    assert response.headers['Cache-Control']=='no-store'
    assert response.headers['Referrer-Policy']=='no-referrer'
    with app.app_context():assert db.session.get(Member,members[1]).passwort_hash=='unused'
    with client.session_transaction() as state:assert '_user_id' not in state
