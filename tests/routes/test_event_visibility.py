"""Synthetic visibility regressions; no real services or membership data."""
from datetime import datetime, timedelta
import pytest
from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.event import Event, EventType, EventAudience
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.accounting import MemberClaim, ClaimType
from backend.services.calendar_feed import CalendarFeedService
from backend.services.monatsessen_stats import get_monatsessen_statistics, get_landing_restaurant_table, get_landing_extras
from tests.conftest import auth_id


@pytest.fixture
def visibility_data(app):
    with app.app_context():
        members = [Member(vorname=name, nachname='Synthetic', email=f'{name}@example.test',
                          passwort_hash='unused', password_changed_at=datetime(2026, 1, 1),
                          vorstandsmitglied=name == 'Board', role=Role.ADMIN if name == 'Admin' else Role.MEMBER)
                   for name in ['Organizer', 'Reader', 'Board', 'Admin']]
        db.session.add_all(members); db.session.flush()
        events=[]
        for audience in [EventAudience.ALL, EventAudience.BOARD]:
            for future in [False, True]:
                event=Event(organisator_id=members[0].id, datum=datetime.now()+timedelta(days=10 if future else -10),
                            season=2026, event_typ=EventType.MONATSESSEN, audience=audience,
                            restaurant=f'{audience.value}-{"future" if future else "past"}-private-marker',
                            published=True, allow_ratings=True)
                db.session.add(event); db.session.flush(); events.append(event)
                db.session.add(EventRating(event_id=event.id, participant_id=members[0].id,
                                           food_rating=4, drinks_rating=4, service_rating=4,
                                           highlights='internal-comment-marker'))
        db.session.commit()
        return [m.id for m in members], [e.id for e in events]


def login(client, mid):
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,mid); state['_fresh']=True


@pytest.mark.parametrize('actor,visible', [(0,True),(1,False),(2,True),(3,True)])
def test_board_visibility_across_detail_api_lists_statistics(app, client, visibility_data, actor, visible):
    members, events=visibility_data; login(client,members[actor])
    for path in [f'/events/{events[2]}', f'/ratings/event/{events[2]}/ratings/api']:
        response=client.get(path)
        assert response.status_code == (200 if visible else 403)
        assert ('internal-comment-marker' in response.get_data(as_text=True)) == visible
    for path in ['/events/?tab=archiv','/events/?tab=stats','/events/?tab=kommend']:
        response=client.get(path); assert response.status_code == 200
        assert ('board-' in response.get_data(as_text=True)) == visible
    with app.app_context():
        stats=get_monatsessen_statistics(now=datetime.now(),season_year=None,organizer_id=None,current_member_id=members[actor])
        assert stats['count_past_monatsessen'] == (2 if visible else 1)
        assert stats['user_eligible_count'] == (2 if visible else 1)


def test_nonparticipant_can_read_but_not_write(app,client,visibility_data):
    members,events=visibility_data; login(client,members[1])
    assert client.get(f'/ratings/event/{events[0]}/ratings/api').status_code == 200
    assert 'internal-comment-marker' in client.get(f'/events/{events[0]}').get_data(as_text=True)
    response=client.get(f'/ratings/event/{events[0]}/ratings'); assert response.status_code == 302
    assert response.location.endswith('?tab=ratings')
    client.post(f'/ratings/event/{events[0]}/rate',data={'food_rating':5,'drinks_rating':5,'service_rating':5})
    with app.app_context():
        assert EventRating.query.filter_by(participant_id=members[1]).count() == 0
    assert app.test_client().get(f'/ratings/event/{events[0]}/ratings/api').status_code == 302


def test_public_excludes_board_details_and_internal_comments(app,client,visibility_data):
    with app.app_context():
        rows,*_=get_landing_restaurant_table(datetime.now())
        assert len(rows)==1 and rows[0]['restaurant'].startswith('all-')
        assert rows[0]['overall_avg']==4
        extras=get_landing_extras(datetime.now())
        assert extras['last_restaurant'].startswith('all-')
        assert extras['next_essen_restaurant'].startswith('all-')
    for path in ['/','/restaurants']:
        response=client.get(path); assert response.status_code==200
        body=response.get_data(as_text=True)
        assert 'board-past-private-marker' not in body and 'board-future-private-marker' not in body
        assert 'internal-comment-marker' not in body and 'Organizer Synthetic' not in body


@pytest.mark.parametrize('requested,event_type,expected', [('board','MONATSESSEN','board'),('all','MONATSESSEN','all'),('all','VORSTANDSSITZUNG','board')])
def test_edit_audience_and_calendar(app,client,visibility_data,requested,event_type,expected):
    members,events=visibility_data; login(client,members[0]); eid=events[3]
    with app.app_context():
        ev=db.session.get(Event,eid)
        ev.audience=EventAudience.ALL if requested=='board' else EventAudience.BOARD
        db.session.commit()
    response=client.post(f'/events/{eid}/edit',data={
        'datum':(datetime.now()+timedelta(days=10)).strftime('%Y-%m-%d'),
        'event_typ':event_type,'audience':requested,'organisator_id':members[0],
        'restaurant':'changed-visibility-marker'})
    assert response.status_code==302
    with app.app_context():
        assert db.session.get(Event,eid).audience.value==expected
        for index in [0,1,2,3]:
            feed=CalendarFeedService.generate_feed_for_member(db.session.get(Member,members[index])).decode()
            assert ('changed-visibility-marker' in feed)==(expected=='all' or index==2)
    login(client,members[1])
    assert client.get(f'/events/{eid}').status_code==(200 if expected=='all' else 403)


def test_invalid_audience_does_not_mutate(app,client,visibility_data):
    members,events=visibility_data; login(client,members[0])
    response=client.post(f'/events/{events[0]}/edit',data={'datum':'2026-01-01','event_typ':'MONATSESSEN',
        'audience':'invalid','organisator_id':members[0]})
    assert response.status_code==200
    with app.app_context(): assert db.session.get(Event,events[0]).audience==EventAudience.ALL


def test_dashboard_preserves_claims_without_hidden_event_details(app,client,visibility_data):
    members,events=visibility_data
    with app.app_context():
        db.session.add(Participation(member_id=members[1],event_id=events[2],teilnahme=True,calculated_share_rappen=12345))
        db.session.add(MemberClaim(member_id=members[1],event_id=events[2],claim_type=ClaimType.ESSENSANTEIL,expected_rappen=12345))
        db.session.commit()
    login(client,members[1]); response=client.get('/dashboard/'); assert response.status_code==200
    body=response.get_data(as_text=True)
    assert 'board-past-private-marker' not in body and 'board-future-private-marker' not in body
    assert f'/events/{events[2]}' not in body
    assert '123.45' in body and 'Geschuetztes Event' in body
    with app.app_context():
        claim=MemberClaim.query.one(); assert claim.open_rappen==12345

