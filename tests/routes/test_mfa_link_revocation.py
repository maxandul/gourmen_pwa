"""A-141 MFA scope: stale recovery links cannot disable a newly configured factor."""
import base64
import hashlib
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.services.security import SecurityService
from backend.services.mail import MailService

PASSWORD = 'Synthetic-MFA-password'
SECRET = 'JBSWY3DPEHPK3PXP'
NEW_SECRET = 'KRSXG5DSNFXGOIDB'
OLD_LINKS = ('synthetic-old-mfa-link-one', 'synthetic-old-mfa-link-two')


@pytest.fixture
def mfa_case(app, monkeypatch):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    monkeypatch.setattr(MailService, 'send_async', Mock())
    monkeypatch.setattr(SecurityService, 'log_audit_event', Mock())
    with app.app_context():
        member = Member(vorname='MFA', nachname='Links', email='mfa-links@example.com', role=Role.ADMIN)
        member.set_password(PASSWORD)
        db.session.add(member)
        db.session.flush()
        uid = member.id
        db.session.add(MemberMFA(member_id=uid, is_totp_enabled=True,
                                totp_secret_encrypted=SecurityService.encrypt_json(SECRET)))
        db.session.add(MFABackupCode(member_id=uid, code_hash='synthetic-old-backup'))
        for raw in OLD_LINKS:
            db.session.add(AuthToken(member_id=uid, token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                                    purpose=AuthTokenPurpose.MFA_RESET,
                                    expires_at=datetime.utcnow() + timedelta(hours=1)))
        from backend.routes.auth import _issue_auth_token
        for purpose in (AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.ONBOARDING,
                        AuthTokenPurpose.GOOGLE_EMAIL_VERIFY):
            _issue_auth_token(uid, purpose, timedelta(days=1), None)
        db.session.commit()
    return uid


def login(client, uid):
    with client.session_transaction() as state:
        state['_user_id'] = str(uid)
        state['_fresh'] = True
        state['sensitive_access_member_id'] = str(uid)
        state['sensitive_access_until'] = time.time() + 600


def enroll(client):
    with client.session_transaction() as state:
        state['2fa_secret'] = NEW_SECRET
    return client.post('/auth/2fa/enroll', data={'token': pyotp.TOTP(NEW_SECRET).now()})


@pytest.mark.parametrize('entry', ['mail_reset', 'admin_reset', 'disable', 'enroll'])
def test_factor_change_revokes_old_links_and_preserves_new_factor(app, client, mfa_case, entry):
    uid = mfa_case
    if entry == 'mail_reset':
        response = client.post('/auth/2fa/reset/' + OLD_LINKS[0], data={'confirm': 'y'})
    else:
        login(client, uid)
        if entry == 'admin_reset':
            response = client.post(f'/admin/members/{uid}/reset-2fa', data={'confirm': 'RESET'})
        elif entry == 'disable':
            response = client.post('/auth/2fa/disable', data={'password': PASSWORD})
        else:
            with app.app_context():
                MemberMFA.query.one().is_totp_enabled = False
                db.session.commit()
            response = enroll(client)
    assert response.status_code == (200 if entry == 'enroll' else 302)
    with app.app_context():
        assert all(row.used_at is not None for row in AuthToken.query.filter_by(purpose=AuthTokenPurpose.MFA_RESET))
        assert all(row.used_at is None for row in AuthToken.query.filter(AuthToken.purpose != AuthTokenPurpose.MFA_RESET))
    if entry != 'enroll':
        login(client, uid)
        assert enroll(client).status_code == 200
    with app.app_context():
        db.session.add(MFABackupCode(member_id=uid, code_hash='synthetic-new-backup'))
        db.session.commit()
        encrypted = MemberMFA.query.one().totp_secret_encrypted
        codes = [(r.id, r.code_hash, r.revoked_at) for r in MFABackupCode.query.all()]
    with client.session_transaction() as state:
        state.clear()
    for token in OLD_LINKS:
        client.post('/auth/2fa/reset/' + token, data={'confirm': 'y'})
        with app.app_context():
            assert MemberMFA.query.one().is_totp_enabled
            assert MemberMFA.query.one().totp_secret_encrypted == encrypted
            assert [(r.id, r.code_hash, r.revoked_at) for r in MFABackupCode.query.all()] == codes


def test_resend_replaces_previous_mfa_links_only(app, client, mfa_case):
    import re
    links = []
    for _ in range(2):
        client.post('/auth/2fa/reset-request', data={'email': 'mfa-links@example.com'})
        text = MailService.send_async.call_args.kwargs['text']
        links.append(re.search(r'/auth/2fa/reset/([^\s]+)', text).group(1))
    client.post('/auth/2fa/reset/' + links[0], data={'confirm': 'y'})
    with app.app_context():
        assert MemberMFA.query.one().is_totp_enabled
    client.post('/auth/2fa/reset/' + links[1], data={'confirm': 'y'})
    with app.app_context():
        assert not MemberMFA.query.one().is_totp_enabled
        assert all(row.used_at is None for row in AuthToken.query.filter(AuthToken.purpose != AuthTokenPurpose.MFA_RESET))


