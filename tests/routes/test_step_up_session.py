"""A-075: sensitive access belongs to one authenticated account/session."""

from datetime import datetime

import time

import pytest
from flask_login import login_user, logout_user

from backend.extensions import db
from backend.models.member import Member
from backend.services.security import SecurityService


PASSWORD = 'Synthetic-session-password'
TRANSIENTS = ('sensitive_access_until', 'sensitive_access_member_id',
              '2fa_secret', 'pending_2fa_user_id', 'pending_2fa_next', 'step_up_next')


@pytest.fixture
def accounts(app):
    with app.app_context():
        password_hash = SecurityService.hash_password(PASSWORD)
        members = [Member(password_changed_at=datetime(2026, 1, 1),
                          vorname='Session', nachname=str(i), email=f'session{i}@example.com',
                          passwort_hash=password_hash) for i in range(2)]
        db.session.add_all(members)
        db.session.commit()
        return [member.id for member in members]


def login(client, index):
    assert client.post('/auth/login', data={
        'email': f'session{index}@example.com', 'password': PASSWORD,
    }).status_code == 302


def grant(client):
    response = client.post('/auth/step-up', data={
        'password': PASSWORD, 'next': '/member/profile?tab=sensitive',
    })
    assert response.status_code == 302
    assert client.get('/member/profile?tab=sensitive').status_code == 200


def assert_needs_step_up(client):
    response = client.get('/member/profile?tab=sensitive')
    assert response.status_code == 302
    assert '/auth/step-up' in response.location


@pytest.mark.parametrize('next_account', [0, 1])
def test_logout_requires_new_confirmation(client, accounts, next_account):
    login(client, 0)
    grant(client)
    with client.session_transaction() as session:
        session['2fa_secret'] = 'SYNTHETIC-ENROLLMENT'
        session['pending_2fa_user_id'] = accounts[0]
        session['step_up_next'] = '/member/profile?tab=sensitive'
        session['unrelated_preference'] = 'preserved'
    assert client.get('/auth/logout').status_code == 302
    with client.session_transaction() as session:
        assert not any(key in session for key in TRANSIENTS)
        assert session['unrelated_preference'] == 'preserved'
    login(client, next_account)
    assert_needs_step_up(client)
    grant(client)
    with client.session_transaction() as session:
        assert session['sensitive_access_member_id'] == str(accounts[next_account])


@pytest.mark.parametrize('state', ['legacy', 'other_account', 'expired', 'malformed'])
def test_stale_or_invalid_grant_is_rejected(client, accounts, state):
    login(client, 0)
    with client.session_transaction() as session:
        session['sensitive_access_until'] = int(time.time()) + 600
        if state != 'legacy':
            session['sensitive_access_member_id'] = str(accounts[1] if state == 'other_account' else accounts[0])
        if state == 'expired':
            session['sensitive_access_until'] = int(time.time()) - 1
        if state == 'malformed':
            session['sensitive_access_until'] = 'invalid'
    assert_needs_step_up(client)
    with client.session_transaction() as session:
        assert 'sensitive_access_until' not in session
        assert 'sensitive_access_member_id' not in session


def test_login_clears_old_grant_without_prior_logout(client, accounts):
    with client.session_transaction() as session:
        session['sensitive_access_until'] = int(time.time()) + 600
        session['sensitive_access_member_id'] = str(accounts[0])
        session['2fa_secret'] = 'SYNTHETIC-OLD-ENROLLMENT'
    login(client, 0)
    assert_needs_step_up(client)
    with client.session_transaction() as session:
        assert '2fa_secret' not in session


def test_account_switch_cannot_reuse_grant(client, accounts):
    login(client, 0)
    grant(client)
    # Simulate a changed account identity without the normal login/logout hooks.
    with client.session_transaction() as session:
        session['_user_id'] = str(accounts[1])
    assert_needs_step_up(client)


def test_wrong_password_does_not_grant_access(client, accounts):
    login(client, 0)
    assert client.post('/auth/step-up', data={'password': 'wrong'}).status_code == 200
    assert_needs_step_up(client)


def test_grant_uses_configured_ttl(app, client, accounts, monkeypatch):
    app.config['SENSITIVE_ACCESS_TTL_SECONDS'] = 45
    monkeypatch.setattr(time, 'time', lambda: 1800000000)
    login(client, 0)
    grant(client)
    with client.session_transaction() as session:
        assert session['sensitive_access_until'] == 1800000045
        assert session['sensitive_access_member_id'] == str(accounts[0])


@pytest.mark.parametrize('event', ['login', 'logout', 'cookie_restore'])
def test_auth_lifecycle_clears_transients(app, accounts, event):
    from flask import session
    from flask_login import user_loaded_from_cookie

    with app.test_request_context('/'):
        member = db.session.get(Member, accounts[0])
        login_user(member)
        for key in TRANSIENTS:
            session[key] = 'SYNTHETIC-STALE'
        if event == 'login':
            login_user(member)
        elif event == 'logout':
            logout_user()
        else:
            user_loaded_from_cookie.send(app, user=member)
        assert not any(key in session for key in TRANSIENTS)


def test_remember_cookie_restores_login_without_sensitive_access(app, client, accounts):
    assert client.post('/auth/login', data={
        'email': 'session0@example.com', 'password': PASSWORD, 'remember_me': 'y',
    }).status_code == 302
    grant(client)
    client.delete_cookie(app.config['SESSION_COOKIE_NAME'])
    assert_needs_step_up(client)
    with client.session_transaction() as session:
        assert session['_user_id'] == str(accounts[0])
        assert 'sensitive_access_until' not in session
    grant(client)


def test_second_browser_needs_its_own_confirmation(app, client, accounts):
    login(client, 0)
    grant(client)
    other_browser = app.test_client()
    login(other_browser, 0)
    assert_needs_step_up(other_browser)
    assert client.get('/member/profile?tab=sensitive').status_code == 200


def test_anonymous_context_cannot_grant_access(app):
    from flask import session

    with app.test_request_context('/'):
        SecurityService.grant_step_up_access()
        assert not SecurityService.check_step_up_access()
        assert 'sensitive_access_until' not in session
        assert 'sensitive_access_member_id' not in session
