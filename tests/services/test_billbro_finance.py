"""Financial approval and real bank refunds preserve the original identities."""
import re
from datetime import date
from unittest.mock import Mock
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.event import Event, EventAudience
from backend.models.accounting import (MemberClaim, Account, AccountKind, BankTransaction,
    BookingDirection, FiscalYear, FiscalYearStatus, ClaimStatus, Booking)
from backend.models.billbro_correction import BillBroCorrection
from backend.models.billbro_correction_draft import BillBroCorrectionDraft as Draft
from backend.models.claim_refund_payment import ClaimRefundPayment
from backend.services.billbro_finance import BillBroFinanceService
from backend.services.claim_refunds import ClaimRefundService
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.allocation_reversal import AllocationReversalService
from backend.services.payment_allocations import PaymentAllocationService
from tests.services.test_billbro_drafts import paid_round, final_round, round_data, seed, proposal, save, form, finances
from tests.services.test_accounting_year_guards import csrf
from tests.conftest import auth_id


def draft(app,client,ids,total='234',**updates):
    assert save(client,ids,proposal(client,ids,form(total,**updates))).status_code==302
    with app.app_context(): return Draft.query.order_by(Draft.id.desc()).first().id


def url(ids,did): return f'/billbro/{ids[1]}/correction-drafts/{did}/approve'


def preview(client,ids,did):
    response=client.get(url(ids,did))
    assert response.status_code==200,response.text
    return re.search(r'name="approval_token" value="([^"]+)"',response.text).group(1)


def approve(client,ids,did,token):
    return client.post(url(ids,did),data={'action':'approve','approval_token':token})


def outgoing(ids,amount=600,year=2027):
    account=Account.query.filter_by(code='6710').first()
    if not account:
        db.session.add(Account(code='6710',name='Synthetic refunds',kind=AccountKind.EXPENSE))
    source=db.session.get(BankTransaction,ids[2])
    tx=BankTransaction(import_id=source.import_id,line_key=f'synthetic-out-{BankTransaction.query.count()}',
        booked_date=date(year,1,2),amount_rappen=amount,direction=BookingDirection.OUT,buchungstext='Synthetic refund')
    db.session.add(tx); db.session.commit(); return tx


@pytest.mark.parametrize('total,expected,open_amount,refund',[('234',7800,0,600),('270',9000,600,0)])
def test_finance_preview_approval_and_retry_keep_claim_ids_and_bank_rows(app,client,paid_round,total,expected,open_amount,refund):
    did=draft(app,client,paid_round,total)
    before=finances(app,paid_round)
    with app.app_context():
        ids=[c.id for c in MemberClaim.query.order_by(MemberClaim.id)]
        engine=db.engine
    writes=[]
    def capture(conn,cursor,sql,*args):
        if sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')): writes.append(sql)
    sa_event.listen(engine,'before_cursor_execute',capture)
    try: token=preview(client,paid_round,did)
    finally: sa_event.remove(engine,'before_cursor_execute',capture)
    assert not writes and finances(app,paid_round)==before
    assert approve(client,paid_round,did,token).status_code==302
    assert approve(client,paid_round,did,token).status_code==302
    assert finances(app,paid_round)[1]==before[1]
    with app.app_context():
        assert [c.id for c in MemberClaim.query.order_by(MemberClaim.id)]==ids
        claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        assert (claim.expected_rappen,claim.paid_rappen,claim.open_rappen,claim.refund_due_rappen)==(expected,8400,open_amount,refund)
        assert Draft.query.one().status=='applied' and BillBroCorrection.query.count()==2
        assert BillBroCorrection.query.order_by(BillBroCorrection.id.desc()).first().after_json['finance_approval']['draft_id']==did
    assert client.get(f'/billbro/{paid_round[1]}/correction-balances').status_code==200


