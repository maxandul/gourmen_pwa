"""Single-claim direction, ownership and explicit excess disposition."""
import pytest

from backend.extensions import db
from backend.models.accounting import Account, AccountKind, BankTransaction, Booking, BookingDirection, MemberBankAlias, MemberClaim
from backend.models.member import Member
from backend.services.bank_import import BankImportService, BankImportError
from tests.services.test_bank_booking_atomicity import case, rounding_account, unchanged


def assign(case, **overrides):
    data = dict(account_id=case[1], claim_id=case[2],booked_by=db.session.get(Member,case[0]))
    data.update(overrides)
    return BankImportService.book_transaction(case[3],**data)


@pytest.mark.parametrize('choice',[None,'','defer','unknown'])
def test_excess_without_explicit_rounding_stays_pending(app,case,choice):
    with app.app_context():
        rounding_account()
        with pytest.raises(BankImportError):
            assign(case,excess_action=choice)
        unchanged(case)


def test_explicit_rounding_records_only_allocated_claim_amount(app,case):
    with app.app_context():
        rounding_account()
        assign(case,excess_action='rounding')
        assert sorted(row.amount_rappen for row in Booking.query.all()) == [500,2000]
        assert db.session.get(MemberClaim,case[2]).paid_rappen == 2000
        assert MemberBankAlias.query.count()==0


@pytest.mark.parametrize('change',['outgoing','member','account','inactive_account','kind'])
def test_inconsistent_assignment_rejected_without_mutation(app,case,change):
    with app.app_context():
        options=dict(excess_action='rounding')
        account=db.session.get(Account,case[1])
        if change=='outgoing':
            db.session.get(BankTransaction,case[3]).direction=BookingDirection.OUT
            account.kind=AccountKind.EXPENSE  # Pass direction/account guard, then reject claim.
        elif change=='member':
            other=Member(vorname='Other',nachname='Synthetic',email='other@example.com')
            other.set_password('Synthetic-other-password!'); db.session.add(other);db.session.flush()
            options['member_id']=other.id
        elif change=='account':
            account.code='3000'
        elif change=='inactive_account':
            account.is_active=False
        else:
            account.kind=AccountKind.EXPENSE
        db.session.commit()
        with pytest.raises(BankImportError):
            assign(case,**options)
        unchanged(case)


@pytest.mark.parametrize('amount',[500,2000])
def test_partial_and_exact_payment_need_no_rounding_choice(app,case,amount):
    with app.app_context():
        db.session.get(BankTransaction,case[3]).amount_rappen=amount;db.session.commit()
        assign(case)
        assert Booking.query.one().amount_rappen==amount
        assert db.session.get(MemberClaim,case[2]).paid_rappen==amount


def test_third_party_payment_does_not_learn_debtor_alias(app,case,monkeypatch):
    with app.app_context():
        db.session.get(BankTransaction,case[3]).amount_rappen=2000;db.session.commit()
        monkeypatch.setattr(BankImportService,'extract_counterparty',lambda tx:'Another synthetic payer')
        assign(case)
        assert Booking.query.one().member_id==case[0]
        assert MemberBankAlias.query.count()==0


def test_alias_requires_explicit_confirmation(app,case,monkeypatch):
    with app.app_context():
        db.session.get(BankTransaction,case[3]).amount_rappen=2000;db.session.commit()
        monkeypatch.setattr(BankImportService,'extract_counterparty',lambda tx:'Verified synthetic payer')
        assign(case,learn_payer_alias=True)
        assert MemberBankAlias.query.one().member_id==case[0]


def test_existing_unrelated_event_is_rejected(app,case):
    from datetime import datetime
    from backend.models.event import Event, EventType
    with app.app_context():
        event=Event(datum=datetime(2026,6,1),organisator_id=case[0],event_typ=EventType.MONATSESSEN,season=2026)
        db.session.add(event);db.session.commit()
        with pytest.raises(BankImportError,match='Event passt nicht'):
            assign(case,event_id=event.id,excess_action='rounding')
        unchanged(case)


def test_form_requires_explicit_choice_and_does_not_preselect_rounding(app,client,case):
    from itsdangerous import URLSafeTimedSerializer
    from tests.conftest import auth_id
    with app.app_context():
        rounding_account()
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,case[0]);state['_fresh']=True;state['csrf_token']='synthetic'
    page=client.get(f'/accounting/import/{case[4]}/review')
    assert page.status_code==200
    assert '<option value="rounding">' in page.text
    assert 'automatisch auf dem Aufrundungs-Konto' not in page.text
    csrf=URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('synthetic')
    payload=dict(account_id=case[1],claim_id=case[2],csrf_token=csrf)
    assert client.post(f'/accounting/import/tx/{case[3]}/book',data=payload).status_code==302
    with app.app_context():
        unchanged(case)
    payload['excess_action']='rounding'
    assert client.post(f'/accounting/import/tx/{case[3]}/book',data=payload).status_code==302
    with app.app_context():
        assert Booking.query.count()==2
        assert db.session.get(MemberClaim,case[2]).paid_rappen==2000
