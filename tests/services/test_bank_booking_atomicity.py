"""A-060: no durable partial payment, including failures after ORM flush."""
from datetime import date
from unittest.mock import Mock

import pytest
from itsdangerous import URLSafeTimedSerializer

from backend.extensions import db
from backend.models.accounting import (Account, AccountKind, BankStatementImport, BankTransaction,
    Booking, BookingDirection, ClaimType, FiscalYear, MemberBankAlias, MemberClaim)
from backend.models.member import Member, Role
from backend.services.accounting import AccountingService
from backend.services.bank_import import BankImportService, BankImportError
from tests.conftest import auth_id


@pytest.fixture
def case(app):
    with app.app_context():
        member = Member(vorname='Synthetic', nachname='Importer', email='importer@example.com', role=Role.ADMIN)
        member.set_password('Synthetic-import-password1!')
        fy = FiscalYear(year=2026,start_date=date(2026,1,1),end_date=date(2026,12,31))
        account = Account(code='3400',name='Merch',kind=AccountKind.INCOME)
        db.session.add_all([member,fy,account]); db.session.flush()
        statement = BankStatementImport(fiscal_year_id=fy.id,filename='synthetic.csv',imported_by=member.id)
        claim = MemberClaim(member_id=member.id,claim_type=ClaimType.MERCH,expected_rappen=2000)
        db.session.add_all([statement,claim]); db.session.flush()
        tx = BankTransaction(import_id=statement.id,line_key='synthetic-payment',booked_date=date(2027,1,1),
            amount_rappen=2500,direction=BookingDirection.IN,buchungstext='Synthetic payment')
        db.session.add(tx); db.session.commit()
        return member.id, account.id, claim.id, tx.id, statement.id


def book(case):
    uid, account_id, claim_id, tx_id, _ = case
    return BankImportService.book_transaction(tx_id,account_id=account_id,claim_id=claim_id,
                                             booked_by=db.session.get(Member,uid), excess_action="rounding", learn_payer_alias=True)


def rounding_account():
    db.session.add(Account(code='3410',name='Synthetic rounding',kind=AccountKind.INCOME))
    db.session.commit()


def unchanged(case):
    assert Booking.query.count() == 0
    assert MemberBankAlias.query.count() == 0
    assert FiscalYear.query.filter_by(year=2027).count() == 0
    assert db.session.get(MemberClaim,case[2]).paid_rappen == 0
    tx = db.session.get(BankTransaction,case[3])
    assert tx.is_pending and tx.booking_id is None


def test_missing_second_account_retry_then_success_is_exactly_once(app,case):
    with app.app_context():
        for _ in range(2):
            with pytest.raises(BankImportError,match='Aufrundungs-Konto fehlt'):
                book(case)
            unchanged(case)
        rounding_account()
        result = book(case)
        assert result.id == db.session.get(BankTransaction,case[3]).booking_id
        assert sorted(b.amount_rappen for b in Booking.query.all()) == [500,2000]
        assert sum(b.amount_rappen for b in Booking.query.all()) == 2500
        assert db.session.get(MemberClaim,case[2]).paid_rappen == 2000
        with pytest.raises(BankImportError,match='bereits verarbeitet'):
            book(case)
        assert Booking.query.count() == 2
        assert db.session.get(MemberClaim,case[2]).paid_rappen == 2000
        with pytest.raises(BankImportError,match='verbuchte'):
            BankImportService.delete_import(case[4])


@pytest.mark.parametrize('stage',['second_flush','claim','alias','commit'])
def test_failure_at_each_stage_rolls_back_all_changes(app,case,monkeypatch,stage):
    with app.app_context():
        rounding_account()
        with monkeypatch.context() as patch:
            if stage=='second_flush':
                original = AccountingService.create_booking
                calls = []
                def fail_second(**kwargs):
                    result = original(**kwargs)
                    calls.append(result)
                    if len(calls)==2:
                        result.description=None
                        db.session.flush()  # Real NOT NULL failure after both inserts.
                    return result
                patch.setattr(AccountingService,'create_booking',fail_second)
            elif stage=='claim':
                def fail_claim(self,amount):
                    self.paid_rappen += amount
                    db.session.flush()
                    raise RuntimeError('synthetic claim failure')
                patch.setattr(MemberClaim,'register_payment',fail_claim)
            elif stage=='alias':
                patch.setattr(BankImportService,'extract_counterparty',lambda tx:'Synthetic payer')
                def fail_alias(uid,text):
                    db.session.add(MemberBankAlias(member_id=uid,alias_text=text))
                    db.session.flush()
                    raise RuntimeError('synthetic alias failure')
                patch.setattr(BankImportService,'learn_alias',fail_alias)
            else:
                patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic commit failure')))
            with pytest.raises(BankImportError,match='nicht bestätigt'):
                book(case)
        unchanged(case)
        book(case)
        assert Booking.query.count()==2


def test_repeated_original_post_does_not_leave_partial_bookings(app,client,case):
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]); state['_fresh']=True
        state['csrf_token']='synthetic-csrf'
    csrf=URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic-csrf')
    for _ in range(2):
        response=client.post(f'/accounting/import/tx/{case[3]}/book',
            data={'account_id':case[1],'claim_id':case[2],'csrf_token':csrf,'excess_action':'rounding'})
        assert response.status_code==302
        with app.app_context():
            unchanged(case)


def test_ignore_reopen_and_booked_guard(app,case):
    with app.app_context():
        BankImportService.ignore_transaction(case[3])
        with pytest.raises(BankImportError,match='bereits verarbeitet'):
            book(case)
        BankImportService.reopen_transaction(case[3])
        rounding_account(); book(case)
        with pytest.raises(BankImportError):
            BankImportService.ignore_transaction(case[3])
        with pytest.raises(BankImportError):
            BankImportService.reopen_transaction(case[3])
        assert Booking.query.count()==2