def test_full_refund_cross_year_reverse_and_second_correction(app,client,paid_round):
    did=draft(app,client,paid_round)
    assert approve(client,paid_round,did,preview(client,paid_round,did)).status_code==302
    with app.app_context():
        actor=db.session.get(Member,paid_round[0]); claim=MemberClaim.query.filter_by(member_id=actor.id).one()
        cid=BillBroCorrection.query.order_by(BillBroCorrection.id.desc()).first().id
        original_year=FiscalYear.query.filter_by(year=2026).one()
        original_year.status=FiscalYearStatus.CLOSED; db.session.commit()
        tx=outgoing(paid_round)
        first=ClaimRefundService.allocate(tx.id,claim.id,cid,actor,expected_version=0,amount_rappen=400)
        assert claim.refund_due_rappen==200 and claim.paid_rappen==8400 and claim.refunded_rappen==400
        assert first.allocation.booking.account.code=='6710' and first.allocation.booking.fiscal_year.year==2027
        assert original_year.status==FiscalYearStatus.CLOSED
        ClaimRefundService.allocate(tx.id,claim.id,cid,actor,expected_version=1,amount_rappen=200)
        assert claim.refund_due_rappen==0 and ClaimRefundService.available(actor)==[]
        another=outgoing(paid_round,amount=1)
        with pytest.raises(AccountingValidationError):
            ClaimRefundService.allocate(another.id,claim.id,cid,actor,expected_version=0,amount_rappen=1)
        assert AccountingService.get_year_summary(first.allocation.booking.fiscal_year_id)['expense_rappen']==600
        assert AccountingService.get_year_summary(original_year.id)['income_rappen']==8400
        with pytest.raises(AccountingValidationError):
            ClaimRefundService.allocate(tx.id,claim.id,cid,actor,expected_version=1,amount_rappen=200)
        original_year.status=FiscalYearStatus.OPEN; db.session.commit()
        tx_id=tx.id
    second=draft(app,client,paid_round,'270')
    assert approve(client,paid_round,second,preview(client,paid_round,second)).status_code==302
    with app.app_context():
        claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        assert claim.open_rappen==1200 and claim.paid_rappen==8400 and claim.refunded_rappen==600
        AllocationReversalService.reverse(tx_id,db.session.get(Member,paid_round[0]),expected_version=2,reason='Synthetic correction')
        assert claim.open_rappen==600 and claim.refunded_rappen==0 and ClaimRefundPayment.query.count()==2
        assert claim.status==ClaimStatus.TEILWEISE


@pytest.mark.parametrize('kind',['history','commit'])
def test_approval_failure_rolls_back_and_retry_succeeds(app,client,paid_round,monkeypatch,kind):
    did=draft(app,client,paid_round); token=preview(client,paid_round,did); before=finances(app,paid_round)
    def fail(*args): raise OperationalError('synthetic',{},Exception('synthetic'))
    if kind=='history': sa_event.listen(BillBroCorrection,'before_insert',fail)
    try:
        with monkeypatch.context() as patch:
            if kind=='commit': patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            assert approve(client,paid_round,did,token).status_code==400
    finally:
        if kind=='history': sa_event.remove(BillBroCorrection,'before_insert',fail)
    assert finances(app,paid_round)==before
    with app.app_context(): assert db.session.get(Draft,did).status=='pending'
    assert approve(client,paid_round,did,token).status_code==302


@pytest.mark.parametrize('kind',['organizer','reviewer','treasurer','hidden'])
def test_financial_role_and_event_visibility(app,client,paid_round,kind):
    did=draft(app,client,paid_round)
    with app.app_context():
        actor=Member.query.filter(Member.id!=paid_round[0]).first(); mid=actor.id
        if kind=='organizer': db.session.get(Event,paid_round[1]).organisator_id=mid
        if kind=='reviewer': actor.funktion=Funktion.RECHNUNGSPRUEFER
        if kind in ('treasurer','hidden'): actor.funktion=Funktion.SCHATZMEISTER
        if kind=='hidden': db.session.get(Event,paid_round[1]).audience=EventAudience.BOARD
        db.session.commit()
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,mid); state['_fresh']=True
    assert client.get(url(paid_round,did)).status_code==(200 if kind=='treasurer' else 403)
    if kind!='treasurer': assert client.post(url(paid_round,did),data={'action':'approve'}).status_code==403


