import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.participation import Participation, Esstyp
from backend.models.billbro_correction import BillBroCorrection
from backend.models.accounting import MemberClaim
from tests.services.test_billbro_correction import final_round, preview, confirm, url
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot


def type_form(app):
    with app.app_context(): pid = Participation.query.order_by(Participation.id).first().id
    return dict(total='100', invoice='100', paid_by='vereinskonto', reason='Correct eating type', **{f'esstyp_{pid}':'SPARSAM'})


def test_type_only_preview_is_read_only_and_confirmation_rebalances(app,client,final_round):
    with app.app_context():
        first=Participation.query.order_by(Participation.member_id).first()
        first.guess_bill_amount_rappen=9900; first.diff_amount_rappen=100; first.rank=1.5; first.points=2.5; db.session.commit()
    before=snapshot(app,final_round[1]); form=type_form(app)
    token=preview(client,final_round,form)
    assert snapshot(app,final_round[1])==before
    assert confirm(client,final_round,token).status_code==302
    with app.app_context():
        parts=Participation.query.order_by(Participation.member_id).all()
        assert [p.calculated_share_rappen for p in parts]==[2592,3704,3704]
        assert [p.esstyp for p in parts]==[Esstyp.SPARSAM,Esstyp.NORMAL,Esstyp.NORMAL]
        assert (parts[0].guess_bill_amount_rappen,parts[0].diff_amount_rappen,parts[0].rank,parts[0].points)==(9900,100,1.5,2.5)
        assert all(p.teilnahme for p in parts) and sum(c.expected_rappen for c in MemberClaim.query.all())==10000
        history=BillBroCorrection.query.one()
        assert history.before_json['participations'][0]['esstyp']=='NORMAL'
        assert history.after_json['participations'][0]['esstyp']=='SPARSAM'
    assert confirm(client,final_round,token).status_code==302
    with app.app_context(): assert BillBroCorrection.query.count()==1
    response=client.get(url(final_round))
    assert response.status_code==200 and 'Sparsam' in response.text


@pytest.mark.parametrize('value',['','UNKNOWN','<invalid>'])
def test_invalid_type_is_retained_and_changes_nothing(app,client,final_round,value):
    form=type_form(app); key=next(k for k in form if k.startswith('esstyp_')); form[key]=value
    before=snapshot(app,final_round[1])
    response=client.post(url(final_round),data=form)
    assert response.status_code==400 and 'gültigen Ess-Typ' in response.text
    if value=='<invalid>': assert '&lt;invalid&gt;' in response.text
    assert snapshot(app,final_round[1])==before


def test_unknown_participant_field_cannot_be_applied(app,client,final_round):
    form=type_form(app);form['esstyp_999999']='ALLIN'
    assert client.post(url(final_round),data=form).status_code==400
    with app.app_context(): assert BillBroCorrection.query.count()==0


def test_type_write_failure_rolls_back_distribution_and_claims(app,client,final_round):
    token=preview(client,final_round,type_form(app));before=snapshot(app,final_round[1])
    def fail(*args): raise OperationalError('synthetic',{},Exception('synthetic'))
    sa_event.listen(Participation,'before_update',fail)
    try: assert confirm(client,final_round,token).status_code==400
    finally: sa_event.remove(Participation,'before_update',fail)
    assert snapshot(app,final_round[1])==before
    assert confirm(client,final_round,token).status_code==302


def test_v2_preview_requires_new_type_aware_preview(app,client,final_round):
    from itsdangerous import URLSafeTimedSerializer
    from backend.services.billbro_correction import BillBroCorrectionService
    token=preview(client,final_round,type_form(app))
    with app.app_context():
        payload=BillBroCorrectionService.serializer().loads(token)
        payload['proposed'].pop('types')
        token=URLSafeTimedSerializer(app.config['SECRET_KEY'],salt='billbro-correction-v2').dumps(payload)
    assert confirm(client,final_round,token).status_code==400
