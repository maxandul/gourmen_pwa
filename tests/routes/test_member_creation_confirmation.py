"""U1x: one creation intent cannot grant initial rights twice."""
import re
from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.action_confirmation_use import ActionConfirmationUse
from backend.services.action_confirmation import ActionConfirmationService
from backend.services.mail import MailService
from backend.services.security import SecurityService
from tests.conftest import auth_id
from tests.routes.test_admin_email_conflict import data

PATH = '/admin/members/new'
PASSWORD = 'Synthetic-admin-password-123'


@pytest.fixture
def creation(app, client, monkeypatch):
    mail = Mock(return_value={'success': True})
    monkeypatch.setattr(MailService, 'send', mail)
    with app.app_context():
        member = Member(vorname='Admin', nachname='Synthetic', email='admin@example.com',
                        role=Role.ADMIN, password_changed_at=datetime(2026, 1, 1))
        member.set_password(PASSWORD)
        db.session.add(member)
        db.session.commit()
        uid = member.id
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True
    return uid, mail


def intent(client):
    response = client.get(PATH)
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    return re.search(r'name="action_token" value="([^"]+)"', response.text).group(1)


def post(client, token, email='new@example.com', **changes):
    payload = dict(data(email), action_token=token, action_password=PASSWORD)
    payload.update(changes)
    return client.post(PATH, data=payload)


def counts(app):
    with app.app_context():
        return Member.query.count(), ActionConfirmationUse.query.count()


def test_read_cancel_and_two_tabs(app, client, creation):
    first, second = intent(client), intent(client)
    assert first != second
    assert client.head(PATH).headers['Cache-Control'] == 'no-store'
    assert counts(app) == (1, 0)
    identity = auth_id(client, creation[0])
    assert post(client, first, role='ADMIN', funktion='SCHATZMEISTER', vorstandsmitglied='y').status_code == 302
    assert post(client, second, email='second@example.com').status_code == 302
    assert counts(app) == (3, 2)
    assert auth_id(client, creation[0]) == identity
    with app.app_context():
        row = Member.query.filter_by(email='new@example.com').one()
        assert row.role == Role.ADMIN and row.vorstandsmitglied
        assert row.funktion.value == 'SCHATZMEISTER'


@pytest.mark.parametrize('fault', ['missing', 'tampered', 'password', 'empty_password',
                                  'session', 'action', 'expired', 'nonce'])
def test_rejected_without_writes(app, client, creation, monkeypatch, fault, caplog):
    token = intent(client)
    changes = {}
    if fault == 'missing':
        token = ''
    elif fault == 'tampered':
        token += 'x'
    elif fault in {'password', 'empty_password'}:
        changes['action_password'] = 'Synthetic-wrong-private' if fault == 'password' else ''
    elif fault == 'session':
        with client.session_transaction() as state:
            state['action_session'] = 'different-login'
    elif fault == 'expired':
        monkeypatch.setattr(ActionConfirmationService, 'MAX_AGE', -1)
    else:
        with app.app_context():
            serializer = ActionConfirmationService.serializer()
            payload = serializer.loads(token)
            payload['action' if fault == 'action' else 'nonce'] = 'invalid'
            token = serializer.dumps(payload)
    response = post(client, token, **changes)
    assert response.status_code == 200
    assert counts(app) == (1, 0)
    creation[1].assert_not_called()
    assert 'Synthetic-wrong-private' not in response.text + caplog.text
    with client.session_transaction() as state:
        assert PASSWORD not in str(dict(state))


def test_consumption_survives_old_cookie_and_changed_target(app, client, creation):
    token = intent(client)
    cookie = client.get_cookie('session').value
    assert post(client, token).status_code == 302
    client.set_cookie('session', cookie)
    response = post(client, token, email='other@example.com', role='ADMIN')
    assert response.status_code == 200
    assert 'bereits verwendet' in response.text
    assert counts(app) == (2, 1)
    assert creation[1].call_count == 1


