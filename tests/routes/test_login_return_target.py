"""A-078: keep a safe return target through the password/MFA boundary."""
from datetime import datetime
import base64
from urllib.parse import urlencode

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService

PASSWORD = 'Synthetic-return-password'
SECRET = 'JBSWY3DPEHPK3PXP'
TARGET = '/member/profile?tab=details#contact'


@pytest.fixture
def account(app):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        user = Member(vorname='Return', nachname='Test', email='return@example.com',
                      passwort_hash=SecurityService.hash_password(PASSWORD),
                      password_changed_at=datetime.utcnow())
        db.session.add(user)
        db.session.flush()
        db.session.add(MemberMFA(member_id=user.id, is_totp_enabled=True,
                                totp_secret_encrypted=SecurityService.encrypt_json(SECRET)))
        db.session.add(MFABackupCode(member_id=user.id,
                                    code_hash=SecurityService.hash_backup_code('AB12CD34')))
        db.session.commit()
        return user.id


def start(client, target=TARGET, password=PASSWORD):
    return client.post('/auth/login?' + urlencode({'next': target}),
                       data={'email': 'return@example.com', 'password': password})


@pytest.mark.parametrize('method', ['totp', 'backup', 'password', 'remembered'])
def test_login_returns_to_original_target(app, client, account, method):
    if method == 'password':
        with app.app_context():
            MemberMFA.query.filter_by(member_id=account).first().is_totp_enabled = False
            db.session.commit()
    if method == 'remembered':
        with client.session_transaction() as state:
            state['remembered_device'] = {'user_id': account, 'expires_at': 9999999999}
    response = start(client)
    if method in ('totp', 'backup'):
        assert response.location.endswith('/auth/2fa/verify')
        assert client.get('/auth/2fa/verify').status_code == 200
        assert client.post('/auth/2fa/verify', data={'token': 'bad'}).status_code == 200
        data = {'token': pyotp.TOTP(SECRET).now()} if method == 'totp' else {'backup_code': 'AB12CD34'}
        response = client.post('/auth/2fa/verify', data=data)
    assert response.location == TARGET
    with client.session_transaction() as state:
        assert state['_user_id'] == str(account)
        assert 'pending_2fa_next' not in state


def test_new_login_abandons_old_target(client, account):
    start(client)
    client.get('/auth/login')
    assert client.get('/auth/2fa/verify').location.endswith('/auth/login')
    start(client, target='')
    response = client.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now()})
    assert response.location.endswith('/dashboard') or response.location.endswith('/dashboard/')


def test_verify_query_cannot_replace_original_target(client, account):
    start(client)
    response = client.post('/auth/2fa/verify?next=//example.invalid',
                           data={'token': pyotp.TOTP(SECRET).now()})
    assert response.location == TARGET


def test_failed_new_password_attempt_clears_pending_login(client, account):
    start(client)
    assert start(client, password='wrong').status_code == 200
    response = client.post('/auth/2fa/verify', data={'token': pyotp.TOTP(SECRET).now()})
    assert response.location.endswith('/auth/login')
    with client.session_transaction() as state:
        assert 'pending_2fa_next' not in state
        assert '_user_id' not in state


def test_target_without_pending_account_is_discarded(client):
    with client.session_transaction() as state:
        state['pending_2fa_next'] = TARGET
    assert client.get('/auth/2fa/verify').location.endswith('/auth/login')
    with client.session_transaction() as state:
        assert 'pending_2fa_next' not in state


@pytest.mark.parametrize('target', ['https://example.invalid', '//example.invalid',
                                  '///example.invalid', '/\\example.invalid',
                                  '/%2fexample.invalid', '/%5cexample.invalid',
                                  '/\texample.invalid', ' /member/profile'])
@pytest.mark.parametrize('mfa', [True, False])
def test_unsafe_targets_fall_back(app, client, account, target, mfa):
    if not mfa:
        with app.app_context():
            MemberMFA.query.filter_by(member_id=account).first().is_totp_enabled = False
            db.session.commit()
    response = start(client, target)
    if mfa:
        response = client.post('/auth/2fa/verify', data={'backup_code': 'AB12CD34'})
    assert response.location.rstrip('/') == '/dashboard'
