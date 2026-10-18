"""Explicit withdrawal keeps source money and old evidence intact."""
from unittest.mock import Mock
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from backend.extensions import db
from backend.models.accounting import Booking, BankTransaction, MemberClaim, FiscalYearStatus, FiscalYear, RevisionComment, Receipt, Account, AccountKind, ClaimStatus
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.bank_allocation_reversal import BankAllocationReversal
from backend.models.member import Member,Role
from backend.services.accounting import AccountingService,AccountingValidationError
from backend.services.accounting_revision import AccountingRevisionService
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.allocation_reversal import AllocationReversalService as Service
from tests.services.test_bank_booking_atomicity import case,rounding_account,book
from tests.services.test_payment_allocations import allocate
from tests.services.test_accounting_year_guards import csrf
from tests.conftest import auth_id


def reverse(case,version=1,reason='Synthetic wrong assignment'):
    return Service.reverse(case[3],db.session.get(Member,case[0]),expected_version=version,reason=reason)


def test_reverse_rounding_preserves_source_and_other_payments_then_reallocate(app,case):
    with app.app_context():
        rounding_account();book(case)
        tx=db.session.get(BankTransaction,case[3]);fy=Booking.query.first().fiscal_year
        claim=db.session.get(MemberClaim,case[2]);claim.paid_rappen+=300;db.session.commit()
        original_ids=[b.id for b in Booking.query.all()]
        reversal=reverse(case)
        assert tx.is_pending and tx.amount_rappen==2500 and tx.allocation_version==2
        assert claim.paid_rappen==300 and claim.status==ClaimStatus.TEILWEISE and claim.settled_at is None
        assert Booking.query.count()==2 and all(db.session.get(Booking,i).reversal_id==reversal.id for i in original_ids)
        state=PaymentAllocationService.summary(tx)
        assert (state['booked'],state['refund'],state['remaining'])==(0,0,2500)
        assert AccountingService.get_year_summary(fy.id)['income_rappen']==0
        assert AccountingService.get_journal(fy.id)==[]
        assert 'Synthetic payment' not in AccountingService.export_csv(fy.id)
        assert all(value==0 for value in AccountingService.get_saldo_timeline(fy.id)['values_rappen'])
        assert AccountingService.get_year_comparison()[-1]['income_rappen']==0
        allocate(case,version=2,amount=1700)
        allocate(case,version=3,amount=800,kind='refund',member_id=case[0])
        assert claim.paid_rappen==2000 and Booking.query.count()==3
        state=PaymentAllocationService.summary(tx)
        assert (state['booked'],state['refund'],state['remaining'])==(1700,800,0)
        assert len(state['rows'])==4 and len(state['active_rows'])==2
        assert BankAllocationReversal.query.count()==1


def test_refund_only_reservation_can_be_withdrawn_without_payment(app,case):
    with app.app_context():
        allocate(case,amount=2500,kind='refund',member_id=case[0])
        reverse(case)
        assert Booking.query.count()==0 and db.session.get(MemberClaim,case[2]).paid_rappen==0
        assert PaymentAllocationService.summary(db.session.get(BankTransaction,case[3]))['remaining']==2500


@pytest.mark.parametrize('mode',['stale','reason','review','closed','role','claim_mismatch','commit'])
def test_invalid_or_failed_withdrawal_preserves_all_rows(app,case,monkeypatch,mode):
    with app.app_context():
        row=allocate(case,amount=1000);claim=db.session.get(MemberClaim,case[2]);tx=db.session.get(BankTransaction,case[3])
        if mode in ('review','closed'):
            row.booking.fiscal_year.status=FiscalYearStatus.IN_REVIEW if mode=='review' else FiscalYearStatus.CLOSED
        if mode=='role':db.session.get(Member,case[0]).role=Role.MEMBER
        if mode=='claim_mismatch':claim.paid_rappen=900
        db.session.commit()
        with monkeypatch.context() as patch:
            if mode=='commit':patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):reverse(case,version=0 if mode=='stale' else 1,reason='' if mode=='reason' else 'Synthetic')
        assert BankAllocationReversal.query.count()==0 and tx.allocation_version==1
        assert row.reversal_id is None and row.booking.reversal_id is None
        assert claim.paid_rappen==(900 if mode=='claim_mismatch' else 1000)


def test_prior_review_snapshot_retained_and_repeat_rejected(app,case):
    with app.app_context():
        row=allocate(case,amount=1000);member=db.session.get(Member,case[0]);fy=row.booking.fiscal_year
        AccountingRevisionService.submit(fy.id,member,expected_version=0)
        prior=AccountingRevisionService.current(fy)
        AccountingRevisionService.withdraw(fy.id,member,expected_version=1,reason='Wrong assignment')
        reverse(case)
        with pytest.raises(AccountingValidationError):reverse(case)
        AccountingRevisionService.submit(fy.id,member,expected_version=1)
        assert prior.snapshot['bookings'][0]['amount_rappen']==1000
        assert AccountingRevisionService.current(fy).snapshot['bookings']==[]
        assert BankAllocationReversal.query.count()==1


def test_retained_comments_do_not_leak_from_other_year_and_receipts_remain(app,case):
    with app.app_context():
        row=allocate(case,amount=1000);fy=row.booking.fiscal_year
        other=FiscalYear.query.filter_by(year=2026).one()
        comment=RevisionComment(fiscal_year_id=other.id,author_id=case[0],text='Other year only')
        receipt=Receipt(booking_id=row.booking_id,drive_file_id='synthetic',drive_file_name='synthetic.pdf',
                        drive_folder_id='synthetic',uploader_id=case[0])
        db.session.add_all([comment,receipt]);db.session.commit()
        reverse(case)
        assert receipt.booking_id==row.booking_id and receipt.status_display=='Zuordnung zurückgenommen'
        assert AccountingService.get_comments_for_year(fy.id)==[]
        assert AccountingService.get_comments_for_year(other.id)==[comment]
        assert AccountingService.receipt_booking_choices_query(db.session.get(Member,case[0])).count()==0


def test_original_preview_post_history_and_csrf(app,client,case):
    with app.app_context():allocate(case,amount=1000)
    with client.session_transaction() as state:state['_user_id']=auth_id(client,case[0]);state['_fresh']=True
    url=f'/accounting/import/tx/{case[3]}/reverse'
    page=client.get(url);assert page.status_code==200 and 'Forderungszahlung' in page.text
    assert client.post(url,data={'version':1,'reason':'Synthetic'}).status_code in (400,403)
    data={'csrf_token':csrf(client,app),'version':1,'reason':'Synthetic correction'}
    assert client.post(url,data=data).status_code==302
    history=client.get(f'/accounting/import/tx/{case[3]}/allocations')
    assert 'Synthetic correction' in history.text and 'Zurückgenommen' in history.text
    assert client.post(url,data=data).status_code==400
    with app.app_context():assert BankAllocationReversal.query.count()==1


def test_reversal_migration_cycle_and_history_guard():
    spec=importlib.util.spec_from_file_location('reversal_migration',Path('migrations/versions/u202c120261018_allocation_reversals.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as conn:
        for table in ('bank_transactions','members','bookings','bank_payment_allocations'):
            conn.execute(sa.text(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)'))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade();module.downgrade();module.upgrade()
            conn.execute(sa.text("INSERT INTO bank_allocation_reversals (bank_transaction_id,version,reason,created_by,created_at) VALUES (1,1,'synthetic',1,CURRENT_TIMESTAMP)"))
            with pytest.raises(RuntimeError,match='history'):module.downgrade()
