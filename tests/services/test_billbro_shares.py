"""A-031: sum preservation, deterministic cents and original finalization routes."""
from fractions import Fraction
from datetime import datetime
from itertools import permutations
from urllib.parse import unquote
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.event import Event, BillPaidBy
from backend.models.member import Member
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim
from backend.services.billbro_shares import BillBroShareService as Shares, ShareError
from backend.services.money import MoneyService
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


def test_equal_remainders_stable_member_id_and_input_order():
    for order in permutations([(7,1),(2,1),(4,1)]):
        assert Shares.distribute(10000,order)=={2:3334,4:3333,7:3333}


@pytest.mark.parametrize('total',[1,2,3,99,10000,MoneyService.MAX_RAPPEN])
def test_weighted_shares_sum_and_deviation_less_than_one_rappen(total):
    weights={9:Fraction(7,10),2:Fraction(1),5:Fraction(13,10)}
    actual=Shares.distribute(total,[(9,'0.7'),(2,1),(5,1.3)])
    assert sum(actual.values())==total and all(value>=0 for value in actual.values())
    for mid,weight in weights.items():
        assert abs(actual[mid]-total*weight/sum(weights.values()))<1


@pytest.mark.parametrize('weight',[None,0,-1,'NaN','Infinity',True,'1e100000','0'*41])
def test_invalid_weights(weight):
    with pytest.raises(ShareError):Shares.distribute(100,[(1,weight)])


@pytest.mark.parametrize('members',[[],[(1,1),(1,2)],[(None,1)]])
def test_no_or_ambiguous_participants(members):
    with pytest.raises(ShareError):Shares.distribute(100,members)


@pytest.fixture
def round_data(app,client,seed):
    with app.app_context():
        event=db.session.get(Event,seed[1]);event.rechnungsbetrag_rappen=10000;event.trinkgeld_rappen=0;event.bill_paid_by=BillPaidBy.VEREINSKONTO
        first=Participation.query.one();first.teilnahme=True;first.esstyp=Esstyp.NORMAL
        for index in range(2):
            member=Member(vorname=f'Synthetic{index}',nachname='Share',passwort_hash='unused',password_changed_at=datetime(2026,1,1),email=f'share{index}@example.com')
            db.session.add(member);db.session.flush()
            db.session.add(Participation(member_id=member.id,event_id=event.id,teilnahme=True,esstyp=Esstyp.NORMAL))
        db.session.commit()
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    return seed


@pytest.mark.parametrize('endpoint',['set_total','accept_suggested_total'])
def test_original_finalization_claims_display_and_repeat(app,client,round_data,endpoint):
    url=f'/billbro/{round_data[1]}/{endpoint}'
    assert client.post(url,data={'gesamtbetrag_manual':'100.00'}).status_code==302
    with app.app_context():
        event=db.session.get(Event,round_data[1]);parts=Participation.query.order_by(Participation.member_id).all()
        assert [p.calculated_share_rappen for p in parts]==[3334,3333,3333]
        assert event.rounding_rule==Shares.RULE and event.betrag_normal_rappen is None
        assert sum(c.expected_rappen for c in MemberClaim.query.all())==10000
        assert Shares.groups(event)[1]==dict(label='Normal',minimum=3333,maximum=3334)
    response=client.get(f'/events/{round_data[1]}?tab=billbro')
    assert response.status_code==200 and '33.34 CHF' in response.text and '33.33' in response.text
    sync=client.get(f'/events/{round_data[1]}/billbro-sync')
    assert sync.status_code==200 and sync.json['own_share_rappen']==3334
    assert sync.json['betrag_normal_rappen'] is None and sync.json['rounding_rule']==Shares.RULE
    response=client.get(f'/billbro/{round_data[1]}/share_whatsapp')
    assert response.status_code==302
    assert '33.34 CHF' in unquote(response.location) and '33.33 CHF' in unquote(response.location)
    assert client.post(url,data={'gesamtbetrag_manual':'120.00'}).status_code==400
    with app.app_context():
        assert db.session.get(Event,round_data[1]).gesamtbetrag_rappen==10000
        assert MemberClaim.query.count()==3 and sum(c.expected_rappen for c in MemberClaim.query.all())==10000


@pytest.mark.parametrize('invalid',['missing_type','missing_weights','invalid_weight','empty'])
def test_invalid_round_preserves_everything(app,client,round_data,invalid):
    with app.app_context():
        event=db.session.get(Event,round_data[1]);part=Participation.query.first()
        if invalid=='missing_type':part.esstyp=None
        if invalid=='missing_weights':event.weights_used_json={}
        if invalid=='invalid_weight':event.weights_used_json={'normal':-1}
        if invalid=='empty':
            for part in event.participations:part.teilnahme=False
        db.session.commit()
    response=client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'})
    assert response.status_code==400
    with app.app_context():
        assert db.session.get(Event,round_data[1]).gesamtbetrag_rappen is None
        assert all(p.calculated_share_rappen is None for p in Participation.query.all())
        assert MemberClaim.query.count()==0


