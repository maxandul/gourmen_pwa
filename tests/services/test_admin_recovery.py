"""Synthetic hosting recovery: transaction, retained data and revoked access."""
from datetime import datetime, timedelta
import base64
import pyotp
from tests.action_confirmation_helpers import confirmed_post
from unittest.mock import Mock

import pytest

from backend.extensions import db
from backend.models.audit_event import AuditEvent
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.member import Member, Role
from backend.models.member_mfa import MemberMFA
from backend.models.member_sensitive import MemberSensitive
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.admin_recovery import AdminRecoveryService

OLD = 'Synthetic-old-password1!'
NEW = 'Synthetic-new-password2!'


@pytest.fixture
def target(app):
    app.config["CRYPTO_KEY"] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        member = Member(vorname='Synthetic', nachname='Admin', email='admin@example.com', role=Role.ADMIN)
        member.set_password(OLD)
        db.session.add(member)
        db.session.flush()
        uid, generation = member.id, member.auth_generation
        db.session.add(MemberMFA(member_id=uid, is_totp_enabled=True, totp_secret_encrypted='retained-secret'))
        db.session.add(MemberSensitive(member_id=uid, payload_encrypted='retained-ciphertext'))
        db.session.add(MFABackupCode(member_id=uid, code_hash='old-code-hash'))
        for purpose in AuthTokenPurpose:
            db.session.add(AuthToken(member_id=uid, token_hash=purpose.value, purpose=purpose,
                                     expires_at=datetime.utcnow()+timedelta(hours=1)))
        db.session.commit()
        return uid, generation


def run(app, target, *options, confirmation=None):
    uid, _ = target
    entered = f'{NEW}\n{NEW}\nsynthetic-operator\nsynthetic-case\n{confirmation or f"RECOVER {uid}"}\n'
    return app.test_cli_runner().invoke(args=['admin-recover', '--member-id', str(uid), *options], input=entered)


@pytest.mark.parametrize('reset', [False, True])
def test_success_revokes_access_without_changing_role_or_sensitive_data(app, client, target, caplog, reset):
    uid, generation = target
    with client.session_transaction() as state:
        state['_user_id'] = f'{uid}:{generation}'
        state['_fresh'] = True
    result = run(app, target, '--apply', *(['--reset-mfa'] if reset else []))
    assert result.exit_code == 0, result.output
    assert 'gespeichert' in result.output
    assert NEW not in result.output + caplog.text
    with app.app_context():
        member = db.session.get(Member, uid)
        assert member.check_password(NEW) and not member.check_password(OLD)
        assert member.is_admin() and member.is_active
        assert member.auth_generation != generation
        assert Member.query.count() == 1
        assert MemberSensitive.query.one().payload_encrypted == 'retained-ciphertext'
        mfa = MemberMFA.query.one()
        assert mfa.is_totp_enabled is not reset
        assert mfa.totp_secret_encrypted == (None if reset else 'retained-secret')
        assert (MFABackupCode.query.one().revoked_at is not None) is reset
        assert all(row.used_at for row in AuthToken.query.all())
        audits = AuditEvent.query.all()
        assert len(audits) == (2 if reset else 1)
        assert all(row.extra_json['source'] == 'hosting_cli' for row in audits)
        assert NEW not in str([row.extra_json for row in audits])
    assert '/auth/login' in client.get('/dashboard/').location
    if reset:
        assert client.post('/auth/login', data={'email':'admin@example.com', 'password':NEW}).status_code == 302
        with client.session_transaction() as state:
            assert state.get('_user_id', '').startswith(f'{uid}:')
            state['2fa_secret'] = 'JBSWY3DPEHPK3PXP'
        enrolled = confirmed_post(client, '/auth/2fa/enroll',
            data={'token': pyotp.TOTP('JBSWY3DPEHPK3PXP').now()}, password=NEW)
        assert enrolled.status_code == 200
        assert 'Diese Codes werden nur einmal angezeigt' in enrolled.text
        with app.app_context():
            assert MemberMFA.query.one().is_totp_enabled
            assert MFABackupCode.query.filter_by(revoked_at=None, used_at=None).count() == 10


def assert_unchanged(app, target):
    uid, generation = target
    with app.app_context():
        member = db.session.get(Member, uid)
        assert member.auth_generation == generation and member.check_password(OLD)
        assert MemberMFA.query.one().is_totp_enabled
        assert MFABackupCode.query.one().revoked_at is None
        assert all(row.used_at is None for row in AuthToken.query.all())
        assert AuditEvent.query.count() == 0


def test_preview_never_mutates(app, target):
    result = run(app, target, '--reset-mfa')
    assert result.exit_code == 0 and 'Vorschau' in result.output
    assert_unchanged(app, target)


def test_wrong_confirmation_aborts(app, target):
    assert run(app, target, '--apply', confirmation='wrong').exit_code != 0
    assert_unchanged(app, target)


def test_eof_aborts(app, target):
    result = app.test_cli_runner().invoke(args=['admin-recover', '--member-id', str(target[0]), '--apply'], input='')
    assert result.exit_code != 0
    assert_unchanged(app, target)


@pytest.mark.parametrize('change', ['member', 'inactive', 'missing'])
def test_only_existing_active_admin_can_be_recovered(app, target, change):
    uid, _ = target
    with app.app_context():
        member = db.session.get(Member, uid)
        if change == 'member':
            member.role = Role.MEMBER
        elif change == 'inactive':
            member.is_active = False
        db.session.commit()
    chosen = (999, '') if change == 'missing' else target
    result = run(app, chosen, '--apply', '--reset-mfa')
    assert result.exit_code != 0 and 'kein aktiver Systemadmin' in result.output
    assert_unchanged(app, target)


@pytest.mark.parametrize('field,value', [('password','short'), ('password',OLD), ('operator',''), ('reason',''), ('reason','x'*501)])
def test_invalid_input_rejected_before_mutation(app, target, field, value):
    uid, generation = target
    values = dict(password=NEW, operator='operator', reason='reason')
    values[field] = value
    with app.app_context():
        with pytest.raises(ValueError):
            AdminRecoveryService.recover(uid, generation, **values, reset_mfa=True)
        db.session.rollback()
    assert_unchanged(app, target)


def test_changed_generation_wins(app, target):
    uid, generation = target
    with app.app_context():
        member = db.session.get(Member, uid)
        member.rotate_auth_generation()
        db.session.commit()
        changed = member.auth_generation
        with pytest.raises(ValueError, match='zwischenzeitlich'):
            AdminRecoveryService.recover(uid, generation, NEW, 'operator', 'reason', reset_mfa=True)
        db.session.rollback()
    assert_unchanged(app, (uid, changed))


def test_commit_failure_rolls_back_password_mfa_links_and_audit(app, target, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic database failure')))
        result = run(app, target, '--apply', '--reset-mfa')
    assert result.exit_code != 0 and 'nicht bestätigt' in result.output
    assert 'synthetic database failure' not in result.output
    assert_unchanged(app, target)
