"""U1y: durable tokens, honest delivery status and explicit replacement."""
import hashlib
import re
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.audit_event import AuditEvent
from backend.models.member import Member, Role
from backend.services.onboarding import OnboardingService
from backend.services.security import SecurityService
from tests.conftest import auth_id
from tests.routes.test_member_creation_confirmation import creation, intent, post, PASSWORD


def invited(app, client, creation):
    assert post(client, intent(client)).status_code == 302
    with app.app_context():
        return Member.query.filter_by(email='new@example.com').one().id


def path(uid):
    return f'/admin/members/{uid}/onboarding'


def token(client, uid):
    response = client.get(path(uid))
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    return re.search(r'name="action_token" value="([^"]+)"', response.text).group(1)


def resend(client, uid, proof, password=PASSWORD):
    return client.post(path(uid), data={'action_token': proof, 'action_password': password})


def state(app, uid):
    with app.app_context():
        row = OnboardingService.latest(uid)
        return row.id, row.delivery_status, row.used_at


def raw_from_mail(mail):
    return re.search(r'/auth/activate/([\w-]+)', mail.call_args.kwargs['text']).group(1)


@pytest.mark.parametrize('result', ['accepted', 'unconfirmed', 'exception', 'audit_failure'])
def test_token_durable_before_send_and_after_failure(app, client, creation, monkeypatch, result, caplog):
    observed = []
    def send(**kwargs):
        raw = re.search(r'/auth/activate/([\w-]+)', kwargs['text']).group(1)
        # A rollback here removes any merely flushed writes: token must survive.
        db.session.rollback()
        row = AuthToken.query.filter_by(token_hash=hashlib.sha256(raw.encode()).hexdigest()).one()
        assert row.delivery_status == 'pending'
        assert db.session.get(Member, row.member_id).email == kwargs['to'] == row.recipient_email
        observed.append(raw)
        if result == 'exception':
            raise RuntimeError('Synthetic-private-token ' + raw)
        return {'success': result != 'unconfirmed', 'error': 'Synthetic-private-provider'}
    creation[1].side_effect = send
    if result == 'audit_failure':
        monkeypatch.setattr('backend.services.onboarding.AuditEvent', Mock(side_effect=RuntimeError('synthetic')))
    uid = invited(app, client, creation)
    expected = 'pending' if result == 'audit_failure' else 'accepted' if result == 'accepted' else 'unconfirmed'
    assert state(app, uid)[1:] == (expected, None)
    assert len(observed) == 1
    assert observed[0] not in caplog.text
    assert 'Synthetic-private' not in caplog.text
    with app.app_context():
        assert AuthToken.query.count() == 1
        if result != 'audit_failure':
            assert AuditEvent.query.count() == 2
            assert observed[0] not in str([row.extra_json for row in AuditEvent.query.all()])


def test_initial_commit_failure_never_sends_or_saves_partial_member(app, client, creation, monkeypatch):
    proof = intent(client)
    def fail():
        raise IntegrityError('synthetic', {}, Exception('synthetic'))
    monkeypatch.setattr(db.session, 'commit', fail)
    assert post(client, proof).status_code == 200
    with app.app_context():
        assert Member.query.count() == 1
        assert AuthToken.query.count() == 0
    creation[1].assert_not_called()


def test_resend_replaces_only_onboarding_and_receipt_blocks_cookie_replay(app, client, creation):
    uid = invited(app, client, creation)
    raw = raw_from_mail(creation[1])
    before = auth_id(client, uid)
    proof = token(client, uid)
    cookie = client.get_cookie('session').value
    first_id = state(app, uid)[0]
    assert client.head(path(uid)).status_code == 200
    assert creation[1].call_count == 1
    assert resend(client, uid, proof).status_code == 302
    with app.app_context():
        assert db.session.get(AuthToken, first_id).used_at is not None
        assert AuthToken.query.count() == 2
    assert auth_id(client, uid) == before
    client.set_cookie('session', cookie)
    assert resend(client, uid, proof).status_code == 200
    assert creation[1].call_count == 2
    anonymous = app.test_client()
    assert anonymous.get('/auth/activate/' + raw).status_code == 302
    assert anonymous.get('/auth/activate/' + raw_from_mail(creation[1])).status_code == 200


