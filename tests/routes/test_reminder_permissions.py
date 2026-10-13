"""A-043: both RSVP reminder entry points enforce the same sender permission."""

from datetime import datetime
from unittest.mock import Mock

from tests.conftest import auth_id
import pytest

from backend.extensions import db
from backend.models.event import Event, EventAudience, EventType
from backend.models.member import Member, Role, Funktion


@pytest.fixture
def reminder_case(app, client, monkeypatch):
    from backend.services.push_notifications import PushNotificationService

    send = Mock(return_value={'success': True, 'sent_count': 1, 'message': 'Synthetic success'})
    monkeypatch.setattr(PushNotificationService, 'send_participation_reminder_to_members', send)

    def prepare(actor_kind, audience, entry):
        with app.app_context():
            organizer = Member(password_changed_at=datetime(2026, 1, 1),
                               vorname='Test', nachname='Organizer', email='organizer@example.test',
                               passwort_hash='unused')
            actor = Member(password_changed_at=datetime(2026, 1, 1),
                           vorname='Test', nachname='Actor', email='actor@example.test',
                           passwort_hash='unused', role=Role.ADMIN if actor_kind == 'admin' else Role.MEMBER,
                           vorstandsmitglied=actor_kind == 'board')
            if actor_kind == 'treasurer':
                actor.funktion = Funktion.SCHATZMEISTER
            db.session.add_all([organizer, actor])
            db.session.flush()
            event = Event(organisator_id=organizer.id, datum=datetime(2027, 1, 15, 18),
                          event_typ=EventType.MONATSESSEN, season=2027, published=True,
                          restaurant='Synthetic', audience=audience)
            db.session.add(event)
            db.session.commit()
            event_id = event.id
            actor_id = organizer.id if actor_kind == 'organizer' else actor.id
        if actor_kind != 'anonymous':
            with client.session_transaction() as session:
                session['_user_id'] = auth_id(client, actor_id)
                session['_fresh'] = True
        path = (f'/events/{event_id}/send_rsvp_reminder' if entry == 'legacy'
                else f'/events/api/events/{event_id}/send-reminders')
        return path, event_id, send

    return prepare


@pytest.mark.parametrize('entry', ['legacy', 'api'])
@pytest.mark.parametrize('audience', [EventAudience.ALL, EventAudience.BOARD])
@pytest.mark.parametrize('actor_kind', ['anonymous', 'member', 'board', 'treasurer', 'organizer', 'admin'])
def test_sender_permissions(client, reminder_case, entry, audience, actor_kind):
    path, event_id, send = reminder_case(actor_kind, audience, entry)
    response = client.post(path)
    if actor_kind in ('organizer', 'admin'):
        assert response.status_code == (302 if entry == 'legacy' else 200)
        send.assert_called_once_with(event_id)
    else:
        send.assert_not_called()
        if actor_kind == 'anonymous':
            assert response.status_code == 302
            assert '/auth/login' in response.location
        elif audience == EventAudience.BOARD and actor_kind != 'board':
            assert response.status_code == 403
        elif entry == 'api':
            assert response.status_code == 403
            assert response.json['error'] == 'Keine Berechtigung'
        else:
            assert response.status_code == 302
            with client.session_transaction() as session:
                assert any(category == 'error' for category, _ in session.get('_flashes', []))


@pytest.mark.parametrize('entry', ['legacy', 'api'])
def test_missing_event_never_dispatches(client, reminder_case, entry):
    path, event_id, send = reminder_case('admin', EventAudience.ALL, entry)
    assert client.post(path.replace(str(event_id), '99999')).status_code == 404
    send.assert_not_called()


@pytest.mark.parametrize('entry', ['legacy', 'api'])
def test_get_never_dispatches(client, reminder_case, entry):
    path, _, send = reminder_case('organizer', EventAudience.ALL, entry)
    assert client.get(path).status_code == 405
    send.assert_not_called()


@pytest.mark.parametrize('entry', ['legacy', 'api'])
def test_csrf_still_required(app, client, reminder_case, entry):
    path, _, send = reminder_case('admin', EventAudience.ALL, entry)
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(path).status_code == 400
    send.assert_not_called()
