"""Confirmed surplus is income, never an outgoing payment or claim payment."""
from unittest.mock import Mock
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from backend.extensions import db
from backend.models.accounting import Account, AccountKind, BankTransactionStatus, BankTransaction, Booking, MemberClaim, FiscalYearStatus
from backend.models.member import Member, Role
from backend.models.bank_refund_confirmation import BankRefundConfirmation
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.refund_confirmation import RefundConfirmationService as Service
from backend.services.allocation_reversal import AllocationReversalService
from tests.services.test_bank_booking_atomicity import case
from tests.services.test_payment_allocations import allocate
from tests.services.test_accounting_year_guards import csrf
from tests.conftest import auth_id


def prepare(case, member=True):
    tx=db.session.get(BankTransaction,case[3]);tx.amount_rappen=9000
    claim=db.session.get(MemberClaim,case[2]);claim.expected_rappen=8400
    db.session.add(Account(code='3620',name='Synthetic surplus',kind=AccountKind.INCOME));db.session.commit()
    allocate(case,amount=8400)
    return allocate(case,version=1,amount=600,kind='refund',member_id=case[0] if member else None)


def confirm(case,row,version=2):
    return Service.confirm(case[3],row.id,db.session.get(Member,case[0]),expected_version=version)


def test_90_received_84_claim_6_confirmed_then_reversed(app,case):
    with app.app_context():
        row=prepare(case);result=confirm(case,row);tx=db.session.get(BankTransaction,case[3])
        assert result.booking.account.code=='3620' and result.booking.amount_rappen==600
        assert result.booking.booking_date==tx.booked_date and result.booking.fiscal_year.year==2027
        assert tx.status==BankTransactionStatus.BOOKED and tx.amount_rappen==9000 and tx.allocation_version==3
        assert db.session.get(MemberClaim,case[2]).paid_rappen==8400
        state=PaymentAllocationService.summary(tx)
        assert (state['booked'],state['refund'],state['confirmed_refund'],state['remaining'])==(9000,0,600,0)
        assert AccountingService.get_year_summary(result.booking.fiscal_year_id)['income_rappen']==9000
        with pytest.raises(AccountingValidationError):confirm(case,row,3)
        with pytest.raises(AccountingValidationError):AccountingService.update_booking(result.booking.id,amount_rappen=700)
        AllocationReversalService.reverse(tx.id,db.session.get(Member,case[0]),expected_version=3,reason='Synthetic correction')
        assert Booking.query.count()==2 and all(b.reversal_id for b in Booking.query.all())
        assert BankRefundConfirmation.query.count()==1 and db.session.get(MemberClaim,case[2]).paid_rappen==0
        assert AccountingService.get_year_summary(result.booking.fiscal_year_id)['income_rappen']==0
        assert PaymentAllocationService.summary(tx)['confirmed_refund']==0


@pytest.mark.parametrize('mode',['member','stale','closed','review','inactive','direction','role','commit'])
def test_invalid_or_failed_confirmation_has_no_durable_effect(app,case,monkeypatch,mode):
    with app.app_context():
        row=prepare(case,member=mode!='member');tx=db.session.get(BankTransaction,case[3])
        account=Account.query.filter_by(code='3620').one()
        if mode=='inactive':account.is_active=False
        if mode=='direction':account.kind=AccountKind.EXPENSE
        if mode=='role':db.session.get(Member,case[0]).role=Role.MEMBER
        if mode in ('closed','review'):
            Booking.query.one().fiscal_year.status=FiscalYearStatus.CLOSED if mode=='closed' else FiscalYearStatus.IN_REVIEW
        db.session.commit()
        with monkeypatch.context() as patch:
            if mode=='commit':patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):confirm(case,row,1 if mode=='stale' else 2)
        assert BankRefundConfirmation.query.count()==0 and Booking.query.count()==1
        assert tx.is_pending and tx.allocation_version==2
        assert db.session.get(MemberClaim,case[2]).paid_rappen==8400


def test_confirmation_then_remaining_allocation_finishes_source(app,case):
    with app.app_context():
        db.session.add(Account(code='3620',name='Synthetic',kind=AccountKind.INCOME));db.session.commit()
        row=allocate(case,amount=500,kind='refund',member_id=case[0]);confirm(case,row,1)
        tx=db.session.get(BankTransaction,case[3]);assert tx.is_pending
        allocate(case,version=2,amount=2000)
        assert tx.status==BankTransactionStatus.BOOKED and tx.booking_id==row.effective_booking.id


def test_original_route_csrf_confirmation_and_history(app,client,case):
    with app.app_context():row_id=prepare(case).id
    with client.session_transaction() as state:state['_user_id']=auth_id(client,case[0]);state['_fresh']=True
    url=f'/accounting/import/tx/{case[3]}/refund/{row_id}/confirm'
    assert client.post(url,data={'version':2}).status_code in (400,403)
    data={'version':2,'csrf_token':csrf(client,app)}
    assert client.post(url,data=data).status_code==302
    assert client.post(url,data=data).status_code==400
    page=client.get(f'/accounting/import/tx/{case[3]}/allocations')
    assert page.status_code==200 and '3620' in page.text and 'Rückzahlung offen' in page.text


def test_migration_cycle_and_history_guard():
    spec=importlib.util.spec_from_file_location('refund_migration',Path('migrations/versions/u202c2a20261018_refund_confirmation.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with sa.create_engine('sqlite://').begin() as conn:
        for table in ('members','bookings','bank_payment_allocations'):
            conn.execute(sa.text(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)'))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade();module.downgrade();module.upgrade()
            conn.execute(sa.text("INSERT INTO bank_refund_confirmations (allocation_id,booking_id,created_by,created_at) VALUES (1,1,1,CURRENT_TIMESTAMP)"))
            with pytest.raises(RuntimeError,match='history'):module.downgrade()