@pytest.mark.parametrize('failure',['claim_insert','commit'])
def test_failure_rolls_back_final_and_all_claims(app,client,round_data,monkeypatch,failure):
    def fail(*args,**kwargs):raise OperationalError('synthetic',{},Exception('synthetic'))
    if failure=='claim_insert':sa_event.listen(MemberClaim,'before_insert',fail)
    else:monkeypatch.setattr(db.session,'commit',fail)
    try:
        response=client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'})
        assert response.status_code==400 and 'nicht gespeichert' in response.text
    finally:
        if failure=='claim_insert':sa_event.remove(MemberClaim,'before_insert',fail)
    with app.app_context():
        event=db.session.get(Event,round_data[1]);assert event.gesamtbetrag_rappen is None and event.rounding_rule=='ceil_10'
        assert MemberClaim.query.count()==0 and all(p.calculated_share_rappen is None for p in Participation.query.all())


def test_private_payer_own_share_and_claims_sum(app,client,round_data):
    with app.app_context():
        event=db.session.get(Event,round_data[1]);event.bill_paid_by=BillPaidBy.MITGLIED;event.bill_payer_member_id=round_data[0];db.session.commit()
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'}).status_code==302
    with app.app_context():
        own=Participation.query.filter_by(member_id=round_data[0]).one()
        assert MemberClaim.query.count()==2
        assert sum(c.expected_rappen for c in MemberClaim.query.all())+own.calculated_share_rappen==10000


def test_zero_shares_visible_without_fictitious_claims(app,client,round_data):
    with app.app_context():
        event=db.session.get(Event,round_data[1]);event.rechnungsbetrag_rappen=1;db.session.commit()
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'0.01'}).status_code==302
    with app.app_context():
        parts=Participation.query.order_by(Participation.member_id).all()
        assert [p.calculated_share_rappen for p in parts]==[1,0,0] and MemberClaim.query.count()==1
        zero_member=parts[1].member_id
    with client.session_transaction() as state:state['_user_id']=auth_id(client,zero_member);state['_fresh']=True
    response=client.get(f'/events/{round_data[1]}?tab=billbro')
    assert response.status_code==200 and '0.00 CHF' in response.text


def test_historical_results_are_not_recomputed(app,client,round_data):
    with app.app_context():
        event=db.session.get(Event,round_data[1]);event.gesamtbetrag_rappen=10000;event.betrag_normal_rappen=3335
        db.session.commit()
    response=client.get(f'/events/{round_data[1]}?tab=billbro')
    assert response.status_code==200 and '33.35 CHF' in response.text
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'}).status_code==400
    with app.app_context():
        event=db.session.get(Event,round_data[1]);assert event.betrag_normal_rappen==3335 and event.rounding_rule=='ceil_10'
        assert MemberClaim.query.count()==0


@pytest.mark.parametrize('total',[0,-1,1.5,True,MoneyService.MAX_RAPPEN+1])
def test_invalid_total(total):
    with pytest.raises(ShareError):Shares.distribute(total,[(1,1)])


def test_absent_participant_does_not_take_share(app,client,round_data):
    with app.app_context():
        absent=Participation.query.order_by(Participation.member_id.desc()).first()
        absent.teilnahme=False;absent.esstyp=None;db.session.commit()
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'}).status_code==302
    with app.app_context():
        parts=Participation.query.order_by(Participation.member_id).all()
        assert [p.calculated_share_rappen for p in parts]==[5000,5000,None]
        assert MemberClaim.query.count()==2


def test_old_reset_with_preserved_paid_claims_cannot_recalculate(app,client,round_data):
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'100'}).status_code==302
    with app.app_context():
        event=db.session.get(Event,round_data[1]);event.gesamtbetrag_rappen=None
        claim=MemberClaim.query.first();claim.paid_rappen=1000;db.session.commit()
    assert client.post(f'/billbro/{round_data[1]}/set_total',data={'gesamtbetrag_manual':'120'}).status_code==400
    with app.app_context():
        assert sum(c.expected_rappen for c in MemberClaim.query.all())==10000
        assert sum(c.paid_rappen for c in MemberClaim.query.all())==1000
        assert sum(p.calculated_share_rappen for p in Participation.query.all())==10000
