"""A-080: fresh backup codes belong to the confirmed enrollment transaction."""
import base64
import logging
from datetime import datetime
from unittest.mock import Mock

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService

PASSWORD = 'Synthetic-enrollment-password1!'
SECRET = 'JBSWY3DPEHPK3PXP'
OLD = 'AB12CD34'


@pytest.fixture
def case(app, client, monkeypatch):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        member = Member(vorname='Backup', nachname='Test', email='backup@example.com')
        member.set_password(PASSWORD)
        db.session.add(member)
        db.session.commit()
        uid = member.id
    with client.session_transaction() as state:
        state['_user_id'] = str(uid)
        state['_fresh'] = True
        state['2fa_secret'] = SECRET
    from backend.routes import auth
    render = auth.render_template
    shown = []

    def capture(template, **context):
        if template == 'auth/backup_codes.html':
            shown.append(context['backup_codes'])
        return render(template, **context)

    monkeypatch.setattr(auth, 'render_template', capture)
    return uid, shown


def enroll(client):
    return client.post('/auth/2fa/enroll', data={'token': pyotp.TOTP(SECRET).now()})


@pytest.mark.parametrize('old_state', [None, 'active', 'used', 'revoked'])
def test_enrollment_replaces_old_codes_and_displays_only_once(app, client, case, caplog, old_state):
    uid, shown = case
    with app.app_context():
        if old_state:
            db.session.add(MFABackupCode(member_id=uid, code_hash=SecurityService.hash_backup_code(OLD),
                                        used_at=datetime.utcnow() if old_state == 'used' else None,
                                        revoked_at=datetime.utcnow() if old_state == 'revoked' else None))
            db.session.commit()
    with caplog.at_level(logging.INFO):
        response = enroll(client)
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    codes = shown[0]
    assert len(codes) == len(set(codes)) == 10
    for code in codes:
        assert code in response.text
        assert code not in caplog.text
        assert code not in str(response.headers)
    with client.session_transaction() as state:
        assert '2fa_secret' not in state
        assert not any(code in str(dict(state)) for code in codes)
    with app.app_context():
        assert MemberMFA.query.one().is_totp_enabled
        rows = MFABackupCode.query.filter_by(revoked_at=None, used_at=None).all()
        assert len(rows) == 10
        assert all(any(SecurityService.check_backup_code(row.code_hash, code) for row in rows) for code in codes)
        assert SecurityService.consume_backup_code(uid, OLD) is None
        assert SecurityService.consume_backup_code(uid, codes[0]) is not None
        assert SecurityService.consume_backup_code(uid, codes[0]) is None
    assert enroll(client).status_code == 302
    assert client.get('/auth/2fa/backup-codes').status_code == 302
    assert len(shown) == 1
    with app.app_context():
        assert MFABackupCode.query.count() == 10 + bool(old_state)


def test_disable_and_reenroll_provides_new_usable_codes(app, client, case):
    uid, shown = case
    enroll(client)
    old_codes = shown[0]
    assert client.post('/auth/2fa/disable', data={'password': PASSWORD}).status_code == 302
    with client.session_transaction() as state:
        state['2fa_secret'] = SECRET
    assert enroll(client).status_code == 200
    with app.app_context():
        assert MFABackupCode.query.count() == 20
        assert MFABackupCode.query.filter_by(revoked_at=None, used_at=None).count() == 10
    client.get('/auth/logout')
    assert client.post('/auth/login', data={'email': 'backup@example.com', 'password': PASSWORD}).location.endswith('/auth/2fa/verify')
    assert client.post('/auth/2fa/verify', data={'backup_code': old_codes[0]}).status_code == 200
    assert client.post('/auth/2fa/verify', data={'backup_code': shown[1][0]}).status_code == 302
    with client.session_transaction() as state:
        assert state['_user_id'] == str(uid)


@pytest.mark.parametrize('method', ['get', 'head'])
@pytest.mark.parametrize('path', ['/auth/2fa/enroll', '/auth/2fa/backup-codes'])
def test_read_requests_do_not_create_mfa_or_codes(app, client, case, method, path):
    getattr(client, method)(path)
    with app.app_context():
        assert MemberMFA.query.count() == 0
        assert MFABackupCode.query.count() == 0


@pytest.mark.parametrize('failure', ['invalid', 'csrf', 'commit', 'render'])
def test_failure_does_not_activate_or_replace_codes(app, client, case, monkeypatch, failure):
    uid, shown = case
    with app.app_context():
        db.session.add(MFABackupCode(member_id=uid, code_hash=SecurityService.hash_backup_code(OLD)))
        db.session.commit()
    if failure == 'csrf':
        app.config['WTF_CSRF_ENABLED'] = True
        assert enroll(client).status_code == 400
    elif failure == 'invalid':
        assert client.post('/auth/2fa/enroll', data={'token': 'wrong'}).status_code == 200
    else:
        with monkeypatch.context() as patch:
            if failure == 'commit':
                patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
            else:
                patch.setattr('backend.routes.auth.render_template', Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(RuntimeError):
                enroll(client)
    with app.app_context():
        assert MemberMFA.query.count() == 0
        assert MFABackupCode.query.count() == 1
        assert MFABackupCode.query.one().revoked_at is None
    with client.session_transaction() as state:
        assert state['2fa_secret'] == SECRET
    app.config['WTF_CSRF_ENABLED'] = False
    assert enroll(client).status_code == 200


def test_other_members_codes_untouched(app, client, case):
    with app.app_context():
        other = Member(vorname='Other', nachname='Member', email='other@example.com', passwort_hash='unused')
        db.session.add(other)
        db.session.flush()
        row = MFABackupCode(member_id=other.id, code_hash='synthetic-other-hash')
        db.session.add(row)
        db.session.commit()
        row_id = row.id
    enroll(client)
    with app.app_context():
        assert db.session.get(MFABackupCode, row_id).revoked_at is None


def test_anonymous_cannot_generate_codes(app, client):
    assert client.post('/auth/2fa/enroll', data={'token': '123456'}).status_code == 302
    assert client.get('/auth/2fa/backup-codes').status_code == 302
    with app.app_context():
        assert MFABackupCode.query.count() == 0
