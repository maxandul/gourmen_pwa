"""A-025: exact finite positive money before any BillBro mutation."""
import pytest
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation, Esstyp
from backend.models.audit_event import AuditEvent
from backend.models.accounting import MemberClaim
from backend.services.money import MoneyService
from tests.services.test_audit_failure_boundary import seed
from tests.conftest import auth_id


@pytest.fixture
def billbro(app,client,seed):
    with app.app_context():
        event=db.session.get(Event,seed[1]);event.rechnungsbetrag_rappen=10000;event.trinkgeld_rappen=700
        part=Participation.query.one();part.teilnahme=True;part.esstyp=Esstyp.NORMAL;part.guess_bill_amount_rappen=9000;part.rank=2;part.points=3
        db.session.commit()
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    return seed


@pytest.mark.parametrize('value,expected', [('19.99',1999),('0.01',1),('1’234.56',123456),("CHF 1'234,56",123456),('1 234.50',123450),('21474836.47',2147483647)])
def test_swiss_exact_amounts(value,expected):
    assert MoneyService.parse_positive_rappen(value)==expected


@pytest.mark.parametrize('value',['',None,'-1','0','abc','NaN','sNaN','Infinity','1e10','19.999','21474836.48','1,2,3',"1'23.00"])
def test_invalid_parser_inputs(value):
    with pytest.raises(ValueError):MoneyService.parse_positive_rappen(value)


@pytest.mark.parametrize('endpoint,field',[('enter_bill','rechnungsbetrag'),('compute','guess_amount'),('record_guess','guess_amount'),('set_total','gesamtbetrag_manual')])
@pytest.mark.parametrize('value',['abc','NaN','-10','0','19.999','21474836.48'])
def test_invalid_original_posts_leave_all_financial_fields_unchanged(app,client,billbro,endpoint,field,value):
    url=f'/billbro/{billbro[1]}/{endpoint}'+(f'/{billbro[0]}' if endpoint=='record_guess' else '')
    response=client.post(url,data={field:value,'esstyp':'ALLIN'})
    assert response.status_code==400 and 'aria-invalid="true"' in response.text and value in response.text
    with app.app_context():
        event=db.session.get(Event,billbro[1]);part=Participation.query.one()
        assert (event.rechnungsbetrag_rappen,event.trinkgeld_rappen,event.gesamtbetrag_rappen)==(10000,700,None)
        assert (part.esstyp,part.guess_bill_amount_rappen,part.rank,part.points)==(Esstyp.NORMAL,9000,2,3)
        assert AuditEvent.query.count()==0 and MemberClaim.query.count()==0


def test_ajax_error_names_field_and_corrected_post_succeeds(app,client,billbro):
    url=f'/billbro/{billbro[1]}/compute'
    response=client.post(url,data={'guess_amount':'NaN','esstyp':'ALLIN'},headers={'X-Requested-With':'XMLHttpRequest'})
    assert response.status_code==400 and 'guess_amount' in response.json['errors']
    response=client.post(url,data={'guess_amount':'CHF 1’234,56','esstyp':'ALLIN'})
    assert response.status_code==302
    with app.app_context():assert Participation.query.one().guess_bill_amount_rappen==123456


@pytest.mark.parametrize('endpoint',['set_total','accept_suggested_total'])
def test_automatic_total_overflow_does_not_mutate(app,client,billbro,endpoint):
    with app.app_context():
        event=db.session.get(Event,billbro[1]);event.rechnungsbetrag_rappen=MoneyService.MAX_RAPPEN;event.trinkgeld_rappen=700;db.session.commit()
    response=client.post(f'/billbro/{billbro[1]}/{endpoint}')
    assert response.status_code==400
    with app.app_context():assert db.session.get(Event,billbro[1]).gesamtbetrag_rappen is None


def test_manual_total_cannot_undercut_bill(app,client,billbro):
    response=client.post(f'/billbro/{billbro[1]}/set_total',data={'gesamtbetrag_manual':'99.99'})
    assert response.status_code==400 and '99.99' in response.text
    with app.app_context():assert db.session.get(Event,billbro[1]).gesamtbetrag_rappen is None


def test_valid_invoice_preserves_exact_cents(app,client,billbro):
    response=client.post(f'/billbro/{billbro[1]}/enter_bill',data={'rechnungsbetrag':'19,99'})
    assert response.status_code==302
    with app.app_context():assert db.session.get(Event,billbro[1]).rechnungsbetrag_rappen==1999


@pytest.mark.parametrize('endpoint,field',[('enter_bill','rechnungsbetrag'),('compute','guess_amount'),('record_guess','guess_amount')])
def test_empty_required_amount_is_field_error(app,client,billbro,endpoint,field):
    url=f'/billbro/{billbro[1]}/{endpoint}'+(f'/{billbro[0]}' if endpoint=='record_guess' else '')
    assert client.post(url,data={field:'','esstyp':'NORMAL'}).status_code==400
    with app.app_context():assert AuditEvent.query.count()==0


def test_zero_tip_total_is_valid(app,client,billbro):
    response=client.post(f'/billbro/{billbro[1]}/set_total',data={'gesamtbetrag_manual':'100.00'})
    assert response.status_code==302
    with app.app_context():
        event=db.session.get(Event,billbro[1]);assert (event.gesamtbetrag_rappen,event.trinkgeld_rappen)==(10000,0)
