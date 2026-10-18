"""Paid proposals never change the effective settlement or bank evidence."""
import re
from datetime import date
from unittest.mock import Mock
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.accounting import (Account, AccountKind, BankStatementImport, BankTransaction,
    Booking, BookingDirection, FiscalYear, FiscalYearStatus, MemberClaim, ClaimStatus)
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.billbro_correction_draft import BillBroCorrectionDraft as Draft
from backend.models.member import Member, Funktion
from backend.models.event import Event, EventAudience
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.allocation_reversal import AllocationReversalService
from backend.services.billbro_correction import record
from tests.services.test_billbro_correction import final_round, preview, confirm
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot
from tests.conftest import auth_id


@pytest.fixture
def paid_round(app, client, final_round):
    token = preview(client, final_round, dict(total='252', paid_by='vereinskonto', reason='Synthetic 84 each'))
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        fy = FiscalYear(year=2026, start_date=date(2026,1,1), end_date=date(2026,12,31))
        account = Account(code='3310', name='Synthetic food', kind=AccountKind.INCOME)
        db.session.add_all([fy, account]); db.session.flush()
        statement = BankStatementImport(fiscal_year_id=fy.id, filename='synthetic.csv', imported_by=final_round[0])
        db.session.add(statement); db.session.flush()
        tx = BankTransaction(import_id=statement.id, line_key='synthetic-food-payment', booked_date=date(2026,10,1),
            amount_rappen=8400, direction=BookingDirection.IN, buchungstext='Synthetic')
        db.session.add(tx); db.session.commit()
        claim = MemberClaim.query.order_by(MemberClaim.member_id).first()
        PaymentAllocationService.allocate(tx.id, expected_version=0, kind='claim', amount_rappen=8400,
            actor=db.session.get(Member, final_round[0]), claim_id=claim.id)
        return final_round[0], final_round[1], tx.id


def url(ids): return f'/billbro/{ids[1]}/correction-drafts'


def form(total='270', **updates):
    result = dict(invoice='100', total=total, paid_by='vereinskonto', reason='Synthetic paid correction')
    result.update(updates)
    return result


def proposal(client, ids, values=None):
    response = client.post(url(ids), data=values or form())
    assert response.status_code == 200, response.text
    return re.search(r'name="preview_token" value="([^"]+)"', response.text).group(1)


def save(client, ids, token):
    return client.post(url(ids), data={'action':'save', 'preview_token':token})


def finances(app, ids):
    with app.app_context():
        evidence = {model.__tablename__: [record(r) for r in model.query.order_by(model.id)]
                    for model in (BankTransaction, Booking, BankPaymentAllocation)}
    return snapshot(app, ids[1]), evidence


@pytest.mark.parametrize('total,expected_open,expected_refund', [('270',600,0), ('234',0,600)])
def test_preview_save_and_retry_preserve_real_payment_evidence(app, client, paid_round, total, expected_open, expected_refund):
    before = finances(app, paid_round)
    with app.app_context(): engine = db.engine
    writes = []
    def record_sql(conn, cursor, sql, *args):
        if sql.lstrip().upper().startswith(('INSERT','UPDATE','DELETE')): writes.append(sql)
    sa_event.listen(engine, 'before_cursor_execute', record_sql)
    try:
        assert client.get(url(paid_round)).status_code == 200
        token = proposal(client, paid_round, form(total))
    finally:
        sa_event.remove(engine, 'before_cursor_execute', record_sql)
    assert not writes
    assert save(client, paid_round, token).status_code == 302
    assert save(client, paid_round, token).status_code == 302
    assert finances(app, paid_round) == before
    with app.app_context():
        draft = Draft.query.one()
        row = next(r for r in draft.preview_json['rows'] if r['member_id'] == paid_round[0])
        assert (row['paid'], row['open'], row['refund']) == (8400, expected_open, expected_refund)
        assert draft.status == 'pending'
    response = client.get(url(paid_round))
    assert response.status_code == 200 and 'noch nicht finanziell bestÃ¤tigt' in response.text


