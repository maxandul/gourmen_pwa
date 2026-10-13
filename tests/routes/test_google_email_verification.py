"""A-088: address-bound, replaceable Google verification links."""
import re
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from backend.extensions import db
from backend.models.member import Member
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.services.mail import MailService
from backend.services.drive_storage import DriveStorageService


@pytest.fixture
def google_case(app, client, monkeypatch):
    mail = Mock()
    invited = []
    app.config['GOOGLE_DRIVE_ID'] = 'synthetic-drive'
    monkeypatch.setattr(MailService, 'send_async', mail)
    monkeypatch.setattr(DriveStorageService, 'apply_membership',
                        lambda drive_id, email, action: invited.append((uid, email))
                        if action == 'invite' else None)
    with app.app_context():
        member = Member(password_changed_at=datetime(2026, 1, 1),
                        vorname='Google', nachname='Test', email='account@example.com',
                        passwort_hash='unused')
        db.session.add(member)
        db.session.commit()
        uid = member.id
    with client.session_transaction() as state:
        state['_user_id'] = str(uid)
        state['_fresh'] = True
    return uid, mail, invited


def issue(client, mail, address='first@example.com'):
    assert client.post('/member/google-email/save', data={'google_email': address}).status_code == 302
    return re.search(r'/member/google-email/verify/([^\s]+)', mail.call_args.kwargs['text']).group(1)


def assert_unverified(app, uid, invited):
    with app.app_context():
        assert not db.session.get(Member, uid).google_email_verified
    assert invited == []


@pytest.mark.parametrize('change', ['address', 'resend', 'roundtrip', 'out_of_band'])
def test_old_link_cannot_verify(app, client, google_case, change):
    uid, mail, invited = google_case
    old = issue(client, mail)
    if change == 'resend':
        client.post('/member/google-email/resend')
    elif change == 'out_of_band':
        with app.app_context():
            db.session.get(Member, uid).google_email = 'second@example.com'
            db.session.commit()
    else:
        issue(client, mail, 'second@example.com')
        if change == 'roundtrip':
            issue(client, mail)
    assert client.get('/member/google-email/verify/' + old).status_code == 302
    assert_unverified(app, uid, invited)


def test_current_link_is_single_use(app, client, google_case):
    uid, mail, invited = google_case
    issue(client, mail)
    token = issue(client, mail, 'second@example.com')
    for _ in range(2):
        assert client.get('/member/google-email/verify/' + token).status_code == 302
    with app.app_context():
        assert db.session.get(Member, uid).google_email_verified
    assert invited == [(uid, 'second@example.com')]


@pytest.mark.parametrize('invalid', ['expired', 'inactive', 'purpose', 'used', 'tampered', 'legacy'])
def test_invalid_link_has_no_effect(app, client, google_case, invalid):
    uid, mail, invited = google_case
    token = issue(client, mail)
    with app.app_context():
        row = AuthToken.query.one()
        if invalid == 'expired':
            row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        elif invalid == 'inactive':
            db.session.get(Member, uid).is_active = False
        elif invalid == 'purpose':
            row.purpose = AuthTokenPurpose.PASSWORD_RESET
        elif invalid == 'used':
            row.used_at = datetime.utcnow()
        elif invalid == 'legacy':
            import hashlib
            row.token_hash = hashlib.sha256(token.encode()).hexdigest()
        else:
            token += 'tampered'
        db.session.commit()
    client.get('/member/google-email/verify/' + token)
    assert_unverified(app, uid, invited)


def test_resend_only_latest_link_works(app, client, google_case):
    uid, mail, invited = google_case
    issue(client, mail)
    client.post('/member/google-email/resend')
    token = re.search(r'/member/google-email/verify/([^\s]+)', mail.call_args.kwargs['text']).group(1)
    client.get('/member/google-email/verify/' + token)
    assert invited == [(uid, 'first@example.com')]


def test_csrf_blocks_save_and_resend(app, client, google_case):
    uid, mail, invited = google_case
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post('/member/google-email/save', data={'google_email': 'first@example.com'}).status_code == 400
    assert client.post('/member/google-email/resend').status_code == 400
    mail.assert_not_called()
    assert_unverified(app, uid, invited)


def test_stale_invite_is_cancelled_after_intervening_change(app, client, google_case, monkeypatch):
    from backend.services.security import SecurityService
    from backend.models.audit_event import AuditAction
    uid, mail, invited = google_case
    token = issue(client, mail)
    def change_after_verification(action, *args, **kwargs):
        if action == AuditAction.GOOGLE_EMAIL_VERIFIED:
            row = db.session.get(Member, uid)
            row.google_email = 'second@example.com'
            row.google_email_verified = False
            db.session.commit()
    monkeypatch.setattr(SecurityService, 'log_audit_event', change_after_verification)
    client.get('/member/google-email/verify/' + token)
    assert invited == []
    with app.app_context():
        assert not db.session.get(Member, uid).google_email_verified


def test_mail_uses_issued_snapshot_after_intervening_change(app, client, google_case, monkeypatch):
    import backend.routes.member as routes
    uid, mail, invited = google_case
    render = routes.render_template
    def change_before_mail(template, **context):
        if template == 'emails/google_email_verify.html':
            row = db.session.get(Member, uid)
            row.google_email = 'second@example.com'
            db.session.commit()
        return render(template, **context)
    monkeypatch.setattr(routes, 'render_template', change_before_mail)
    token = issue(client, mail)
    assert mail.call_args.kwargs['to'] == 'first@example.com'
    client.get('/member/google-email/verify/' + token)
    assert_unverified(app, uid, invited)


def test_replacement_preserves_other_token_purposes(app, client, google_case):
    uid, mail, invited = google_case
    with app.app_context():
        from backend.routes.auth import _issue_auth_token
        _issue_auth_token(uid, AuthTokenPurpose.PASSWORD_RESET, timedelta(days=1), None)
        db.session.commit()
    issue(client, mail)
    issue(client, mail, 'second@example.com')
    with app.app_context():
        assert AuthToken.query.filter_by(purpose=AuthTokenPurpose.PASSWORD_RESET).one().used_at is None


def test_issue_commit_failure_keeps_old_address_and_link(app, client, google_case, monkeypatch):
    from backend.services.google_email_verification import GoogleEmailVerificationService
    uid, mail, invited = google_case
    token = issue(client, mail)
    with app.app_context():
        with monkeypatch.context() as patch:
            patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic failure')))
            with pytest.raises(RuntimeError):
                GoogleEmailVerificationService.issue(uid, email='second@example.com')
        db.session.rollback()
        assert db.session.get(Member, uid).google_email == 'first@example.com'
    client.get('/member/google-email/verify/' + token)
    assert invited == [(uid, 'first@example.com')]


def test_feature_disabled_verifies_without_invite(app, client, google_case):
    uid, mail, invited = google_case
    app.config['DRIVE_FEATURE_ENABLED'] = False
    token = issue(client, mail)
    client.get('/member/google-email/verify/' + token)
    with app.app_context():
        assert db.session.get(Member, uid).google_email_verified
    assert invited == []
