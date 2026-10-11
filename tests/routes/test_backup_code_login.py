"""A-079: hashed MFA recovery codes work once, only for their owner."""

from datetime import datetime

import pytest
from sqlalchemy.exc import SQLAlchemyError

from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService


CODE = 'AB12CD34'
PASSWORD = 'Synthetic-backup-password'


@pytest.fixture
def recovery(app, client):
    with app.app_context():
        user = Member(vorname='Recovery', nachname='Test', email='recovery@example.com',
                      passwort_hash=SecurityService.hash_password(PASSWORD),
                      password_changed_at=datetime.utcnow())
        other = Member(vorname='Other', nachname='Test', email='other@example.com', passwort_hash='unused')
        db.session.add_all([user, other])
        db.session.flush()
        db.session.add(MemberMFA(member_id=user.id, is_totp_enabled=True))
        row = MFABackupCode(member_id=user.id, code_hash=SecurityService.hash_backup_code(CODE))
        db.session.add(row)
        db.session.commit()
        ids = user.id, other.id, row.id
    response = client.post('/auth/login', data={'email': 'recovery@example.com', 'password': PASSWORD})
    assert response.status_code == 302
    assert '/auth/2fa/verify' in response.location
    return ids


def read_code(app, code_id):
    with app.app_context():
        row = db.session.get(MFABackupCode, code_id)
        return row.code_hash, row.used_at, row.revoked_at


def assert_not_authenticated(client):
    with client.session_transaction() as session:
        assert '_user_id' not in session


@pytest.mark.parametrize('submitted', [CODE, CODE.lower()])
def test_valid_code_logs_in_once(app, client, recovery, submitted, caplog):
    user_id, _, code_id = recovery
    before = read_code(app, code_id)
    assert client.post('/auth/2fa/verify', data={'backup_code': submitted}).status_code == 302
    with client.session_transaction() as session:
        assert session['_user_id'] == str(user_id)
        assert 'pending_2fa_user_id' not in session
    after = read_code(app, code_id)
    assert after[0] == before[0]
    assert after[1] is not None
    assert after[2] is None
    client.get('/auth/logout')
    client.post('/auth/login', data={'email': 'recovery@example.com', 'password': PASSWORD})
    assert client.post('/auth/2fa/verify', data={'backup_code': submitted}).status_code == 200
    assert_not_authenticated(client)
    assert read_code(app, code_id) == after
    assert CODE not in caplog.text
    assert before[0] not in caplog.text


@pytest.mark.parametrize('reason', ['wrong', 'used', 'revoked', 'foreign'])
def test_unusable_code_never_authenticates(app, client, recovery, reason):
    _, other_id, code_id = recovery
    with app.app_context():
        row = db.session.get(MFABackupCode, code_id)
        if reason == 'used':
            row.used_at = datetime.utcnow()
        elif reason == 'revoked':
            row.revoked_at = datetime.utcnow()
        elif reason == 'foreign':
            row.member_id = other_id
        db.session.commit()
    before = read_code(app, code_id)
    response = client.post('/auth/2fa/verify', data={'backup_code': 'WRONG123' if reason == 'wrong' else CODE})
    assert response.status_code == 200
    assert_not_authenticated(client)
    assert read_code(app, code_id) == before


def test_code_cannot_replace_password_step(app, client, recovery):
    fresh_client = app.test_client()
    before = read_code(app, recovery[2])
    response = fresh_client.post('/auth/2fa/verify', data={'backup_code': CODE})
    assert response.status_code == 302
    assert '/auth/login' in response.location
    assert_not_authenticated(fresh_client)
    assert read_code(app, recovery[2]) == before


def test_failed_commit_does_not_log_in_or_consume(app, client, recovery, monkeypatch):
    before = read_code(app, recovery[2])

    def fail_commit():
        raise SQLAlchemyError('Synthetic write failure')

    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', fail_commit)
        with pytest.raises(SQLAlchemyError):
            client.post('/auth/2fa/verify', data={'backup_code': CODE})
    assert_not_authenticated(client)
    assert read_code(app, recovery[2]) == before


@pytest.mark.parametrize('changed_field', ['used_at', 'revoked_at'])
def test_intervening_consumption_or_revocation_wins(app, client, recovery, monkeypatch, changed_field):
    code_id = recovery[2]
    original_check = SecurityService.check_backup_code

    def check_then_change(code_hash, submitted):
        matches = original_check(code_hash, submitted)
        if matches:
            # Deterministically inject the competing write after hash verification.
            row = db.session.get(MFABackupCode, code_id)
            setattr(row, changed_field, datetime(2026, 10, 1))
            db.session.commit()
        return matches

    monkeypatch.setattr(SecurityService, 'check_backup_code', check_then_change)
    response = client.post('/auth/2fa/verify', data={'backup_code': CODE})
    assert response.status_code == 200
    assert_not_authenticated(client)
    _, used_at, revoked_at = read_code(app, code_id)
    assert (used_at if changed_field == 'used_at' else revoked_at) == datetime(2026, 10, 1)
    if changed_field == 'revoked_at':
        assert used_at is None


def test_only_matching_code_is_consumed(app, client, recovery):
    user_id, _, first_id = recovery
    with app.app_context():
        first = db.session.get(MFABackupCode, first_id)
        first.code_hash = SecurityService.hash_backup_code('OTHER123')
        second = MFABackupCode(member_id=user_id, code_hash=SecurityService.hash_backup_code(CODE))
        db.session.add(second)
        db.session.commit()
        second_id = second.id
    assert client.post('/auth/2fa/verify', data={'backup_code': CODE}).status_code == 302
    assert read_code(app, first_id)[1] is None
    assert read_code(app, second_id)[1] is not None