def test_stale_payment_reversal_rejects_preview_and_marks_saved_draft_stale(app, client, paid_round):
    first = proposal(client, paid_round)
    assert save(client, paid_round, first).status_code == 302
    token = proposal(client, paid_round, form('273'))
    with app.app_context():
        tx = db.session.get(BankTransaction, paid_round[2])
        AllocationReversalService.reverse(tx.id, db.session.get(Member,paid_round[0]), expected_version=tx.allocation_version, reason='Synthetic reversal')
    before = finances(app, paid_round)
    assert save(client, paid_round, token).status_code == 400
    assert finances(app, paid_round) == before
    assert 'Ausgangsstand inzwischen geÃ¤ndert' in client.get(url(paid_round)).text


@pytest.mark.parametrize('failure', ['insert','commit'])
def test_failed_draft_save_rolls_back_superseding_and_can_retry(app, client, paid_round, monkeypatch, failure):
    assert save(client, paid_round, proposal(client, paid_round)).status_code == 302
    token = proposal(client, paid_round, form('273'))
    before = finances(app, paid_round)
    def fail(*args): raise OperationalError('synthetic', {}, Exception('synthetic'))
    if failure == 'insert': sa_event.listen(Draft, 'before_insert', fail)
    try:
        with monkeypatch.context() as patch:
            if failure == 'commit': patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
            assert save(client, paid_round, token).status_code == 400
    finally:
        if failure == 'insert': sa_event.remove(Draft, 'before_insert', fail)
    assert finances(app, paid_round) == before
    with app.app_context(): assert Draft.query.one().status == 'pending'
    assert save(client, paid_round, token).status_code == 302
    with app.app_context(): assert [d.status for d in Draft.query.order_by(Draft.id)] == ['superseded','pending']


def test_parallel_previews_and_withdraw_preserve_finances(app, client, paid_round):
    first = proposal(client, paid_round)
    stale = proposal(client, paid_round, form('273'))
    before = finances(app, paid_round)
    assert save(client, paid_round, first).status_code == 302
    assert save(client, paid_round, stale).status_code == 400
    with app.app_context(): did = Draft.query.one().id
    assert client.post(url(paid_round), data={'action':'withdraw','draft_id':did,'withdraw_reason':''}).status_code == 400
    for _ in range(2):
        assert client.post(url(paid_round), data={'action':'withdraw','draft_id':did,'withdraw_reason':'Synthetic cancelled'}).status_code == 302
    with app.app_context():
        draft = Draft.query.one()
        assert draft.status == 'withdrawn' and draft.status_reason == 'Synthetic cancelled'
    assert finances(app, paid_round) == before


@pytest.mark.parametrize('kind', ['member','finance','hidden_finance'])
def test_draft_access_and_read_only_finance(app, client, paid_round, kind):
    with app.app_context():
        member = Member.query.filter(Member.id != paid_round[0]).first()
        mid = member.id
        if kind != 'member': member.funktion = Funktion.SCHATZMEISTER
        if kind == 'hidden_finance': db.session.get(Event,paid_round[1]).audience = EventAudience.BOARD
        db.session.commit()
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, mid); state['_fresh'] = True
    before = finances(app, paid_round)
    assert client.get(url(paid_round)).status_code == (200 if kind == 'finance' else 403)
    assert client.post(url(paid_round), data=form()).status_code == 403
    assert finances(app, paid_round) == before


def test_closed_year_allows_draft_only_without_opening_year(app, client, paid_round):
    with app.app_context():
        FiscalYear.query.one().status = FiscalYearStatus.CLOSED; db.session.commit()
    before = finances(app, paid_round)
    token = proposal(client, paid_round)
    assert save(client, paid_round, token).status_code == 302
    assert finances(app, paid_round) == before
    with app.app_context():
        assert FiscalYear.query.one().status == FiscalYearStatus.CLOSED
        assert Draft.query.one().preview_json['blocked_years'] == [2026]