@pytest.mark.parametrize('kind',['closed','legacy','reversed','withdrawn','tamper','expired','generation'])
def test_finance_rejects_stale_unproven_or_invalid_approval(app,client,paid_round,monkeypatch,kind):
    if kind=='legacy':
        with app.app_context():
            claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one(); claim.paid_rappen+=1; db.session.commit()
    did=draft(app,client,paid_round)
    if kind=='legacy':
        assert client.get(url(paid_round,did)).status_code==400
        return
    token=preview(client,paid_round,did)
    with app.app_context():
        if kind=='closed': FiscalYear.query.one().status=FiscalYearStatus.CLOSED
        if kind=='withdrawn': db.session.get(Draft,did).status='withdrawn'
        if kind=='generation': db.session.get(Member,paid_round[0]).rotate_auth_generation()
        db.session.commit()
        if kind=='reversed': AllocationReversalService.reverse(paid_round[2],db.session.get(Member,paid_round[0]),expected_version=1,reason='Synthetic')
    if kind=='generation':
        with client.session_transaction() as state: state['_user_id']=auth_id(client,paid_round[0]); state['_fresh']=True
    if kind=='tamper': token+='invalid'
    if kind=='expired':
        from itsdangerous.timed import TimestampSigner
        original=TimestampSigner.get_timestamp
        monkeypatch.setattr(TimestampSigner,'get_timestamp',lambda self: original(self)+1900)
    before=finances(app,paid_round)
    assert approve(client,paid_round,did,token).status_code==400
    assert finances(app,paid_round)==before


def test_finance_return_requires_reason_and_keeps_original(app,client,paid_round):
    did=draft(app,client,paid_round); before=finances(app,paid_round)
    assert client.post(url(paid_round,did),data={'action':'return','reason':''}).status_code==400
    assert client.post(url(paid_round,did),data={'action':'return','reason':'Synthetic clarification needed'}).status_code==302
    assert finances(app,paid_round)==before
    with app.app_context(): assert 'Synthetic clarification needed' in db.session.get(Draft,did).status_reason


def test_refund_original_route_and_csrf(app,client,paid_round):
    did=draft(app,client,paid_round)
    assert approve(client,paid_round,did,preview(client,paid_round,did)).status_code==302
    with app.app_context():
        claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one(); cid=claim.id
        correction=BillBroCorrection.query.order_by(BillBroCorrection.id.desc()).first().id
        txid=outgoing(paid_round).id
    route=f'/accounting/import/tx/{txid}/claim-refund-payment'
    assert client.post(route,data={'source':f'{cid}:{correction}','amount_chf':'6','version':0}).status_code in (400,403)
    values={'source':f'{cid}:{correction}','amount_chf':'7','version':0,'csrf_token':csrf(client,app)}
    response=client.post(route,data=values)
    assert response.status_code==400 and 'value="7"' in response.text
    values['amount_chf']='6'
    assert client.post(route,data=values).status_code==302
    response=client.get(f'/accounting/import/tx/{txid}/allocations')
    assert response.status_code==200 and 'Finanzkorrektur' in response.text


@pytest.mark.parametrize('kind',['excess','bank_excess','closed','earlier','incoming','role','hidden','stale_version','stale_correction','inactive','insert','commit'])
def test_invalid_refund_never_partially_books(app,client,paid_round,monkeypatch,kind):
    did=draft(app,client,paid_round)
    assert approve(client,paid_round,did,preview(client,paid_round,did)).status_code==302
    with app.app_context():
        claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        cid=BillBroCorrection.query.order_by(BillBroCorrection.id.desc()).first().id
        actor=db.session.get(Member,paid_round[0]); tx=outgoing(paid_round)
        if kind=='bank_excess': tx.amount_rappen=300
        if kind=='closed': AccountingService.get_or_create_fiscal_year(2027).status=FiscalYearStatus.CLOSED
        if kind=='earlier': tx.booked_date=date(2026,9,1)
        if kind=='incoming': tx.direction=BookingDirection.IN
        if kind=='role': actor.role=Role.MEMBER
        if kind=='hidden':
            actor.role=Role.MEMBER; actor.funktion=Funktion.SCHATZMEISTER
            claim.event.audience=EventAudience.BOARD
            claim.event.organisator_id=Member.query.filter(Member.id!=actor.id).first().id
        if kind=='inactive': Account.query.filter_by(code='6710').one().is_active=False
        db.session.commit()
        txid,claimid=tx.id,claim.id
    before=finances(app,paid_round)
    def fail(*args): raise OperationalError('synthetic',{},Exception('synthetic'))
    if kind=='insert': sa_event.listen(ClaimRefundPayment,'before_insert',fail)
    try:
        with app.app_context(),monkeypatch.context() as patch:
            if kind=='commit': patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):
                ClaimRefundService.allocate(txid,claimid,cid-1 if kind=='stale_correction' else cid,
                    db.session.get(Member,paid_round[0]),expected_version=1 if kind=='stale_version' else 0,
                    amount_rappen=601 if kind=='excess' else 600)
    finally:
        if kind=='insert': sa_event.remove(ClaimRefundPayment,'before_insert',fail)
    assert finances(app,paid_round)==before
    with app.app_context(): assert ClaimRefundPayment.query.count()==0


