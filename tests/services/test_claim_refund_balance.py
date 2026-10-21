"""Gross receipts, net debt and real outgoing evidence remain distinct."""
from datetime import date
from unittest.mock import Mock
import pytest
from backend.extensions import db
from backend.models.accounting import (Account, AccountKind, BankTransaction, BookingDirection,
    MemberClaim, ClaimStatus)
from backend.models.member import Member
from backend.models.billbro_correction import BillBroCorrection
from backend.models.claim_refund_payment import ClaimRefundPayment
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.allocation_reversal import AllocationReversalService
from tests.services.test_billbro_drafts import paid_round, final_round, round_data, seed, proposal, save, finances


def link_outflow(ids, amount):
    """Synthetic already-approved correction state; no approval endpoint in b1."""
    actor = db.session.get(Member, ids[0])
    claim = MemberClaim.query.filter_by(member_id=ids[0]).one()
    source = db.session.get(BankTransaction, ids[2])
    account = Account.query.filter_by(code='6710').first()
    if not account:
        account = Account(code='6710', name='Synthetic refunds', kind=AccountKind.EXPENSE)
        db.session.add(account); db.session.flush()
    outgoing = BankTransaction(import_id=source.import_id, line_key=f'synthetic-refund-{amount}',
        booked_date=date(2026,10,2), amount_rappen=amount, direction=BookingDirection.OUT, buchungstext='Synthetic')
    db.session.add(outgoing); db.session.commit()
    row = PaymentAllocationService.allocate(outgoing.id, expected_version=0, kind='booking', amount_rappen=amount,
        actor=actor, account_id=account.id, member_id=claim.member_id, event_id=claim.event_id, commit=False)
    db.session.add(ClaimRefundPayment(claim_id=claim.id, correction_id=BillBroCorrection.query.first().id, allocation=row))
    db.session.flush(); claim.sync_payment_status(); db.session.commit()
    return claim, outgoing


@pytest.mark.parametrize('returned', [0,200,600])
def test_partial_refund_later_increase_and_new_receipt(app, paid_round, returned):
    with app.app_context():
        claim = MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        claim.expected_rappen = 7800; claim.sync_payment_status(); db.session.commit()
        if returned: claim, _ = link_outflow(paid_round, returned)
        assert (claim.paid_rappen, claim.refunded_rappen, claim.net_paid_rappen) == (8400,returned,8400-returned)
        assert (claim.open_rappen, claim.refund_due_rappen) == (0,600-returned)
        claim.expected_rappen = 9000; claim.sync_payment_status(); db.session.commit()
        assert claim.open_rappen == 600+returned and claim.refund_due_rappen == 0
        assert claim.status == ClaimStatus.TEILWEISE and claim.settled_at is None
        overview = next(v for v in AccountingService.get_claims_overview() if v['member'].id == claim.member_id)
        assert overview['paid_rappen'] == 8400-returned and overview['open_rappen'] == 600+returned
        source = db.session.get(BankTransaction,paid_round[2])
        tx = BankTransaction(import_id=source.import_id, line_key='synthetic-additional-receipt',
            booked_date=date(2026,10,3), amount_rappen=600+returned, direction=BookingDirection.IN, buchungstext='Synthetic')
        db.session.add(tx); db.session.commit()
        PaymentAllocationService.allocate(tx.id, expected_version=0, kind='claim', amount_rappen=600+returned,
            actor=db.session.get(Member,paid_round[0]), claim_id=claim.id)
        assert (claim.paid_rappen, claim.net_paid_rappen, claim.open_rappen, claim.refund_due_rappen) == (9000+returned,9000,0,0)
        assert claim.status == ClaimStatus.BEGLICHEN
        assert source.amount_rappen == 8400


def test_zero_claim_and_full_refund_then_new_debt(app, paid_round):
    with app.app_context():
        claim = MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        claim.expected_rappen=0; claim.sync_payment_status(); db.session.commit()
        claim, outgoing = link_outflow(paid_round,8400)
        assert claim.net_paid_rappen == 0 and claim.status == ClaimStatus.BEGLICHEN
        claim.expected_rappen=9000; claim.sync_payment_status(); db.session.commit()
        assert claim.status == ClaimStatus.OFFEN and claim.open_rappen == 9000
        AllocationReversalService.reverse(outgoing.id, db.session.get(Member,paid_round[0]), expected_version=1, reason='Synthetic correction')
        assert claim.status == ClaimStatus.TEILWEISE and claim.open_rappen == 600
        assert claim.paid_rappen == 8400 and ClaimRefundPayment.query.count() == 1