@pytest.mark.parametrize('bad', ['private_target','waived','negative_paid','mismatched_claim','no_change'])
def test_invalid_draft_does_not_change_anything(app, client, paid_round, bad):
    values = form()
    with app.app_context():
        if bad == 'private_target': values.update(paid_by='mitglied', payer_member_id=str(paid_round[0]))
        if bad == 'waived': MemberClaim.query.first().status = ClaimStatus.ERLASSEN
        if bad == 'negative_paid': MemberClaim.query.first().paid_rappen = -1
        if bad == 'mismatched_claim': MemberClaim.query.first().expected_rappen += 1
        if bad == 'no_change': values['total'] = '252'
        db.session.commit()
    before = finances(app, paid_round)
    assert client.post(url(paid_round), data=values).status_code == 400
    assert finances(app, paid_round) == before
    with app.app_context(): assert Draft.query.count() == 0


@pytest.mark.parametrize('kind', ['tamper','expired','generation','other_actor'])
def test_draft_preview_bound_to_time_access_and_integrity(app, client, paid_round, monkeypatch, kind):
    from itsdangerous.timed import TimestampSigner
    token = proposal(client, paid_round)
    if kind == 'tamper': token += 'invalid'
    if kind == 'expired':
        original = TimestampSigner.get_timestamp
        monkeypatch.setattr(TimestampSigner, 'get_timestamp', lambda self: original(self) + 1900)
    if kind == 'generation':
        with app.app_context():
            db.session.get(Member, paid_round[0]).rotate_auth_generation(); db.session.commit()
        with client.session_transaction() as state:
            state['_user_id'] = auth_id(client, paid_round[0]); state['_fresh'] = True
    if kind == 'other_actor':
        from backend.models.member import Role
        with app.app_context():
            other = Member.query.filter(Member.id != paid_round[0]).first()
            other.role = Role.ADMIN; mid = other.id; db.session.commit()
        with client.session_transaction() as state:
            state['_user_id'] = auth_id(client, mid); state['_fresh'] = True
    before = finances(app, paid_round)
    assert save(client, paid_round, token).status_code == 400
    assert finances(app, paid_round) == before


def test_withdraw_storage_failure_keeps_pending_draft_and_finances(app, client, paid_round):
    assert save(client, paid_round, proposal(client, paid_round)).status_code == 302
    with app.app_context(): did = Draft.query.one().id
    before = finances(app, paid_round)
    def fail(*args): raise OperationalError('synthetic', {}, Exception('synthetic'))
    sa_event.listen(Draft, 'before_update', fail)
    try:
        assert client.post(url(paid_round), data={'action':'withdraw','draft_id':did,'withdraw_reason':'Synthetic'}).status_code == 400
    finally:
        sa_event.remove(Draft, 'before_update', fail)
    with app.app_context(): assert Draft.query.one().status == 'pending'
    assert finances(app, paid_round) == before


def test_draft_csrf_and_original_unpaid_confirm_still_protect_payments(app, client, paid_round):
    before = finances(app, paid_round)
    assert client.post(f'/billbro/{paid_round[1]}/correction', data=form()).status_code == 400
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(url(paid_round), data=form()).status_code == 400
    assert finances(app, paid_round) == before


def test_draft_projects_attendance_types_and_ggl_without_applying(app, client, paid_round):
    from tests.services.test_billbro_invoice_correction import seed_guesses
    from backend.models.participation import Participation
    seed_guesses(app, paid_round)
    with app.app_context():
        parts = Participation.query.order_by(Participation.member_id).all()
        absent, changed = parts[0].id, parts[1].id
    before = finances(app, paid_round)
    values = form(invoice='105', **{f'attendance_{absent}':'absent', f'esstyp_{changed}':'ALLIN'})
    assert save(client, paid_round, proposal(client, paid_round, values)).status_code == 302
    assert finances(app, paid_round) == before
    with app.app_context():
        view = Draft.query.one().preview_json
        paid = next(r for r in view['rows'] if r['member_id'] == paid_round[0])
        assert paid['refund'] == 8400 and paid['after'] == 0 and not paid['after_attending']
        assert any(r['before_type'] == 'NORMAL' and r['after_type'] == 'ALLIN' for r in view['rows'])
        assert any(r['before'] != r['after'] for r in view['ggl_rows'])
    assert client.post(url(paid_round), data={'action':'confirm'}).status_code == 400
    assert finances(app, paid_round) == before