def test_paid_attendance_change_preserves_old_claim_and_creates_new_claim_atomically(app,client,paid_round):
    from tests.services.test_billbro_attendance import new_member
    from tests.services.test_billbro_invoice_correction import seed_guesses
    from backend.models.participation import Participation,Esstyp
    mid=new_member(app); seed_guesses(app,paid_round)
    with app.app_context():
        part=Participation.query.filter_by(member_id=paid_round[0]).one(); pid=part.id
        claimid=MemberClaim.query.filter_by(member_id=paid_round[0]).one().id
    did=draft(app,client,paid_round,'270',invoice='105',**{f'attendance_{pid}':'absent',f'attendance_{-mid}':'present',f'esstyp_{-mid}':'NORMAL'})
    assert approve(client,paid_round,did,preview(client,paid_round,did)).status_code==302
    with app.app_context():
        old=db.session.get(MemberClaim,claimid)
        assert old.expected_rappen==0 and old.paid_rappen==8400 and old.refund_due_rappen==8400
        new=MemberClaim.query.filter_by(member_id=mid).one()
        assert new.id!=claimid and new.expected_rappen==9000 and new.paid_rappen==0
        part=db.session.get(Participation,pid)
        assert part.teilnahme is True and not part.billbro_attending and part.esstyp==Esstyp.NORMAL
        assert part.points is None and part.guess_bill_amount_rappen==10000
        added=Participation.query.filter_by(member_id=mid).one()
        assert added.teilnahme is None and added.billbro_attending
        assert sum(c.expected_rappen for c in MemberClaim.query.all())==27000
    # A subsequent draft must accept the preserved zero-valued claim.
    assert draft(app,client,paid_round,'273')


def test_new_draft_cancels_old_approval_and_csrf(app,client,paid_round):
    first=draft(app,client,paid_round); token=preview(client,paid_round,first)
    draft(app,client,paid_round,'237')
    before=finances(app,paid_round)
    assert approve(client,paid_round,first,token).status_code==400
    app.config['WTF_CSRF_ENABLED']=True
    assert client.post(url(paid_round,first),data={'action':'return','reason':'Synthetic'}).status_code==400
    assert finances(app,paid_round)==before


def test_member_sees_only_own_balance_without_bank_workplace_links(app,client,paid_round):
    did=draft(app,client,paid_round)
    assert approve(client,paid_round,did,preview(client,paid_round,did)).status_code==302
    with app.app_context():
        actor=db.session.get(Member,paid_round[0]); actor.role=Role.MEMBER
        other=Member.query.filter(Member.id!=actor.id).first()
        other.vorname='HiddenOtherBalance'; other.nachname='Synthetic'
        db.session.get(Event,paid_round[1]).organisator_id=other.id
        db.session.commit()
    response=client.get(f'/billbro/{paid_round[1]}/correction-balances')
    assert response.status_code==200 and '6.00 CHF' in response.text
    assert 'HiddenOtherBalance' not in response.text and '/accounting/import/tx/' not in response.text
    response=client.get(f'/events/{paid_round[1]}?tab=billbro')
    assert response.status_code==200 and 'Meinen Zahlungs-' in response.text


def test_finance_token_cannot_be_reused_by_another_financial_actor(app,client,paid_round):
    did=draft(app,client,paid_round); token=preview(client,paid_round,did)
    with app.app_context():
        other=Member.query.filter(Member.id!=paid_round[0]).first()
        other.role=Role.ADMIN; mid=other.id; db.session.commit()
    with client.session_transaction() as state:
        state['_user_id']=auth_id(client,mid); state['_fresh']=True
    before=finances(app,paid_round)
    assert approve(client,paid_round,did,token).status_code==400
    assert finances(app,paid_round)==before
