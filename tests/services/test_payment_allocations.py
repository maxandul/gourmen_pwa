"""B01: one bank movement, explicit portions, visible remainder and replay safety."""
from unittest.mock import Mock
import pytest
from itsdangerous import URLSafeTimedSerializer
from backend.extensions import db
from backend.models.accounting import Account,AccountKind,BankTransaction,BankTransactionStatus,Booking,ClaimType,MemberClaim
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.member import Member
from backend.services.accounting import AccountingService,AccountingValidationError
from backend.services.bank_import import BankImportService,BankImportError
from backend.services.payment_allocations import PaymentAllocationService as Service
from tests.services.test_bank_booking_atomicity import case,rounding_account,unchanged
from tests.conftest import auth_id


def allocate(case,version=0,amount=1000,kind='claim',**extra):
    params=dict(expected_version=version,kind=kind,amount_rappen=amount,
                actor=db.session.get(Member,case[0]))
    if kind in ('claim','rounding'):
        params['claim_id']=case[2]
    params.update(extra)
    return Service.allocate(case[3],**params)


def test_multiple_members_and_refund_reservation_preserve_sum(app,case):
    with app.app_context():
        other=Member(vorname='Second',nachname='Synthetic',email='second@example.com')
        other.set_password('Synthetic-second-password!');db.session.add(other);db.session.flush()
        claim=MemberClaim(member_id=other.id,claim_type=ClaimType.MERCH,expected_rappen=400)
        db.session.add(claim);db.session.commit()
        allocate(case,amount=2000)
        allocate(case,version=1,amount=400,claim_id=claim.id)
        allocate(case,version=2,amount=100,kind='refund',member_id=case[0])
        tx=db.session.get(BankTransaction,case[3]);state=Service.summary(tx)
        assert (state['booked'],state['refund'],state['remaining'])==(2400,100,0)
        assert tx.amount_rappen==2500 and tx.is_pending and tx.allocation_version==3
        assert BankTransaction.query.count()==1 and Booking.query.count()==2
        assert {row.member_id for row in Booking.query.all()}=={case[0],other.id}
        assert all(row.fiscal_year.year==2027 for row in Booking.query.all())
        assert db.session.get(MemberClaim,case[2]).paid_rappen==2000 and claim.paid_rappen==400
        assert sum(row.amount_rappen for row in state['rows'])==tx.amount_rappen


def test_remaining_then_rounding_completes_same_movement(app,case):
    with app.app_context():
        rounding_account()
        allocate(case,amount=2000)
        tx=db.session.get(BankTransaction,case[3])
        assert Service.summary(tx)['remaining']==500 and tx.is_pending
        allocate(case,version=1,amount=500,kind='rounding')
        assert tx.status==BankTransactionStatus.BOOKED
        assert tx.booking_id and tx.allocation_version==2
        assert Service.summary(tx)['remaining']==0
        assert db.session.get(MemberClaim,case[2]).paid_rappen==2000


@pytest.mark.parametrize('params',[{'expected_version':1},{'expected_version':None}, {'amount_rappen':2501},
    {'amount_rappen':2001},{'amount_rappen':True},{'kind':'unknown'},{'claim_id':99999}])
def test_invalid_initial_request_changes_nothing(app,case,params):
    with app.app_context():
        base=dict(expected_version=0,kind='claim',amount_rappen=1000,claim_id=case[2],actor=db.session.get(Member,case[0]))
        base.update(params)
        with pytest.raises(AccountingValidationError):
            Service.allocate(case[3],**base)
        unchanged(case)
        assert BankPaymentAllocation.query.count()==0
        assert db.session.get(BankTransaction,case[3]).allocation_version==0


def test_stale_version_and_legacy_full_booking_cannot_repeat_partial(app,case):
    with app.app_context():
        allocate(case)
        with pytest.raises(BankImportError,match='Stand geändert|stand geändert'):
            allocate(case)
        with pytest.raises(BankImportError,match='teilweise'):
            BankImportService.book_transaction(case[3],account_id=case[1],claim_id=case[2],
                booked_by=db.session.get(Member,case[0]),excess_action='rounding')
        assert Booking.query.count()==1 and db.session.get(MemberClaim,case[2]).paid_rappen==1000


def test_partial_cannot_be_ignored_deleted_or_freely_edited(app,case):
    with app.app_context():
        row=allocate(case)
        with pytest.raises(AccountingValidationError,match='Importzuordnung'):
            AccountingService.update_booking(row.booking_id,amount_rappen=1)
        with pytest.raises(BankImportError):
            BankImportService.ignore_transaction(case[3])
        with pytest.raises(BankImportError):
            BankImportService.delete_import(case[4])
        assert Booking.query.one().amount_rappen==1000


