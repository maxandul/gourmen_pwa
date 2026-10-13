"""A-077/A-082: replay old cookies and pending MFA across security events."""
import base64
import time
from datetime import timedelta
from unittest.mock import Mock

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.member_mfa import MemberMFA
from backend.models.auth_token import AuthTokenPurpose
from backend.services.authentication import AuthenticationService
from backend.services.security import SecurityService
from tests.conftest import auth_id, device_grant

PASSWORD = 'Synthetic-access-password1!'
NEW = 'Synthetic-access-password2!'
SECRET = 'JBSWY3DPEHPK3PXP'


@pytest.fixture
def accounts(app):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        users = []
        for name, role in [('member', Role.MEMBER), ('admin', Role.ADMIN)]:
            user = Member(vorname=name, nachname='Test', email=f'{name}@example.com', role=role)
            user.set_password(PASSWORD)
            db.session.add(user)
            users.append(user)
        db.session.flush()
        db.session.add(MemberMFA(member_id=users[0].id, is_totp_enabled=True,
                                totp_secret_encrypted=SecurityService.encrypt_json(SECRET)))
        db.session.commit()
        return [user.id for user in users]


def start(client, *, password=PASSWORD):
    return client.post('/auth/login', data={'email': 'member@example.com', 'password': password})


def login(client):
    assert start(client).location.endswith('/auth/2fa/verify')
    assert client.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now(),
                                               'remember_device': '1'}).status_code == 302
    assert client.get('/member/profile').status_code == 200


def token(app, uid, purpose):
    from backend.routes.auth import _issue_auth_token
    with app.app_context():
        raw = _issue_auth_token(uid, purpose, timedelta(hours=1), None)
        db.session.commit()
        return raw


def administrator(client, uid):
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True
        state['sensitive_access_member_id'] = auth_id(client, uid)
        state['sensitive_access_until'] = time.time() + 300


def edit_payload(*, active=True, role='MEMBER', function='MEMBER'):
    data = {'vorname': 'member', 'nachname': 'Test', 'email': 'member@example.com',
            'role': role, 'funktion': function, 'beitritt': '2020-01-01'}
    if active:
        data['is_active'] = 'y'
    return data


@pytest.mark.parametrize('event', ['password_reset', 'admin_password', 'mfa_reset', 'admin_mfa',
                                  'deactivate', 'permissions'])
def test_security_event_revokes_session_cookie_remember_cookie_and_pending_mfa(app, accounts, event):
    uid, admin_id = accounts
    active, pending, operator = [app.test_client() for _ in range(3)]
    login(active)
    old_session = active.get_cookie('session').value
    old_remember = active.get_cookie('remember_token').value
    with active.session_transaction() as state:
        old_trust = dict(state['remembered_device'])
    start(pending)
    if event in ('password_reset', 'mfa_reset'):
        purpose = AuthTokenPurpose.PASSWORD_RESET if event == 'password_reset' else AuthTokenPurpose.MFA_RESET
        route = 'reset-password' if event == 'password_reset' else '2fa/reset'
        raw = token(app, uid, purpose)
        data = {'new_password': NEW, 'confirm_password': NEW} if event == 'password_reset' else {'confirm': 'y'}
        response = operator.post(f'/auth/{route}/{raw}', data=data)
    else:
        administrator(operator, admin_id)
        if event in ('admin_password', 'admin_mfa'):
            route = 'reset-password' if event == 'admin_password' else 'reset-2fa'
            response = operator.post(f'/admin/members/{uid}/{route}', data={'confirm': 'RESET'})
        else:
            response = operator.post(f'/admin/members/{uid}/edit', data=edit_payload(
                active=event != 'deactivate', function='SCHATZMEISTER' if event == 'permissions' else 'MEMBER'))
    assert response.status_code == 302
    for cookie in ('session', 'remember_token'):
        replay = app.test_client()
        replay.set_cookie(cookie, old_session if cookie == 'session' else old_remember)
        assert replay.get('/member/profile').status_code == 302
        with replay.session_transaction() as state:
            assert '_user_id' not in state
    assert pending.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now()}).location.endswith('/auth/login')
    with active.session_transaction() as state:
        state.clear()
        state['remembered_device'] = old_trust
    with app.test_request_context():
        with app.app_context():
            from flask import session
            session['remembered_device'] = old_trust
            assert AuthenticationService.trusted_device(db.session.get(Member, uid)) is None
    if event == 'deactivate':
        administrator(operator, admin_id)
        assert operator.post(f'/admin/members/{uid}/edit', data=edit_payload()).status_code == 302
        replay = app.test_client()
        replay.set_cookie('session', old_session)
        assert replay.get('/member/profile').status_code == 302
    assert operator.get('/member/profile').status_code == (200 if event.startswith('admin_') or event in ('permissions', 'deactivate') else 302)


def test_normal_password_change_preserves_only_current_session_and_trust(app, accounts):
    current, other = app.test_client(), app.test_client()
    login(current)
    login(other)
    old_cookie = current.get_cookie('session').value
    with current.session_transaction() as state:
        old_expiry = state['remembered_device']['expires_at']
    response = current.post('/auth/change-password', data={'current_password': PASSWORD,
                            'new_password': NEW, 'confirm_password': NEW})
    assert response.status_code == 302
    assert current.get('/member/profile').status_code == 200
    assert other.get('/member/profile').status_code == 302
    replay = app.test_client()
    replay.set_cookie('session', old_cookie)
    assert replay.get('/member/profile').status_code == 302
    with current.session_transaction() as state:
        assert state['remembered_device']['expires_at'] == old_expiry
        assert state['remembered_device']['generation'] == auth_id(current, accounts[0]).split(':', 1)[1]
    current.get('/auth/logout')
    assert start(current, password=NEW).location.endswith('/dashboard/')
    current.delete_cookie('session')
    assert current.get('/member/profile').status_code == 200  # renewed remember cookie