@pytest.mark.parametrize('fault', ['password', 'missing', 'csrf', 'nonadmin', 'generation', 'email'])
def test_resend_rejects_without_send(app, client, creation, fault):
    uid = invited(app, client, creation)
    proof = token(client, uid)
    if fault == 'csrf':
        app.config['WTF_CSRF_ENABLED'] = True
    elif fault == 'nonadmin':
        with client.session_transaction() as session:
            session['_user_id'] = auth_id(client, uid)
    elif fault in {'generation', 'email'}:
        with app.app_context():
            member = db.session.get(Member, uid)
            if fault == 'generation':
                member.rotate_auth_generation()
            else:
                member.email = 'changed@example.com'
            db.session.commit()
    response = resend(client, uid, '' if fault == 'missing' else proof,
                      'wrong' if fault == 'password' else PASSWORD)
    assert response.status_code == {'csrf': 400, 'nonadmin': 403}.get(fault, 200)
    assert creation[1].call_count == 1
    with app.app_context():
        assert AuthToken.query.count() == 1


def test_address_correction_invalidates_old_link_and_new_invite_uses_new_address(app, client, creation):
    uid = invited(app, client, creation)
    raw = raw_from_mail(creation[1])
    with app.app_context():
        db.session.get(Member, uid).email = 'corrected@example.com'
        db.session.commit()
    anonymous = app.test_client()
    assert anonymous.get('/auth/activate/' + raw).status_code == 302
    assert resend(client, uid, token(client, uid)).status_code == 302
    assert creation[1].call_args.kwargs['to'] == 'corrected@example.com'


def test_activation_stops_resend(app, client, creation):
    uid = invited(app, client, creation)
    raw = raw_from_mail(creation[1])
    anonymous = app.test_client()
    response = anonymous.post('/auth/activate/' + raw, data={
        'new_password': 'Synthetic-New-password-234!', 'confirm_password': 'Synthetic-New-password-234!'})
    assert response.status_code == 302
    page = client.get(path(uid))
    assert 'name="action_token"' not in page.text
    assert 'nicht verfügbar' in page.text
    assert creation[1].call_count == 1


def test_replacement_commit_failure_keeps_old_link_and_allows_retry(app, client, creation, monkeypatch):
    uid = invited(app, client, creation)
    proof = token(client, uid)
    original = state(app, uid)
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
        assert resend(client, uid, proof).status_code == 200
    assert state(app, uid) == original
    assert creation[1].call_count == 1
    assert resend(client, uid, proof).status_code == 302


def test_inactive_initial_account_not_sent(app, client, creation):
    assert post(client, intent(client), is_active='').status_code == 302
    with app.app_context():
        row = AuthToken.query.one()
        assert row.delivery_status == 'obsolete'
    creation[1].assert_not_called()


def test_late_result_updates_only_its_attempt(app, client, creation):
    uid = invited(app, client, creation)
    def send(**kwargs):
        member = SecurityService.lock_credential_member(uid)
        OnboardingService.prepare(member, replace=True)
        db.session.commit()
        return {'success': True}
    creation[1].side_effect = send
    assert resend(client, uid, token(client, uid)).status_code == 302
    with app.app_context():
        rows = AuthToken.query.filter_by(member_id=uid).order_by(AuthToken.id).all()
        assert len(rows) == 3
        assert rows[1].delivery_status == 'accepted' and rows[1].used_at is not None
        assert rows[2].delivery_status == 'pending' and rows[2].used_at is None


def test_activation_rechecks_address_under_lock(app, client, creation, monkeypatch):
    uid = invited(app, client, creation)
    raw = raw_from_mail(creation[1])
    lock = SecurityService.lock_credential_member
    def changed(member_id):
        db.session.execute(Member.__table__.update().where(Member.id == uid)
                           .values(email='changed@example.com'))
        db.session.commit()
        return lock(member_id)
    monkeypatch.setattr(SecurityService, 'lock_credential_member', changed)
    anonymous = app.test_client()
    assert anonymous.post('/auth/activate/' + raw, data={
        'new_password': 'Synthetic-New-password-234!', 'confirm_password': 'Synthetic-New-password-234!'}).status_code == 302
    with app.app_context():
        assert not db.session.get(Member, uid).check_password('Synthetic-New-password-234!')
        assert OnboardingService.latest(uid).used_at is None


def test_legacy_account_has_no_resend_and_does_not_change_tokens(app, client, creation):
    page = client.get(path(creation[0]))
    assert page.status_code == 200
    assert 'name="action_token"' not in page.text
    assert 'kein nachverfolgbarer' in page.text
    creation[1].assert_not_called()


def test_sensitive_failure_rolls_back_and_still_sends_durable_link(app, client, creation, monkeypatch, caplog):
    monkeypatch.setattr(SecurityService, 'encrypt_json', Mock(side_effect=RuntimeError('Synthetic-private-passport')))
    assert post(client, intent(client), pass_nummer='Synthetic-private-passport').status_code == 302
    assert creation[1].call_count == 1
    assert 'Synthetic-private-passport' not in caplog.text
    with app.app_context():
        assert AuthToken.query.one().delivery_status == 'accepted'
