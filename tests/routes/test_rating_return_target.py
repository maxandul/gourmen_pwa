"""A-035: rating success and error paths use only internal return targets."""
from datetime import datetime
from urllib.parse import urlencode

from tests.conftest import auth_id
import pytest

from backend.extensions import db
from backend.models.event import Event, EventType, EventAudience
from backend.models.member import Member
from backend.models.participation import Participation
from backend.models.rating import EventRating


@pytest.fixture
def rating_case(app, client):
    def prepare(case):
        with app.app_context():
            organizer = Member(password_changed_at=datetime(2026, 1, 1),
                               vorname='Organizer', nachname='Test', email='org@example.test',
                               passwort_hash='unused')
            member = Member(password_changed_at=datetime(2026, 1, 1),
                            vorname='Rating', nachname='Test', email='rating@example.test',
                            passwort_hash='unused')
            db.session.add_all([organizer, member])
            db.session.flush()
            event = Event(organisator_id=organizer.id, datum=datetime(2026, 1, 1),
                          event_typ=EventType.MONATSESSEN, season=2026,
                          restaurant='Synthetic', published=True, allow_ratings=case != 'disabled')
            db.session.add(event)
            db.session.flush()
            db.session.add(Participation(event_id=event.id, member_id=member.id,
                                         teilnahme=case != 'absent'))
            if case == 'existing':
                db.session.add(EventRating(event_id=event.id, participant_id=member.id,
                                           food_rating=2, drinks_rating=2, service_rating=2))
            db.session.commit()
            event_id, member_id = event.id, member.id
        with client.session_transaction() as state:
            state['_user_id'] = auth_id(client, member_id)
            state['_fresh'] = True
        return event_id
    return prepare


@pytest.mark.parametrize('case', ['disabled', 'absent', 'existing', 'success', 'invalid', 'get'])
@pytest.mark.parametrize('target', ['https://example.invalid/audit', '//example.invalid/audit',
                                  '/events/cleanup?tab=ratings#pending'])
@pytest.mark.parametrize('source', ['query', 'form'])
def test_rating_return_paths(app, client, rating_case, case, target, source):
    event_id = rating_case(case)
    path = f'/ratings/event/{event_id}/rate'
    data = {'food_rating': '4', 'drinks_rating': '5', 'service_rating': '3',
            'highlights': 'Synthetic feedback'}
    if case == 'invalid':
        data['food_rating'] = '9'
    if source == 'query':
        path += '?' + urlencode({'next': target})
    else:
        data['next'] = target
    response = client.get(path, data=data) if case == 'get' else client.post(path, data=data)
    assert response.status_code == 302
    if target.startswith('/events/'):
        assert response.location == target
    elif case == 'disabled':
        assert response.location == f'/events/{event_id}?tab=info'
    else:
        anchor = 'event-ratings-form' if case in ('invalid', 'get') else 'event-ratings-all'
        assert response.location == f'/events/{event_id}?tab=ratings#{anchor}'
    with app.app_context():
        ratings = EventRating.query.filter_by(event_id=event_id).all()
        assert len(ratings) == (1 if case in ('existing', 'success') else 0)
        if case == 'existing':
            assert ratings[0].food_rating == 2
        if case == 'success':
            assert (ratings[0].food_rating, ratings[0].drinks_rating,
                    ratings[0].service_rating) == (4, 5, 3)


def test_rating_still_requires_login(app, client, rating_case):
    event_id = rating_case('success')
    response = app.test_client().post(f'/ratings/event/{event_id}/rate',
                                      data={'next': '//example.invalid'})
    assert response.status_code == 302
    assert '/auth/login' in response.location
    with app.app_context():
        assert EventRating.query.count() == 0


def test_hidden_event_does_not_redirect_or_save(app, client, rating_case):
    event_id = rating_case('success')
    with app.app_context():
        db.session.get(Event, event_id).audience = EventAudience.BOARD
        db.session.commit()
    response = client.post(f'/ratings/event/{event_id}/rate',
                           data={'next': '/events/cleanup', 'food_rating': '4',
                                 'drinks_rating': '4', 'service_rating': '4'})
    assert response.status_code == 403
    with app.app_context():
        assert EventRating.query.count() == 0


def test_rating_csrf_still_required(app, client, rating_case):
    event_id = rating_case('success')
    app.config['WTF_CSRF_ENABLED'] = True
    response = client.post(f'/ratings/event/{event_id}/rate',
                           data={'next': '/events/cleanup', 'food_rating': '4',
                                 'drinks_rating': '4', 'service_rating': '4'})
    assert response.status_code == 400
    with app.app_context():
        assert EventRating.query.count() == 0


def test_invalid_query_allows_valid_form_return(client, rating_case):
    event_id = rating_case('disabled')
    response = client.post(f'/ratings/event/{event_id}/rate?next=//example.invalid',
                           data={'next': '/events/cleanup'})
    assert response.location == '/events/cleanup'
