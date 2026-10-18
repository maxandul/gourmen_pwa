"""Synthetic travel scope boundaries; network blocked by isolated runner."""
from datetime import datetime
import pytest
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.event import Event, EventType
from backend.models.member_area_grant import MemberAreaGrant
from backend.services.area_permissions import AreaPermissionService
from tests.routes.test_event_visibility import visibility_data, login


@pytest.fixture
def travel_case(app, visibility_data):
    members, events = visibility_data
    with app.app_context():
        for eid in [events[0], events[2]]:
            db.session.get(Event, eid).event_typ = EventType.AUSFLUG
        db.session.commit()
    return members, events


@pytest.mark.parametrize('kind', ['grant', 'function', 'member', 'organizer', 'admin'])
def test_manage_matrix(app, client, travel_case, kind, monkeypatch):
    members, events = travel_case
    actor = members[0] if kind == 'organizer' else members[3] if kind == 'admin' else members[1]
    with app.app_context():
        if kind == 'grant':
            db.session.add(MemberAreaGrant(member_id=actor, scope='travel_manage', granted_by=members[3]))
        if kind == 'function':
            db.session.get(Member, actor).funktion = Funktion.REISEKOMMISSAR
        db.session.commit()
    login(client, actor)
    for index in [0, 1, 2]:
        eid = events[index]
        allowed = kind in ['admin', 'organizer'] or (index == 0 and kind in ['grant', 'function'])
        hidden = index == 2 and kind not in ['admin', 'organizer']
        assert client.get(f'/events/{eid}/edit').status_code == (403 if hidden else 200 if allowed else 302)
        page = client.get(f'/events/{eid}?tab=billbro')
        assert (f'/events/{eid}/edit' in page.get_data(as_text=True)) == allowed
        client.post(f'/billbro/{eid}/toggle_status')
        with app.app_context():
            assert bool(db.session.get(Event, eid).billbro_closed) == allowed
    if kind in ['grant', 'function']:
        from backend.services.push_notifications import PushNotificationService
        monkeypatch.setattr(PushNotificationService, 'send_participation_reminder_to_members', lambda *a, **k: pytest.fail('Unauthorized notification'))
        assert client.post(f'/events/{events[0]}/send_rsvp_reminder').status_code == 302
        assert client.get('/events/year-planning').status_code == 302
        assert client.get(f'/admin/members/{members[0]}/sensitive').status_code == 403


def test_creation_type_tampering_and_revocation(app, client, travel_case):
    members, events = travel_case
    with app.app_context():
        db.session.add(MemberAreaGrant(member_id=members[1], scope='travel_manage', granted_by=members[3]))
        db.session.commit()
    login(client, members[1])
    assert client.get('/admin/events/new').status_code == 200
    assert '/admin/events/new' in client.get('/events/').get_data(as_text=True)
    data = {'datum':'2027-06-01', 'event_typ':'MONATSESSEN', 'audience':'all', 'organisator_id':members[0]}
    assert client.post('/admin/events/new', data=data).status_code == 200
    assert client.post(f'/events/{events[0]}/edit', data=data).status_code == 200
    with app.app_context():
        assert Event.query.count() == 4
        assert db.session.get(Event, events[0]).event_typ == EventType.AUSFLUG
        assert not AreaPermissionService.has_scope(db.session.get(Member,members[1]), 'travel_documents')
    # Assigning oneself must not permit a subsequent type escalation.
    with app.app_context():
        db.session.get(Event,events[0]).organisator_id = members[1]; db.session.commit()
    assert client.post(f'/events/{events[0]}/edit', data=data).status_code == 200
    data['event_typ'] = 'AUSFLUG'
    assert client.post('/admin/events/new', data=data).status_code == 302
    assert client.post(f'/events/{events[0]}/edit', data=data).status_code == 302
    with app.app_context():
        assert Event.query.count() == 5
        member = db.session.get(Member,members[1]); member.is_active = False
        assert not AreaPermissionService.can_manage_event(member, db.session.get(Event,events[0]))
        member.is_active = True
        MemberAreaGrant.query.one().revoked_at = datetime.now(); db.session.commit()
    assert client.get('/admin/events/new').status_code == 403
    assert client.get(f'/events/{events[0]}/edit').status_code == 302
