"""A-076: initial passwords cannot open protected views or execute mutations."""
from tests.action_confirmation_helpers import confirmed_post

from tests.conftest import auth_id, device_grant
import base64
from datetime import datetime
from unittest.mock import Mock
from urllib.parse import urlencode

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService

OLD = 'Initial-Synthetic-Password1!'
NEW = 'New-Synthetic-Password2!'
SECRET = 'JBSWY3DPEHPK3PXP'
TARGET = '/member/profile?tab=details#contact'


@pytest.fixture
def pending(app):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        user = Member(vorname='Pending', nachname='Change', email='pending@example.com',
                      passwort_hash=SecurityService.hash_password(OLD), role=Role.ADMIN,
                      password_changed_at=None)
        db.session.add(user)
        db.session.commit()
        return user.id


def login(client, next=TARGET):
    return client.post('/auth/login?' + urlencode({'next': next}),
                       data={'email': 'pending@example.com', 'password': OLD})


def change(client, **overrides):
    data = {'current_password': OLD, 'new_password': NEW, 'confirm_password': NEW}
    data.update(overrides)
    return confirmed_post(client, '/auth/change-password', data=data, password=OLD)


def session_login(client, uid):
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True


@pytest.mark.parametrize('method', ['password', 'totp', 'backup', 'remembered', 'removed_mfa'])
def test_every_login_path_requires_change_and_retains_target(app, client, pending, method):
    if method != 'password':
        with app.app_context():
            db.session.add(MemberMFA(member_id=pending, is_totp_enabled=True,
                                    totp_secret_encrypted=SecurityService.encrypt_json(SECRET)))
            db.session.add(MFABackupCode(member_id=pending,
                                        code_hash=SecurityService.hash_backup_code('AB12CD34')))
            db.session.commit()
    if method == 'remembered':
        with client.session_transaction() as state:
            state['remembered_device'] = device_grant(client, pending)
    response = login(client)
    if method in ('totp', 'backup', 'removed_mfa'):
        assert response.location.endswith('/auth/2fa/verify')
        with client.session_transaction() as state:
            assert '_user_id' not in state
        if method == 'removed_mfa':
            with app.app_context():
                MemberMFA.query.one().is_totp_enabled = False
                db.session.commit()
            response = client.get('/auth/2fa/verify')
            assert response.location.endswith('/auth/login')
            with client.session_transaction() as state:
                assert '_user_id' not in state
            response = login(client)
        else:
            data = {'token': pyotp.TOTP(SECRET).now()} if method == 'totp' else {'backup_code': 'AB12CD34'}
            response = client.post('/auth/2fa/verify', data=data)
    assert response.location.endswith('/auth/change-password')
    assert client.get('/member/profile').location.endswith('/auth/change-password')
    assert client.get('/auth/change-password').status_code == 200
    assert change(client).location == TARGET
    with app.app_context():
        assert not db.session.get(Member, pending).needs_password_change
    with client.session_transaction() as state:
        assert state['_user_id'] == auth_id(client, pending)
        assert 'password_change_return' not in state
    assert client.get('/member/profile').status_code == 200


@pytest.mark.parametrize('path', ['/member/profile', '/admin/', '/events/', '/ggl/',
                                  '/docs/', '/accounting/', '/auth/step-up',
                                  '/auth/2fa/enroll', '/auth/2fa/backup-codes'])
def test_direct_gets_are_blocked_even_for_admin(app, client, pending, path):
    session_login(client, pending)
    response = client.get(path)
    assert response.status_code == 302
    assert response.location.endswith('/auth/change-password')
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('json_api', [False, True])
def test_mutation_never_runs_or_becomes_return_target(app, client, pending, json_api):
    view = Mock(return_value='mutation ran')
    app.add_url_rule('/_write_probe', view_func=lambda: view(), endpoint='write_probe', methods=['POST'])
    session_login(client, pending)
    response = client.post('/_write_probe', **({'json': {'value': 1}} if json_api else {}))
    assert response.status_code == (403 if json_api else 303)
    if json_api:
        assert response.json['error'] == 'password_change_required'
        assert response.json['next'] == '/auth/change-password'
    view.assert_not_called()
    assert change(client).location.endswith('/dashboard/')
    view.assert_not_called()


def test_api_get_returns_403_without_saving_poll_target(client, pending):
    session_login(client, pending)
    response = client.get('/api/push/subscription-status')
    assert response.status_code == 403
    assert response.json['error'] == 'password_change_required'
    with client.session_transaction() as state:
        assert 'password_change_return' not in state


@pytest.mark.parametrize('target', ['/member/profile?tab=details', '/member/profile?value=why?'])
def test_direct_navigation_remembered_but_later_request_does_not_replace_it(client, pending, target):
    session_login(client, pending)
    assert client.get(target).status_code == 302
    client.get('/admin/')
    assert change(client).location == target