@pytest.mark.parametrize('fault', ['validation', 'password', 'commit'])
def test_failure_preserves_intent_for_fresh_password_retry(app, client, creation, monkeypatch, fault):
    token = intent(client)
    with monkeypatch.context() as patch:
        changes = {}
        if fault == 'validation':
            changes['vorname'] = ''
        elif fault == 'password':
            changes['action_password'] = 'wrong'
        else:
            def fail():
                raise IntegrityError('synthetic', {}, Exception('synthetic'))
            patch.setattr(db.session, 'commit', fail)
        assert post(client, token, **changes).status_code == 200
    assert counts(app) == (1, 0)
    assert post(client, token).status_code == 302
    assert counts(app) == (2, 1)


@pytest.mark.parametrize('fault', ['mail', 'audit'])
def test_followup_failure_cannot_reuse_intent(app, client, creation, monkeypatch, fault):
    token = intent(client)
    if fault == 'mail':
        creation[1].return_value = {'success': False}
        assert post(client, token).status_code == 302
    else:
        monkeypatch.setattr('backend.services.onboarding.AuditEvent', Mock(side_effect=RuntimeError('synthetic')))
        assert post(client, token).status_code == 302
    assert post(client, token, email='other@example.com').status_code == 200
    assert counts(app) == (2, 1)
    assert creation[1].call_count == 1


@pytest.mark.parametrize('change', ['generation', 'deactivate', 'demote'])
def test_actor_change_after_auth_before_lock(app, client, creation, monkeypatch, change):
    token = intent(client)
    lock = SecurityService.lock_credential_member
    def changed(uid):
        values = {'auth_generation': 'synthetic-revoked'}
        if change == 'deactivate':
            values = {'is_active': False}
        elif change == 'demote':
            values = {'role': Role.MEMBER}
        db.session.execute(Member.__table__.update().where(Member.id == uid).values(**values))
        db.session.commit()
        return lock(uid)
    monkeypatch.setattr(SecurityService, 'lock_credential_member', changed)
    assert post(client, token).status_code == 403
    assert counts(app) == (1, 0)
    creation[1].assert_not_called()


def test_other_admin_cannot_reuse_intent_even_with_same_session_nonce(app, client, creation):
    token = intent(client)
    with app.app_context():
        other = Member(vorname='Other', nachname='Admin', email='other-admin@example.com', role=Role.ADMIN)
        other.set_password(PASSWORD)
        db.session.add(other)
        db.session.commit()
        uid = other.id
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
    assert post(client, token).status_code == 200
    assert counts(app) == (2, 0)
    creation[1].assert_not_called()


def test_real_email_constraint_rolls_back_receipt(app, client, creation, monkeypatch):
    from backend.routes.admin import MemberForm
    token = intent(client)
    monkeypatch.setattr(MemberForm, 'validate_email', lambda self, field: None)
    response = post(client, token, email='admin@example.com')
    assert response.status_code == 200
    assert 'bereits verwendet' in response.text
    assert counts(app) == (1, 0)
    creation[1].assert_not_called()
    assert post(client, token).status_code == 302
    assert counts(app) == (2, 1)


def test_creation_rate_limit(monkeypatch):
    from backend.app import create_app
    from backend.config import TestingConfig
    monkeypatch.setattr(TestingConfig, 'RATELIMIT_ENABLED', True)
    monkeypatch.setattr(TestingConfig, 'REDIS_URL', None)
    app = create_app('testing')
    try:
        with app.app_context():
            db.create_all()
            actor = Member(vorname='Rate', nachname='Test', email='rate@example.com', role=Role.ADMIN)
            actor.set_password(PASSWORD)
            db.session.add(actor)
            db.session.commit()
            uid = actor.id
        client = app.test_client()
        with client.session_transaction() as state:
            state['_user_id'] = auth_id(client, uid)
            state['_fresh'] = True
        token = intent(client)
        for _ in range(5):
            assert post(client, token, action_password='wrong').status_code == 200
        assert post(client, token).status_code == 429
        assert counts(app) == (1, 0)
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
