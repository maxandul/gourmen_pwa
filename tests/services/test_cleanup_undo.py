"""A-029: only an unchanged cleanup result can be undone."""
from datetime import datetime, timedelta
from unittest.mock import Mock
import pytest
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from backend.models.participation import Participation, Esstyp
from backend.models.rating import EventRating
from backend.models.accounting import MemberClaim, ClaimType
from backend.services.cleanup_participation import CleanupParticipationService as Service, CleanupConflict, CleanupFailure
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.fixture
def cleanup_case(app,seed):
    with app.app_context():
        db.session.get(Event,seed[1]).datum=datetime.now()-timedelta(days=2)
        Participation.query.delete();db.session.commit()
    return seed


def apply(case,status='yes'):
    return Service.apply(case[1],db.session.get(Member,case[0]),status)


def undo(case,payload):
    return Service.undo(payload,db.session.get(Member,case[0]))


@pytest.mark.parametrize('existing',[False,True])
def test_unchanged_own_cleanup_can_be_undone(app,cleanup_case,existing):
    with app.app_context():
        if existing:
            db.session.add(Participation(member_id=cleanup_case[0],event_id=cleanup_case[1],teilnahme=False));db.session.commit()
        payload=apply(cleanup_case);assert Participation.query.one().teilnahme
        undo(cleanup_case,payload)
        if existing:assert not Participation.query.one().teilnahme and Participation.query.one().responded_at is None
        else:assert Participation.query.count()==0
        with pytest.raises(CleanupConflict):undo(cleanup_case,payload)


@pytest.mark.parametrize('change',['guess','esstyp','rating','claim','total','attendance','event','replacement'])
def test_later_work_survives_undo(app,cleanup_case,change):
    with app.app_context():
        payload=apply(cleanup_case);row=Participation.query.one();event=db.session.get(Event,cleanup_case[1])
        if change=='guess':row.guess_bill_amount_rappen=10400
        if change=='esstyp':row.esstyp=Esstyp.ALLIN
        if change=='rating':db.session.add(EventRating(event_id=event.id,participant_id=cleanup_case[0],food_rating=3,drinks_rating=3,service_rating=3))
        if change=='claim':db.session.add(MemberClaim(event_id=event.id,member_id=cleanup_case[0],claim_type=ClaimType.ESSENSANTEIL,expected_rappen=1000))
        if change=='total':event.gesamtbetrag_rappen=10000
        if change=='attendance':row.teilnahme=False
        if change=='event':event.restaurant='Changed by organizer'
        if change=='replacement':
            db.session.delete(row);db.session.flush()
            row=Participation(member_id=cleanup_case[0],event_id=event.id,teilnahme=True);db.session.add(row)
        db.session.commit();before=Service.fingerprint(event,row)
        with pytest.raises(CleanupConflict):undo(cleanup_case,payload)
        assert Participation.query.count()==1 and Service.fingerprint(event,row)==before


def test_two_tabs_and_legacy_payload_do_not_revert_newer_answer(app,cleanup_case):
    with app.app_context():
        old=apply(cleanup_case);new=apply(cleanup_case,'no')
        with pytest.raises(CleanupConflict):undo(cleanup_case,old)
        legacy=dict(new);legacy.pop('after')
        with pytest.raises(CleanupConflict):undo(cleanup_case,legacy)
        assert not Participation.query.one().teilnahme
        undo(cleanup_case,new);assert Participation.query.one().teilnahme


def test_commit_failure_can_retry_without_lost_state(app,cleanup_case,monkeypatch):
    with app.app_context():
        payload=apply(cleanup_case)
        with monkeypatch.context() as patch:
            patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(CleanupFailure):undo(cleanup_case,payload)
        assert Participation.query.count()==1
        undo(cleanup_case,payload);assert Participation.query.count()==0


def test_financial_state_and_revoked_access_block_simple_cleanup(app,cleanup_case):
    with app.app_context():
        event=db.session.get(Event,cleanup_case[1]);event.gesamtbetrag_rappen=1000;db.session.commit()
        with pytest.raises(CleanupConflict):apply(cleanup_case)
        assert Participation.query.count()==0
        event.gesamtbetrag_rappen=None;db.session.commit();payload=apply(cleanup_case)
        db.session.get(Member,cleanup_case[0]).is_active=False;db.session.commit()
        with pytest.raises(CleanupConflict):undo(cleanup_case,payload)
        assert Participation.query.count()==1


def test_original_route_later_billbro_guess_is_retained(app,client,cleanup_case):
    with client.session_transaction() as state:state['_user_id']=auth_id(client,cleanup_case[0]);state['_fresh']=True
    assert client.post(f'/events/{cleanup_case[1]}/cleanup/rsvp',data={'status':'yes'}).status_code==302
    assert client.post(f'/billbro/{cleanup_case[1]}/compute',data={'esstyp':'NORMAL','guess_amount':'104.00'}).status_code==302
    assert client.post('/events/cleanup/undo-rsvp').status_code==302
    with app.app_context():assert Participation.query.one().guess_bill_amount_rappen==10400
    with client.session_transaction() as state:
        assert 'cleanup_rsvp_undo' not in state
        assert any('inzwischen geändert' in message for category,message in state.get('_flashes',[]))


def test_route_commit_failure_keeps_undo_for_retry(app,client,cleanup_case,monkeypatch):
    with client.session_transaction() as state:state['_user_id']=auth_id(client,cleanup_case[0]);state['_fresh']=True
    assert client.post(f'/events/{cleanup_case[1]}/cleanup/rsvp',data={'status':'yes'}).status_code==302
    with monkeypatch.context() as patch:
        patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
        assert client.post('/events/cleanup/undo-rsvp').status_code==302
    with client.session_transaction() as state:assert state.get('cleanup_rsvp_undo',{}).get('after')
    with app.app_context():assert Participation.query.count()==1
    assert client.post('/events/cleanup/undo-rsvp').status_code==302
    with app.app_context():assert Participation.query.count()==0
