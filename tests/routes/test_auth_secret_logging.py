"""Original auth routes: logging must not disclose synthetic credentials."""

from datetime import datetime

import logging

import pyotp
import pytest
from cryptography.fernet import Fernet

from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.services.security import SecurityService


@pytest.fixture
def auth_actor(app, client):
    app.config['CRYPTO_KEY'] = Fernet.generate_key().decode()
    with app.app_context():
        member = Member(password_changed_at=datetime(2026, 1, 1),
                        vorname='Log', nachname='Test', email='synthetic-log@example.test',
                        passwort_hash=SecurityService.hash_password('Synthetic-password-private'))
        db.session.add(member)
        db.session.commit()
        member_id = member.id
    with client.session_transaction() as session:
        session['_user_id'] = str(member_id)
        session['_fresh'] = True
    return member_id


def assert_not_logged(caplog, *secrets):
    records = '\n'.join(str(record.__dict__) for record in caplog.records)
    for secret in secrets:
        assert secret not in caplog.text
        assert secret not in records


@pytest.mark.parametrize('existing', [False, True])
def test_enrollment_preserves_flow_without_logging_secret(app, client, auth_actor, caplog, existing):
    if existing:
        with client.session_transaction() as session:
            session['2fa_secret'] = pyotp.random_base32()
    with caplog.at_level(logging.INFO):
        assert client.get('/auth/2fa/enroll').status_code == 200
        with client.session_transaction() as session:
            secret = session['2fa_secret']
        assert client.post('/auth/2fa/enroll', data={'token': 'abcdef'}).status_code == 200
        code = pyotp.TOTP(secret).now()
        assert client.post('/auth/2fa/enroll', data={'token': code}).status_code == 200
    with app.app_context():
        row = MemberMFA.query.filter_by(member_id=auth_actor).one()
        assert row.is_totp_enabled
        assert SecurityService.decrypt_json(row.totp_secret_encrypted) == secret
    assert_not_logged(caplog, secret, code, 'abcdef', 'synthetic-log@example.test')


@pytest.mark.parametrize('valid', [False, True])
def test_mfa_login_does_not_log_codes(app, client, auth_actor, caplog, valid):
    secret = pyotp.random_base32()
    with app.app_context():
        db.session.add(MemberMFA(member_id=auth_actor, is_totp_enabled=True,
                                totp_secret_encrypted=SecurityService.encrypt_json(secret)))
        db.session.commit()
    with client.session_transaction() as session:
        session.clear()
        session['pending_2fa_user_id'] = auth_actor
    current_code = pyotp.TOTP(secret).now()
    token = current_code if valid else 'abcdef'
    with caplog.at_level(logging.INFO):
        response = client.post('/auth/2fa/verify', data={'token': token})
    assert response.status_code == (302 if valid else 200)
    with client.session_transaction() as session:
        assert ('_user_id' in session) is valid
    assert_not_logged(caplog, secret, current_code, token)


@pytest.mark.parametrize('valid', [False, True])
def test_step_up_does_not_log_password_or_return_token(app, client, auth_actor, caplog, valid):
    password = 'Synthetic-password-private' if valid else 'Synthetic-wrong-password'
    target = '/member/profile?token=synthetic-return-token'
    with caplog.at_level(logging.INFO):
        response = client.post('/auth/step-up', data={'password': password, 'next': target})
    assert response.status_code == (302 if valid else 200)
    if valid:
        assert response.location == target
    with client.session_transaction() as session:
        assert ('sensitive_access_until' in session) is valid
    assert_not_logged(caplog, password, 'synthetic-return-token')
