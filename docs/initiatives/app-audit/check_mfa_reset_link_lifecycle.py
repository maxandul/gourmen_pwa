"""Old MFA recovery links across real enrollment/reset/enrollment sequences."""
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from datetime import datetime, timezone
import json
import logging
import re
import runpy

OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT / 'check_onboarding_failures.py'), run_name='audit_helper')
app, db, Member, Role = (ns[key] for key in ('app', 'db', 'Member', 'Role'))
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.auth_token import AuthToken
from backend.routes.auth import MailService
from cryptography.fernet import Fernet
import pyotp

logging.disable(logging.CRITICAL)
app.config['CRYPTO_KEY'] = Fernet.generate_key().decode()
PASSWORD = 'Synthetic-MFA-Lifecycle-471!'


def login(uid):
    client = app.test_client()
    response = client.post('/auth/login', data={'email':f'mfa-lifecycle-{uid}@example.com','password':PASSWORD})
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session.get('_user_id') == str(uid)
    return client


def enroll(client):
    assert client.get('/auth/2fa/enroll').status_code == 200
    with client.session_transaction() as session:
        secret = session['2fa_secret']
    response = client.post('/auth/2fa/enroll', data={'token':pyotp.TOTP(secret).now()})
    assert response.status_code == 302
    assert client.get('/auth/2fa/backup-codes').status_code == 200
    with app.app_context():
        assert MemberMFA.query.filter_by(member_id=2).one().is_totp_enabled
        assert MFABackupCode.query.filter_by(member_id=2).count() > 0
    return secret


def probe(mode):
    with app.app_context():
        db.create_all()
        for uid, role in ((1, Role.ADMIN),(2, Role.MEMBER)):
            member = Member(id=uid, vorname='Audit', nachname='MFA-Folge',
                            email=f'mfa-lifecycle-{uid}@example.com', role=role,is_active=True)
            member.set_password(PASSWORD)
            db.session.add(member)
        db.session.commit()
    first_secret = enroll(login(2))
    paths = []
    def capture(**kwargs):
        paths.append(urlsplit(re.search(r'https?://\S+', kwargs['text']).group(0)).path)
    with patch.object(MailService, 'send_async', side_effect=capture):
        for _ in range(2 if mode == 'mail_reset' else 1):
            response = app.test_client().post('/auth/2fa/reset-request', data={'email':'mfa-lifecycle-2@example.com'})
            assert response.status_code == 302
    assert len(paths) == (2 if mode == 'mail_reset' else 1)
    if mode == 'mail_reset':
        assert paths[0] != paths[1]
        reset = app.test_client().post(paths[1])
    else:
        admin = login(1)
        assert admin.post('/auth/step-up', data={'password':PASSWORD,'next':'/admin/members/2/reset-2fa'}).status_code == 302
        reset = admin.post('/admin/members/2/reset-2fa', data={'confirm':'RESET'})
    assert reset.status_code == 302
    with app.app_context():
        assert not MemberMFA.query.filter_by(member_id=2).one().is_totp_enabled
    second_secret = enroll(login(2))
    assert second_secret != first_secret
    control = app.test_client()
    assert control.post('/auth/login', data={'email':'mfa-lifecycle-2@example.com','password':PASSWORD}).status_code == 302
    with control.session_transaction() as session:
        assert session.get('pending_2fa_user_id') == 2 and '_user_id' not in session
    with app.app_context():
        assert AuthToken.query.filter_by(used_at=None).count() == 1
    old = app.test_client().post(paths[0])
    assert old.status_code == 302
    with app.app_context():
        disabled = not MemberMFA.query.filter_by(member_id=2).one().is_totp_enabled
        backups_deleted = MFABackupCode.query.filter_by(member_id=2).count() == 0
        assert disabled and backups_deleted
    login(2)  # Full session with password alone after the old link was used.
    enroll(login(2))
    replay = app.test_client().post(paths[0])
    assert replay.status_code == 302
    with app.app_context():
        replay_blocked = MemberMFA.query.filter_by(member_id=2).one().is_totp_enabled
        assert replay_blocked
        db.session.remove()
        db.drop_all()
    return dict(case=mode, intercepted_mail_requests=len(paths), distinct_reenrollment_secret=True,
                normal_login_required_mfa_before_old_link=True, old_link_disabled_new_mfa=disabled,
                new_backup_codes_deleted=backups_deleted, password_only_login_after_old_link=True,
                replay_after_third_enrollment_blocked=replay_blocked)


results = [probe(mode) for mode in ('mail_reset','admin_reset')]
output = dict(date=datetime.now(timezone.utc).date().isoformat(),groups=len(results),results=results,
              limits='Original login/enrollment/TOTP, request/reset and admin step-up/reset routes. Mail send_async intercepted; SQLite memory, synthetic accounts and process-only encryption key. No actual mail, production or secrets printed. Logging suppressed. Testing CSRF/rate limits disabled; no browser/concurrency/Postgres coverage. Valid unused old link required.')
(OUT / 'MFA_RESET_LINK_LIFECYCLE_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