def test_outgoing_reversal_required_before_incoming_reversal(app, paid_round):
    with app.app_context():
        claim = MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        claim.expected_rappen=7800; claim.sync_payment_status(); db.session.commit()
        claim, outgoing=link_outflow(paid_round,600)
        actor=db.session.get(Member,paid_round[0])
        with pytest.raises(AccountingValidationError, match='zuerst'):
            AllocationReversalService.reverse(paid_round[2], actor, expected_version=1, reason='Synthetic')
        assert claim.paid_rappen == 8400 and claim.refunded_rappen == 600
        AllocationReversalService.reverse(outgoing.id, actor, expected_version=1, reason='Synthetic outgoing')
        assert claim.refund_due_rappen == 600 and claim.refunded_rappen == 0
        AllocationReversalService.reverse(paid_round[2], actor, expected_version=1, reason='Synthetic incoming')
        assert claim.status == ClaimStatus.OFFEN and claim.open_rappen == 7800
        assert claim.paid_rappen == 0 and ClaimRefundPayment.query.count() == 1


def test_failed_outgoing_reversal_is_atomic(app, paid_round, monkeypatch):
    with app.app_context():
        claim, outgoing=link_outflow(paid_round,600)
        before=(claim.paid_rappen,claim.refunded_rappen,claim.status,claim.settled_at)
        with monkeypatch.context() as patch:
            patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):
                AllocationReversalService.reverse(outgoing.id,db.session.get(Member,paid_round[0]),expected_version=1,reason='Synthetic')
        assert (claim.paid_rappen,claim.refunded_rappen,claim.status,claim.settled_at) == before
        assert outgoing.allocation_version == 1
        assert ClaimRefundPayment.query.one().allocation.reversal_id is None


def test_refund_invalidates_draft_preview_and_net_is_shown(app,client,paid_round):
    token=proposal(client,paid_round)
    with app.app_context(): link_outflow(paid_round,600)
    before=finances(app,paid_round)
    assert save(client,paid_round,token).status_code == 400
    token=proposal(client,paid_round)
    assert save(client,paid_round,token).status_code == 302
    from backend.models.billbro_correction_draft import BillBroCorrectionDraft
    with app.app_context():
        row=next(r for r in BillBroCorrectionDraft.query.one().preview_json['rows'] if r['member_id']==paid_round[0])
        assert (row['paid'],row['refunded'],row['net'],row['open']) == (8400,600,7800,1200)
    assert finances(app,paid_round) == before


def test_draft_retains_absent_zero_claim_and_refund_identity(app,client,paid_round):
    from backend.models.event import Event
    from backend.models.participation import Participation
    from backend.models.billbro_correction_draft import BillBroCorrectionDraft
    with app.app_context():
        event=db.session.get(Event,paid_round[1])
        event.gesamtbetrag_rappen=16800; event.trinkgeld_rappen=6800
        part=Participation.query.filter_by(member_id=paid_round[0]).one()
        part.billbro_attendance=False; part.calculated_share_rappen=0
        claim=MemberClaim.query.filter_by(member_id=paid_round[0]).one()
        claim.expected_rappen=0; claim.sync_payment_status(); db.session.commit()
        original=claim.id
    before=finances(app,paid_round)
    token=proposal(client,paid_round,dict(invoice='100',total='180',paid_by='vereinskonto',reason='Synthetic follow-up'))
    assert save(client,paid_round,token).status_code==302
    assert finances(app,paid_round)==before
    with app.app_context():
        row=next(r for r in BillBroCorrectionDraft.query.one().preview_json['rows'] if r['member_id']==paid_round[0])
        assert row['after']==0 and row['refund']==8400
        assert db.session.get(MemberClaim,original).paid_rappen==8400


def test_bad_refund_member_cannot_reverse_financial_evidence(app,paid_round):
    with app.app_context():
        claim,outgoing=link_outflow(paid_round,600)
        row=ClaimRefundPayment.query.one().allocation
        row.member_id=Member.query.filter(Member.id!=paid_round[0]).first().id
        row.booking.member_id=row.member_id
        db.session.commit()
        with pytest.raises(AccountingValidationError,match='passt nicht'):
            AllocationReversalService.reverse(outgoing.id,db.session.get(Member,paid_round[0]),expected_version=1,reason='Synthetic')
        assert row.reversal_id is None and claim.refunded_rappen==600