@pytest.mark.parametrize('entry', ['disable', 'enroll'])
def test_invalid_proof_does_not_revoke(app, client, mfa_case, entry):
    login(client, mfa_case)
    if entry == 'disable':
        response = client.post('/auth/2fa/disable', data={'password': 'wrong'})
    else:
        with app.app_context():
            MemberMFA.query.one().is_totp_enabled = False
            db.session.commit()
        response = client.post('/auth/2fa/enroll', data={'token': 'invalid'})
    assert response.status_code == 200
    with app.app_context():
        assert all(row.used_at is None for row in AuthToken.query.all())


def test_admin_reset_revokes_even_when_already_disabled(app, client, mfa_case):
    with app.app_context():
        MemberMFA.query.one().is_totp_enabled = False
        db.session.commit()
    login(client, mfa_case)
    client.post(f'/admin/members/{mfa_case}/reset-2fa', data={'confirm': 'RESET'})
    with app.app_context():
        assert all(row.used_at is not None for row in AuthToken.query.filter_by(purpose=AuthTokenPurpose.MFA_RESET))


@pytest.mark.parametrize('entry', ['mail_reset', 'enroll'])
def test_commit_failure_keeps_factor_codes_and_links(app, client, mfa_case, monkeypatch, entry):
    if entry == 'enroll':
        login(client, mfa_case)
        with app.app_context():
            MemberMFA.query.one().is_totp_enabled = False
            db.session.commit()
    with app.app_context():
        old_secret = MemberMFA.query.one().totp_secret_encrypted
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic commit failure')))
        with pytest.raises(RuntimeError):
            if entry == 'enroll':
                enroll(client)
            else:
                client.post('/auth/2fa/reset/' + OLD_LINKS[0], data={'confirm': 'y'})
    with app.app_context():
        assert MemberMFA.query.one().is_totp_enabled == (entry == 'mail_reset')
        assert MemberMFA.query.one().totp_secret_encrypted == old_secret
        assert MFABackupCode.query.count() == 1
        assert all(row.used_at is None for row in AuthToken.query.all())


@pytest.mark.parametrize('intervening', ['revoke', 'expire', 'deactivate'])
def test_reset_rechecks_after_confirmation(app, client, mfa_case, monkeypatch, intervening):
    from backend.routes.auth import ConfirmMFAResetForm
    validate = ConfirmMFAResetForm.validate_on_submit
    def validate_then_change(form):
        valid = validate(form)
        if intervening == 'deactivate':
            db.session.get(Member, mfa_case).is_active = False
        else:
            row = AuthToken.query.filter_by(token_hash=hashlib.sha256(OLD_LINKS[0].encode()).hexdigest()).one()
            if intervening == 'revoke':
                row.used_at = datetime.utcnow()
            else:
                row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
        return valid
    monkeypatch.setattr(ConfirmMFAResetForm, 'validate_on_submit', validate_then_change)
    client.post('/auth/2fa/reset/' + OLD_LINKS[0], data={'confirm': 'y'})
    with app.app_context():
        assert MemberMFA.query.one().is_totp_enabled
        assert MFABackupCode.query.count() == 1


def test_enrollment_does_not_replace_intervening_activation(app, client, mfa_case, monkeypatch):
    from backend.routes.auth import TOTPForm
    login(client, mfa_case)
    with app.app_context():
        MemberMFA.query.one().is_totp_enabled = False
        db.session.commit()
    validate = TOTPForm.validate_on_submit
    def validate_then_activate(form):
        valid = validate(form)
        MemberMFA.query.one().is_totp_enabled = True
        db.session.commit()
        return valid
    monkeypatch.setattr(TOTPForm, 'validate_on_submit', validate_then_activate)
    enroll(client)
    with app.app_context():
        assert SecurityService.decrypt_json(MemberMFA.query.one().totp_secret_encrypted) == SECRET


def test_other_member_reset_link_is_untouched(app, client, mfa_case):
    with app.app_context():
        other = Member(password_changed_at=datetime(2026, 1, 1),
                       vorname='Other', nachname='MFA', email='other-mfa@example.com', passwort_hash='unused')
        db.session.add(other)
        db.session.flush()
        row = AuthToken(member_id=other.id, purpose=AuthTokenPurpose.MFA_RESET,
                        token_hash='synthetic-other-hash', expires_at=datetime.utcnow() + timedelta(hours=1))
        db.session.add(row)
        db.session.commit()
        row_id = row.id
    client.post('/auth/2fa/reset/' + OLD_LINKS[0], data={'confirm': 'y'})
    with app.app_context():
        assert db.session.get(AuthToken, row_id).used_at is None


def test_issue_rollback_preserves_existing_mfa_links(app, mfa_case):
    from backend.routes.auth import _issue_auth_token
    with app.app_context():
        _issue_auth_token(mfa_case, AuthTokenPurpose.MFA_RESET, timedelta(hours=1), None)
        db.session.rollback()
        assert AuthToken.query.filter_by(purpose=AuthTokenPurpose.MFA_RESET).count() == 2
        assert all(row.used_at is None for row in AuthToken.query.all())