@pytest.mark.parametrize('target', ['//evil.example', '/\\evil.example', '/auth/change-password',
                                     '/auth/logout', 'https://evil.example'])
def test_invalid_or_auth_target_does_not_survive_change(client, pending, target):
    assert login(client, target).location.endswith('/auth/change-password')
    assert change(client).location.endswith('/dashboard/')


@pytest.mark.parametrize('bad', [dict(current_password='wrong'), dict(new_password='short', confirm_password='short'),
                               dict(new_password=OLD, confirm_password=OLD), dict(confirm_password='different')])
def test_failed_password_change_keeps_restriction_and_target(app, client, pending, bad):
    login(client)
    assert change(client, **bad).status_code == 200
    with app.app_context():
        assert db.session.get(Member, pending).needs_password_change
    assert client.get('/member/profile').location.endswith('/auth/change-password')
    assert change(client).location == TARGET


def test_commit_failure_keeps_restriction_and_target(app, client, pending, monkeypatch):
    login(client)
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
        with pytest.raises(RuntimeError):
            change(client)
    with app.app_context():
        assert db.session.get(Member, pending).needs_password_change
        assert db.session.get(Member, pending).check_password(OLD)
    assert change(client).location == TARGET


def test_logout_and_new_login_discard_old_destination(client, pending):
    login(client)
    assert client.get('/auth/logout').status_code == 302
    with client.session_transaction() as state:
        assert 'password_change_return' not in state
    login(client, '/events/')
    assert change(client).location == '/events/'


@pytest.mark.parametrize('stored', [{'member_id': -1, 'target': TARGET},
                                   {'target': TARGET}, 'malformed',
                                   {'member_id': 'CURRENT', 'target': '//evil.example'}])
def test_foreign_or_malformed_session_target_is_discarded(client, pending, stored):
    session_login(client, pending)
    if isinstance(stored, dict) and stored.get('member_id') == 'CURRENT':
        stored = dict(stored, member_id=pending)
    with client.session_transaction() as state:
        state['password_change_return'] = stored
    assert change(client).location.endswith('/dashboard/')


def test_restriction_applies_to_existing_session_when_flag_changes(app, client, pending):
    with app.app_context():
        db.session.get(Member, pending).password_changed_at = datetime.utcnow()
        db.session.commit()
    session_login(client, pending)
    assert client.get('/member/profile').status_code == 200
    with app.app_context():
        db.session.get(Member, pending).password_changed_at = None
        db.session.commit()
    assert client.get('/member/profile').location.endswith('/auth/change-password')


@pytest.mark.parametrize('path,status', [('/?show=1', 200), ('/ueber-uns', 200), ('/health', 200),
                                       ('/sw.js', 200), ('/static/manifest.json', 200),
                                       ('/auth/reset-password/invalid', 302),
                                       ('/auth/activate/invalid', 302), ('/auth/2fa/reset/invalid', 302)])
def test_public_assets_and_token_routes_do_not_loop_to_change(client, pending, path, status):
    session_login(client, pending)
    response = client.get(path)
    assert response.status_code == status
    assert response.location != '/auth/change-password'


def test_csrf_still_required_for_change(app, client, pending):
    session_login(client, pending)
    app.config['WTF_CSRF_ENABLED'] = True
    assert change(client).status_code == 400
    with app.app_context():
        assert db.session.get(Member, pending).needs_password_change


def test_remember_cookie_restores_restriction_and_clears_old_target(client, pending):
    client.post('/auth/login?' + urlencode({'next': TARGET}),
                data={'email': 'pending@example.com', 'password': OLD, 'remember_me': 'y'})
    with client.session_transaction() as state:
        state.pop('_user_id')
        state.pop('_fresh', None)
    response = client.get('/member/profile')
    assert response.location.endswith('/auth/change-password')
    with client.session_transaction() as state:
        assert state['password_change_return'] == {'member_id': pending, 'target': '/member/profile'}
    assert change(client).location == '/member/profile'


def test_real_admin_mutation_blocked_before_member_update(app, client, pending):
    session_login(client, pending)
    response = confirmed_post(client, f'/admin/members/{pending}/edit', data={
        'vorname': 'Changed', 'nachname': 'Name', 'email': 'pending@example.com',
        'role': 'ADMIN', 'is_active': 'y', 'funktion': 'MEMBER',
    }, password=OLD)
    assert response.status_code == 303
    with app.app_context():
        assert db.session.get(Member, pending).vorname == 'Pending'


def test_json_navigation_cannot_pollute_return_target(client, pending):
    session_login(client, pending)
    assert client.get('/member/profile', headers={'Accept': 'application/json'}).status_code == 403
    assert change(client).location.endswith('/dashboard/')
