"""A-033: changing responsibility never changes attendance or paid claims."""
from datetime import datetime, timedelta
from unittest.mock import Mock
import pytest
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim, ClaimType, ClaimStatus
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.mark.parametrize('new_attendance',[None,False,True])
@pytest.mark.parametrize('finalized',[False,True])
def test_organizer_change_preserves_both_members_and_financial_history(app,client,seed,new_attendance,finalized):
    with app.app_context():
        new=Member(vorname='New',nachname='Synthetic',email='new-organizer@example.com',passwort_hash='unused')
        db.session.add(new);db.session.flush();new_id=new.id
        old=Participation.query.one();old.teilnahme=True;old.esstyp=Esstyp.NORMAL;old.guess_bill_amount_rappen=10000;old.calculated_share_rappen=4000
        if new_attendance is not None:db.session.add(Participation(member_id=new.id,event_id=seed[1],teilnahme=new_attendance,esstyp=Esstyp.ALLIN,guess_bill_amount_rappen=11000))
        event=db.session.get(Event,seed[1]);event.billbro_closed=finalized;event.gesamtbetrag_rappen=4000 if finalized else None
        claim=MemberClaim(member_id=seed[0],event_id=seed[1],claim_type=ClaimType.ESSENSANTEIL,expected_rappen=4000,paid_rappen=1000,status=ClaimStatus.TEILWEISE)
        db.session.add(claim);db.session.commit()
        before=[(p.id,p.member_id,p.teilnahme,p.esstyp,p.guess_bill_amount_rappen,p.calculated_share_rappen,p.responded_at) for p in Participation.query.order_by(Participation.id)]
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    response=client.post(f'/events/{seed[1]}/edit',data={'datum':(datetime.now()+timedelta(days=10)).strftime('%Y-%m-%d'),'event_typ':'MONATSESSEN','audience':'all','organisator_id':new_id,'restaurant':'Synthetic'})
    assert response.status_code==302
    with app.app_context():
        assert db.session.get(Event,seed[1]).organisator_id==new_id
        after=[(p.id,p.member_id,p.teilnahme,p.esstyp,p.guess_bill_amount_rappen,p.calculated_share_rappen,p.responded_at) for p in Participation.query.order_by(Participation.id)]
        assert after==before
        claim=MemberClaim.query.one();assert (claim.expected_rappen,claim.paid_rappen,claim.status)==(4000,1000,ClaimStatus.TEILWEISE)
    with client.session_transaction() as state:
        messages=' '.join(message for category,message in state.get('_flashes',[]))
        assert 'bleiben unverändert' in messages and 'automatisch als Teilnehmer' not in messages


def test_failed_event_commit_preserves_organizer_and_participation(app,client,seed,monkeypatch):
    with app.app_context():
        new=Member(vorname='New',nachname='Synthetic',email='other-organizer@example.com',passwort_hash='unused');db.session.add(new);db.session.commit();new_id=new.id
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    with monkeypatch.context() as patch:
        patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
        response=client.post(f'/events/{seed[1]}/edit',data={'datum':(datetime.now()+timedelta(days=10)).strftime('%Y-%m-%d'),'event_typ':'MONATSESSEN','audience':'all','organisator_id':new_id,'restaurant':'Synthetic'})
    assert response.status_code==200
    with app.app_context():
        assert db.session.get(Event,seed[1]).organisator_id==seed[0]
        assert Participation.query.one().member_id==seed[0]
