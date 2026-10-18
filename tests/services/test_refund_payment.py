"""Actual refund outflows preserve gross amounts and cross-year evidence."""
from datetime import date
from unittest.mock import Mock
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from backend.extensions import db
from backend.models.accounting import Account, AccountKind, BankTransaction, Booking, BookingDirection, MemberClaim, FiscalYearStatus
from backend.models.bank_refund_payment import BankRefundPayment
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.member import Member, Role
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.refund_payment import RefundPaymentService as Service
from backend.services.allocation_reversal import AllocationReversalService
from tests.services.test_bank_booking_atomicity import case
from tests.services.test_refund_confirmation import prepare, confirm
from tests.services.test_accounting_year_guards import csrf
from tests.conftest import auth_id


def setup(case):
    confirmation=confirm(case,prepare(case))
    db.session.add(Account(code='6710',name='Synthetic refund',kind=AccountKind.EXPENSE))
    tx=BankTransaction(import_id=case[4],line_key='synthetic-refund-out',booked_date=date(2028,1,2),
        amount_rappen=600,direction=BookingDirection.OUT,buchungstext='Synthetic refund')
    db.session.add(tx);db.session.commit()
    return confirmation,tx


def pay(case,confirmation,tx,amount=400,version=0):
    return Service.allocate(tx.id,confirmation.id,db.session.get(Member,case[0]),expected_version=version,amount_rappen=amount)


def test_partial_cross_year_actual_payment_and_reverse_history(app,case):
    with app.app_context():
        confirmation,tx=setup(case);sourceyear=confirmation.booking.fiscal_year
        sourceyear.status=FiscalYearStatus.CLOSED;db.session.commit()
        first=pay(case,confirmation,tx)
        assert first.allocation.booking.account.code=='6710' and first.allocation.booking.fiscal_year.year==2028
        assert sourceyear.status==FiscalYearStatus.CLOSED and confirmation.open_rappen==200
        assert db.session.get(MemberClaim,case[2]).paid_rappen==8400
        assert PaymentAllocationService.summary(tx)['remaining']==200
        pay(case,confirmation,tx,200,1)
        assert confirmation.open_rappen==0 and Service.available()==[]
        state=PaymentAllocationService.summary(confirmation.allocation.transaction)
        assert (state['booked'],state['confirmed_refund'],state['refunded'])==(9000,0,600)
        assert AccountingService.get_year_summary(first.allocation.booking.fiscal_year_id)['expense_rappen']==600
        assert AccountingService.get_year_summary(sourceyear.id)['income_rappen']==9000
        sourceyear.status=FiscalYearStatus.OPEN;db.session.commit()
        with pytest.raises(AccountingValidationError,match='Rückzahlung zuerst'):
            AllocationReversalService.reverse(case[3],db.session.get(Member,case[0]),expected_version=3,reason='Synthetic')
        AllocationReversalService.reverse(tx.id,db.session.get(Member,case[0]),expected_version=2,reason='Synthetic outgoing correction')
        assert confirmation.open_rappen==600 and BankRefundPayment.query.count()==2
        assert AccountingService.get_year_summary(first.allocation.booking.fiscal_year_id)['expense_rappen']==0
        AllocationReversalService.reverse(case[3],db.session.get(Member,case[0]),expected_version=3,reason='Synthetic source correction')
        assert confirmation.open_rappen==0 and Service.available()==[]


@pytest.mark.parametrize('mode',['excess','bank_excess','stale','closed','inactive','role','commit','reversed','earlier'])
def test_failed_refund_is_atomic(app,case,monkeypatch,mode):
    with app.app_context():
        confirmation,tx=setup(case)
        if mode=='closed':AccountingService.get_or_create_fiscal_year(2028).status=FiscalYearStatus.CLOSED
        if mode=='inactive':Account.query.filter_by(code='6710').one().is_active=False
        if mode=='role':db.session.get(Member,case[0]).role=Role.MEMBER
        if mode=='bank_excess':tx.amount_rappen=300
        if mode=='earlier':tx.booked_date=date(2026,1,1)
        db.session.commit()
        if mode=='reversed':AllocationReversalService.reverse(case[3],db.session.get(Member,case[0]),expected_version=3,reason='Synthetic')
        before=Booking.query.count()
        with monkeypatch.context() as patch:
            if mode=='commit':patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):pay(case,confirmation,tx,601 if mode=='excess' else 400,1 if mode=='stale' else 0)
        assert Booking.query.count()==before and BankRefundPayment.query.count()==0
        assert tx.is_pending and tx.allocation_version==0
        assert BankPaymentAllocation.query.filter_by(bank_transaction_id=tx.id).count()==0


def test_replay_and_another_bank_cannot_over_refund(app,case):
    with app.app_context():
        confirmation,tx=setup(case);pay(case,confirmation,tx,600)
        with pytest.raises(AccountingValidationError):pay(case,confirmation,tx,600)
        other=BankTransaction(import_id=case[4],line_key='synthetic-another-out',booked_date=date(2028,1,3),amount_rappen=600,direction=BookingDirection.OUT,buchungstext='Synthetic other')
        db.session.add(other);db.session.commit()
        with pytest.raises(AccountingValidationError):pay(case,confirmation,other,1)
        assert BankRefundPayment.query.count()==1 and confirmation.paid_rappen==600


def test_original_route_csrf_and_retained_invalid_input(app,client,case):
    with app.app_context():confirmation,tx=setup(case);confirmation_id,tx_id=confirmation.id,tx.id
    with client.session_transaction() as state:state['_user_id']=auth_id(client,case[0]);state['_fresh']=True
    url=f'/accounting/import/tx/{tx_id}/refund-payment'
    page=client.get(f'/accounting/import/tx/{tx_id}/allocations');assert page.status_code==200 and '6710' in page.text
    assert client.post(url,data={'version':0}).status_code in (400,403)
    data={'version':0,'confirmation_id':confirmation_id,'amount_chf':'7.00','csrf_token':csrf(client,app)}
    page=client.post(url,data=data);assert page.status_code==400 and '7.00' in page.text
    data['amount_chf']='6.00';assert client.post(url,data=data).status_code==302
    page=client.get(f'/accounting/import/tx/{tx_id}/allocations');assert 'Zugehörigen Überschuss' in page.text


def test_migration_cycle_and_history_guard():
    spec=importlib.util.spec_from_file_location('refund_payment_migration',Path('migrations/versions/u202c2b20261018_refund_payments.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with sa.create_engine('sqlite://').begin() as conn:
        for table in ('bank_refund_confirmations','bank_payment_allocations'):
            conn.execute(sa.text(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)'))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade();module.downgrade();module.upgrade()
            conn.execute(sa.text('INSERT INTO bank_refund_payments (confirmation_id,allocation_id) VALUES (1,1)'))
            with pytest.raises(RuntimeError,match='history'):module.downgrade()
