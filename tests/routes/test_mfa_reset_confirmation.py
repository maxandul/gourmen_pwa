"""A-083: opening a reset link must never mutate MFA state."""
import hashlib
import re
from datetime import datetime, timedelta

import pytest

from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.auth_token import AuthToken, AuthTokenPurpose

TOKEN = 'synthetic-reset-token'
PATH = '/auth/2fa/reset/' + TOKEN


@pytest.fixture
def reset_case(app):
    app.config['WTF_CSRF_ENABLED'] = True
    with app.app_context():
        user = Member(password_changed_at=datetime(2026, 1, 1),
                      vorname='Reset', nachname='Test', email='reset@example.test', passwort_hash='unused')
        db.session.add(user)
        db.session.flush()
        db.session.add(MemberMFA(member_id=user.id, is_totp_enabled=True,
                                totp_secret_encrypted='synthetic-encrypted-payload'))
        db.session.add(MFABackupCode(member_id=user.id, code_hash='synthetic-hash'))
        token = AuthToken(member_id=user.id, purpose=AuthTokenPurpose.MFA_RESET, recipient_email=user.email,
                         token_hash=hashlib.sha256(TOKEN.encode()).hexdigest(),
                         expires_at=datetime.utcnow() + timedelta(hours=1))
        db.session.add(token)
        db.session.commit()
        return user.id, token.id


def snapshot(app):
    with app.app_context():
        mfa = MemberMFA.query.one()
        return (mfa.is_totp_enabled, mfa.totp_secret_encrypted,
                [(row.id, row.code_hash, row.used_at, row.revoked_at) for row in MFABackupCode.query.all()],
                AuthToken.query.one().used_at)


def csrf_from(response):
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.get_data(as_text=True)).group(1)


@pytest.mark.parametrize('method', ['get', 'head'])
def test_opening_link_preserves_all_state(app, client, reset_case, method):
    before = snapshot(app)
    response = getattr(client, method)(PATH)
    assert response.status_code == 200
    assert snapshot(app) == before
    if method == 'get':
        assert b'name="confirm"' in response.data
        assert csrf_from(response)


def test_confirm_once_then_reject_replay(app, client, reset_case):
    csrf = csrf_from(client.get(PATH))
    response = client.post(PATH, data={'csrf_token': csrf, 'confirm': 'y'})
    assert response.status_code == 302
    assert response.location.endswith('/auth/login')
    after = snapshot(app)
    assert after[:3] == (False, None, [])
    assert after[3] is not None
    assert client.post(PATH, data={'csrf_token': csrf, 'confirm': 'y'}).status_code == 302
    assert snapshot(app) == after


@pytest.mark.parametrize('csrf', [None, 'invalid'])
def test_post_without_valid_csrf_preserves_state(app, client, reset_case, csrf):
    before = snapshot(app)
    data = {'confirm': 'y'}
    if csrf:
        data['csrf_token'] = csrf
    assert client.post(PATH, data=data).status_code == 400
    assert snapshot(app) == before


def test_post_without_confirmation_preserves_state(app, client, reset_case):
    csrf = csrf_from(client.get(PATH))
    before = snapshot(app)
    assert client.post(PATH, data={'csrf_token': csrf}).status_code == 200
    assert snapshot(app) == before


@pytest.mark.parametrize('reason', ['expired', 'used', 'wrong_purpose', 'inactive'])
@pytest.mark.parametrize('method', ['get', 'post'])
def test_invalid_link_preserves_state(app, client, reset_case, reason, method):
    csrf = csrf_from(client.get(PATH))
    with app.app_context():
        row = db.session.get(AuthToken, reset_case[1])
        if reason == 'expired':
            row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        elif reason == 'used':
            row.used_at = datetime(2026, 1, 1)
        elif reason == 'wrong_purpose':
            row.purpose = AuthTokenPurpose.PASSWORD_RESET
        else:
            db.session.get(Member, reset_case[0]).is_active = False
        db.session.commit()
    before = snapshot(app)
    response = getattr(client, method)(PATH, data={'csrf_token': csrf, 'confirm': 'y'})
    assert response.status_code == 302
    assert snapshot(app) == before