@pytest.mark.parametrize('invalid', ['legacy', 'expired', 'future', 'long', 'malformed', 'foreign', 'nan', 'overflow'])
def test_invalid_device_grants_cannot_skip_mfa(app, client, accounts, invalid):
    grant = device_grant(client, accounts[0])
    if invalid == 'legacy':
        grant.pop('generation')
    elif invalid == 'expired':
        grant['expires_at'] = time.time() - 1
    elif invalid == 'future':
        grant['issued_at'] = time.time() + 100
    elif invalid == 'long':
        grant['expires_at'] += 100
    elif invalid == 'malformed':
        grant = 'invalid'
    elif invalid == 'foreign':
        grant['user_id'] = accounts[1]
    elif invalid == 'overflow':
        grant['expires_at'] = 10 ** 1000
    else:
        grant['expires_at'] = float('nan')
    with client.session_transaction() as state:
        state['remembered_device'] = grant
    assert start(client).location.endswith('/auth/2fa/verify')


def test_trust_requires_totp_and_cannot_be_issued_by_legacy_endpoint(app, client, accounts):
    assert start(client).location.endswith('/auth/2fa/verify')
    assert client.post('/auth/2fa/verify', data={'token': 'invalid', 'remember_device': '1'}).status_code == 200
    with client.session_transaction() as state:
        assert 'remembered_device' not in state
    client.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now(), 'remember_device': '1'})
    with client.session_transaction() as state:
        trust = state['remembered_device']
        assert trust['expires_at'] - trust['issued_at'] == 30 * 86400
    assert client.post('/auth/2fa/remember-device').status_code == 403
    client.get('/auth/logout')
    assert start(client).location.endswith('/dashboard/')


def test_mfa_reenrollment_invalidates_previous_trust(app, client, accounts):
    login(client)
    old_cookie = client.get_cookie('session').value
    assert client.post('/auth/2fa/disable', data={'password': PASSWORD}).status_code == 302
    assert client.get('/member/profile').status_code == 200
    with client.session_transaction() as state:
        state['2fa_secret'] = SECRET
    assert client.post('/auth/2fa/enroll', data={'token': pyotp.TOTP(SECRET).now()}).status_code == 200
    assert client.get('/member/profile').status_code == 200
    with client.session_transaction() as state:
        assert 'remembered_device' not in state
    replay = app.test_client()
    replay.set_cookie('session', old_cookie)
    assert replay.get('/member/profile').status_code == 302


def test_failed_password_commit_does_not_revoke_or_renew_sessions(app, accounts, monkeypatch):
    current, other = app.test_client(), app.test_client()
    login(current)
    login(other)
    old_id = auth_id(current, accounts[0])
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
        with pytest.raises(RuntimeError):
            current.post('/auth/change-password', data={'current_password': PASSWORD,
                         'new_password': NEW, 'confirm_password': NEW})
    assert auth_id(current, accounts[0]) == old_id
    assert current.get('/member/profile').status_code == other.get('/member/profile').status_code == 200


@pytest.mark.parametrize('identifier', ['1', 'invalid', '1:old', '1:ü', None])
def test_legacy_and_malformed_sessions_fail_closed(client, accounts, identifier):
    with client.session_transaction() as state:
        state['_user_id'] = identifier
    assert client.get('/member/profile').status_code == 302


def test_activation_with_existing_mfa_does_not_log_in(app, accounts):
    client = app.test_client()
    raw = token(app, accounts[0], AuthTokenPurpose.ONBOARDING)
    assert client.post('/auth/activate/' + raw, data={'new_password': NEW, 'confirm_password': NEW}).location.endswith('/auth/login')
    with client.session_transaction() as state:
        assert '_user_id' not in state
    assert start(client, password=NEW).location.endswith('/auth/2fa/verify')


@pytest.mark.parametrize('entry', ['totp', 'change', 'activate'])
def test_intervening_reset_after_commit_is_not_adopted(app, client, accounts, monkeypatch, entry):
    uid = accounts[0]
    if entry == 'change':
        login(client)
    elif entry == 'totp':
        start(client)
    else:
        # No MFA: activation would normally establish a new session.
        with app.app_context():
            MemberMFA.query.one().is_totp_enabled = False
            db.session.commit()
        raw = token(app, uid, AuthTokenPurpose.ONBOARDING)
    commit = db.session.commit
    changed = False

    def commit_then_reset():
        nonlocal changed
        commit()
        if not changed:
            changed = True
            db.session.get(Member, uid).rotate_auth_generation()
            commit()

    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', commit_then_reset)
        if entry == 'totp':
            response = client.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now(), 'remember_device': '1'})
        elif entry == 'change':
            response = client.post('/auth/change-password', data={'current_password': PASSWORD,
                                   'new_password': NEW, 'confirm_password': NEW})
        else:
            response = client.post('/auth/activate/' + raw, data={'new_password': NEW, 'confirm_password': NEW})
    assert response.location.endswith('/auth/login')
    assert client.get('/member/profile').status_code == 302
