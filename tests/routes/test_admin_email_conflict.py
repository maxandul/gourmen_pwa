"""A-084: admin member conflicts must not partially save or send onboarding."""

from datetime import datetime
from unittest.mock import Mock

from tests.conftest import auth_id
import pytest
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.auth_token import AuthToken
from backend.models.member_sensitive import MemberSensitive
from backend.routes.admin import MemberForm
from backend.services.mail import MailService
from backend.services.security import SecurityService


@pytest.fixture
def admin_case(app, client, monkeypatch):
    mail = Mock(return_value={'success': True})
    audit = Mock()
    monkeypatch.setattr(MailService, 'send', mail)
    monkeypatch.setattr(SecurityService, 'log_audit_event', audit)
    with app.app_context():
        users = [Member(password_changed_at=datetime(2026, 1, 1), vorname='Original', nachname=str(i), email=email,
                        passwort_hash='unused', role=Role.ADMIN if i == 0 else Role.MEMBER)
                 for i, email in enumerate(['admin@example.com', 'edit@example.com', 'taken@example.com'])]
        db.session.add_all(users)
        db.session.commit()
        ids = [user.id for user in users]
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, ids[0])
        state['_fresh'] = True
    return ids, mail, audit


def data(email):
    return {'vorname': 'Edited', 'nachname': 'Test', 'email': email,
            'geburtsdatum': '1990-01-01', 'beitritt': '2020-01-01',
            'funktion': 'MEMBER', 'role': 'MEMBER', 'is_active': 'y',
            'password': 'Synthetic-password-123'}


@pytest.mark.parametrize('entry', ['create', 'edit'])
@pytest.mark.parametrize('active', [True, False])
@pytest.mark.parametrize('skip_precheck', [False, True])
def test_duplicate_keeps_state_and_stops_followups(app, client, admin_case, monkeypatch,
                                                  entry, active, skip_precheck):
    ids, mail, audit = admin_case
    if skip_precheck:
        monkeypatch.setattr(MemberForm, 'validate_email', lambda self, field: None, raising=False)
    with app.app_context():
        db.session.get(Member, ids[2]).is_active = active
        db.session.commit()
    path = '/admin/members/new' if entry == 'create' else f'/admin/members/{ids[1]}/edit'
    response = client.post(path, data=data('taken@example.com'))
    assert response.status_code == 200
    assert 'Diese E-Mail-Adresse wird bereits verwendet.' in response.get_data(as_text=True)
    assert b'value="Edited"' in response.data
    assert b'value="taken@example.com"' in response.data
    with app.app_context():
        assert Member.query.count() == 3
        original = db.session.get(Member, ids[1])
        assert (original.email, original.vorname) == ('edit@example.com', 'Original')
        assert AuthToken.query.count() == 0
        assert MemberSensitive.query.count() == 0
    mail.assert_not_called()
    audit.assert_not_called()


@pytest.mark.parametrize('email', ['edit@example.com', 'FreeMixed@example.com'])
def test_edit_own_or_free_address(app, client, admin_case, email):
    ids, mail, audit = admin_case
    response = client.post(f'/admin/members/{ids[1]}/edit', data=data(email))
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Member, ids[1]).email == email
    mail.assert_not_called()
    audit.assert_called_once()


@pytest.mark.parametrize('first_result', ['success', 'mail_failure', 'audit_failure'])
def test_create_retry_does_not_send_again(app, client, admin_case, first_result):
    _, mail, audit = admin_case
    if first_result == 'mail_failure':
        mail.return_value = {'success': False, 'error': 'Synthetic mail failure'}
    elif first_result == 'audit_failure':
        audit.side_effect = RuntimeError('Synthetic audit failure')
    if first_result == 'audit_failure':
        with pytest.raises(RuntimeError):
            client.post('/admin/members/new', data=data('new@example.com'))
    else:
        assert client.post('/admin/members/new', data=data('new@example.com')).status_code == 302
    assert mail.call_count == 1
    audit_count = audit.call_count
    response = client.post('/admin/members/new', data=data('new@example.com'))
    assert response.status_code == 200
    assert mail.call_count == 1
    assert audit.call_count == audit_count
    with app.app_context():
        assert Member.query.filter_by(email='new@example.com').count() == 1


@pytest.mark.parametrize('entry', ['create', 'edit'])
def test_nonadmin_cannot_write(app, client, admin_case, entry):
    ids, mail, audit = admin_case
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, ids[1])
    path = '/admin/members/new' if entry == 'create' else f'/admin/members/{ids[2]}/edit'
    assert client.post(path, data=data('free@example.com')).status_code == 403
    mail.assert_not_called()
    audit.assert_not_called()


@pytest.mark.parametrize('entry', ['create', 'edit'])
def test_other_integrity_failure_rolls_back_without_followups(app, client, admin_case, monkeypatch, entry):
    ids, mail, audit = admin_case
    path = '/admin/members/new' if entry == 'create' else f'/admin/members/{ids[1]}/edit'
    def fail():
        raise IntegrityError('synthetic-private-sql', {}, Exception('synthetic-private-error'))
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', fail)
        response = client.post(path, data=data('free@example.com'))
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Mitglied konnte nicht gespeichert werden.' in text
    assert 'synthetic-private' not in text
    assert 'Diese E-Mail-Adresse wird bereits verwendet.' not in text
    with app.app_context():
        assert Member.query.count() == 3
        assert db.session.get(Member, ids[1]).vorname == 'Original'
    mail.assert_not_called()
    audit.assert_not_called()


@pytest.mark.parametrize('entry', ['create', 'edit'])
def test_admin_forms_require_csrf(app, client, admin_case, entry):
    ids, mail, audit = admin_case
    app.config['WTF_CSRF_ENABLED'] = True
    path = '/admin/members/new' if entry == 'create' else f'/admin/members/{ids[1]}/edit'
    assert client.post(path, data=data('free@example.com')).status_code == 400
    mail.assert_not_called()
    audit.assert_not_called()