def test_commit_failure_rolls_back_allocation_booking_claim_and_version(app,case,monkeypatch):
    with app.app_context():
        with monkeypatch.context() as patch:
            patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(BankImportError,match='nicht bestätigt'):
                allocate(case)
        unchanged(case)
        assert BankPaymentAllocation.query.count()==0
        assert db.session.get(BankTransaction,case[3]).allocation_version==0
        allocate(case)
        assert Booking.query.count()==1


def test_full_legacy_entry_now_records_allocation_evidence(app,case):
    with app.app_context():
        rounding_account()
        BankImportService.book_transaction(case[3],account_id=case[1],claim_id=case[2],
            booked_by=db.session.get(Member,case[0]),excess_action='rounding')
        tx=db.session.get(BankTransaction,case[3]);state=Service.summary(tx)
        assert len(state['rows'])==2 and state['booked']==2500 and state['remaining']==0
        assert tx.allocation_version==1 and not state['legacy']


def test_existing_unjournaled_partial_is_not_silently_reused(app,case):
    from datetime import date
    with app.app_context():
        AccountingService.create_booking(1,date(2026,1,1),'Historic synthetic',100,'in',case[1],None,None,
            db.session.get(Member,case[0]),payment_ref='synthetic-payment')
        with pytest.raises(BankImportError,match='Historische Buchung'):
            allocate(case)
        assert Booking.query.count()==1 and BankPaymentAllocation.query.count()==0


def test_original_route_replay_and_visible_remainder(app,client,case):
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True;state['csrf_token']='synthetic'
    csrf=URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic')
    payload=dict(version='0',kind='claim',amount_chf='10.00',claim_id=case[2],csrf_token=csrf)
    assert client.post(f'/accounting/import/tx/{case[3]}/allocate',data=payload).status_code==302
    assert client.post(f'/accounting/import/tx/{case[3]}/allocate',data=payload).status_code==400
    page=client.get(f'/accounting/import/tx/{case[3]}/allocations')
    assert page.status_code==200 and '15.00' in page.text and 'Noch nicht zugeordnet' in page.text
    with app.app_context():
        assert Booking.query.count()==1 and BankPaymentAllocation.query.count()==1


def test_allocation_route_requires_csrf(app,client,case):
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True
    assert client.post(f'/accounting/import/tx/{case[3]}/allocate',data={}).status_code==403
    with app.app_context():
        unchanged(case)


@pytest.mark.parametrize('scope,expected',[('accounting_read',403),('accounting_write',302)])
def test_scope_boundaries_for_allocation(app,client,case,scope,expected):
    from backend.models.member import Role
    from backend.models.member_area_grant import MemberAreaGrant
    with app.app_context():
        actor=db.session.get(Member,case[0]);actor.role=Role.MEMBER
        db.session.add(MemberAreaGrant(member_id=actor.id,scope=scope,granted_by=actor.id));db.session.commit()
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True;state['csrf_token']='synthetic'
    assert client.get(f'/accounting/import/tx/{case[3]}/allocations').status_code==200
    csrf=URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic')
    response=client.post(f'/accounting/import/tx/{case[3]}/allocate',data=dict(version='0',kind='claim',amount_chf='10',claim_id=case[2],csrf_token=csrf))
    assert response.status_code==expected


def test_invalid_form_preserves_amount(app,client,case):
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True;state['csrf_token']='synthetic'
    csrf=URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic')
    response=client.post(f'/accounting/import/tx/{case[3]}/allocate',data=dict(version='0',kind='claim',amount_chf='10.999',claim_id=case[2],csrf_token=csrf))
    assert response.status_code==400 and 'value="10.999"' in response.text
    with app.app_context():
        unchanged(case)


def test_allocation_journal_flush_failure_rolls_back_money(app,case,monkeypatch):
    with app.app_context():
        original=Service.record
        def fail(*args,**kwargs):
            row=original(*args,**kwargs);row.kind='invalid';db.session.flush()
            return row
        with monkeypatch.context() as patch:
            patch.setattr(Service,'record',fail)
            with pytest.raises(BankImportError,match='nicht bestätigt'):
                allocate(case)
        unchanged(case)
        assert BankPaymentAllocation.query.count()==0
        assert db.session.get(BankTransaction,case[3]).allocation_version==0


def test_outgoing_split_allows_expense_but_not_claim_or_refund(app,case):
    from backend.models.accounting import BookingDirection
    with app.app_context():
        tx=db.session.get(BankTransaction,case[3]);tx.direction=BookingDirection.OUT
        db.session.get(Account,case[1]).kind=AccountKind.EXPENSE;db.session.commit()
        for kind in ['claim','refund']:
            with pytest.raises(BankImportError):
                allocate(case,kind=kind)
        allocate(case,kind='booking',account_id=case[1])
        allocate(case,version=1,amount=1500,kind='booking',account_id=case[1])
        assert tx.status==BankTransactionStatus.BOOKED
        assert sum(row.amount_rappen for row in Booking.query.all())==2500
        assert db.session.get(MemberClaim,case[2]).paid_rappen==0
