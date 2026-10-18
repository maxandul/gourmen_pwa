"""A-059/A-066: source and destination guards share the current year state."""
from datetime import date
import pytest
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import update
from backend.extensions import db
from backend.models.accounting import BudgetEntry,FiscalYear,FiscalYearStatus,Receipt,Booking
from backend.models.member import Member
from backend.services.accounting import AccountingService as Service,AccountingValidationError
from tests.routes.test_booking_values import setup,create


def csrf(client,app):
    with client.session_transaction() as state:state['csrf_token']='synthetic'
    return URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic')


def linked_receipt(setup):
    source=create(setup)
    fy=FiscalYear(year=2027,start_date=date(2027,1,1),end_date=date(2027,12,31))
    db.session.add(fy);db.session.commit()
    target=create(setup,fiscal_year_id=fy.id,booking_date=date(2027,1,1))
    receipt=Receipt(booking_id=source.id,drive_file_id='synthetic-receipt',drive_file_name='synthetic.pdf',
        drive_folder_id='synthetic-folder',file_type='application/pdf',uploader_id=setup[0])
    db.session.add(receipt);db.session.commit()
    return source,target,receipt


@pytest.mark.parametrize('source_status,target_status,allowed',[
    (FiscalYearStatus.OPEN,FiscalYearStatus.OPEN,True),
    (FiscalYearStatus.IN_REVIEW,FiscalYearStatus.OPEN,False),
    (FiscalYearStatus.CLOSED,FiscalYearStatus.OPEN,False),
    (FiscalYearStatus.OPEN,FiscalYearStatus.IN_REVIEW,False),
    (FiscalYearStatus.OPEN,FiscalYearStatus.CLOSED,False)])
def test_receipt_source_and_target_years(app,setup,source_status,target_status,allowed):
    with app.app_context():
        source,target,receipt=linked_receipt(setup)
        source.fiscal_year.status=source_status;target.fiscal_year.status=target_status;db.session.commit()
        if allowed:
            Service.attach_receipt_to_booking(receipt.id,target.id,db.session.get(Member,setup[0]))
        else:
            with pytest.raises(AccountingValidationError,match='Quell- und Zieljahr'):
                Service.attach_receipt_to_booking(receipt.id,target.id,db.session.get(Member,setup[0]))
        db.session.commit();db.session.refresh(receipt)
        assert receipt.booking_id==(target.id if allowed else source.id)


def test_unbound_receipt_can_be_attached_to_open_year(app,setup):
    with app.app_context():
        source,target,receipt=linked_receipt(setup)
        receipt.booking_id=None;source.fiscal_year.status=FiscalYearStatus.CLOSED;db.session.commit()
        Service.attach_receipt_to_booking(receipt.id,target.id,db.session.get(Member,setup[0]))
        assert receipt.booking_id==target.id


@pytest.mark.parametrize('status',[FiscalYearStatus.IN_REVIEW,FiscalYearStatus.CLOSED])
def test_budget_service_and_form_locked_in_review_and_closed(app,client,setup,status):
    with app.app_context():
        Service.set_budget(setup[1],setup[2],1999,db.session.get(Member,setup[0]))
        db.session.get(FiscalYear,setup[1]).status=status;db.session.commit()
        with pytest.raises(AccountingValidationError,match='nicht offen'):
            Service.set_budget(setup[1],setup[2],1,db.session.get(Member,setup[0]))
    response=client.post(f'/accounting/year/{setup[1]}/budget',data=dict(account_id=setup[2],amount_chf='0.01',csrf_token=csrf(client,app)))
    assert response.status_code==302
    page=client.get(f'/accounting/?year={setup[1]}&tab=budget')
    assert page.status_code==200 and f'action="/accounting/year/{setup[1]}/budget"' not in page.text
    with app.app_context():assert BudgetEntry.query.one().amount_rappen==1999


@pytest.mark.parametrize('amount,expected',[('19.99',1999),('0',0),('1.999',None),('NaN',None),('Infinity',None),('-1',None)])
def test_budget_post_uses_exact_finite_rappen(app,client,setup,amount,expected):
    response=client.post(f'/accounting/year/{setup[1]}/budget',data=dict(account_id=setup[2],amount_chf=amount,csrf_token=csrf(client,app)))
    assert response.status_code==302
    with app.app_context():
        if expected is None:assert BudgetEntry.query.count()==0
        else:assert BudgetEntry.query.one().amount_rappen==expected


def test_original_receipt_post_cannot_remove_closed_year_evidence(app,client,setup):
    with app.app_context():
        source,target,receipt=linked_receipt(setup)
        ids=source.id,target.id,receipt.id
        source.fiscal_year.status=FiscalYearStatus.CLOSED;db.session.commit()
    response=client.post(f'/accounting/booking/{ids[1]}/receipt',data=dict(receipt_id=ids[2],csrf_token=csrf(client,app)))
    assert response.status_code==302
    with app.app_context():assert db.session.get(Receipt,ids[2]).booking_id==ids[0]


def test_stale_identity_map_cannot_bypass_review_lock(app,setup):
    with app.app_context():
        fy=db.session.get(FiscalYear,setup[1])
        db.session.execute(update(FiscalYear).where(FiscalYear.id==fy.id).values(status=FiscalYearStatus.IN_REVIEW),
                           execution_options={'synchronize_session':False})
        assert fy.status==FiscalYearStatus.OPEN
        with pytest.raises(AccountingValidationError):
            Service.set_budget(fy.id,setup[2],100,db.session.get(Member,setup[0]))
        assert fy.status==FiscalYearStatus.IN_REVIEW
        assert BudgetEntry.query.count()==0
