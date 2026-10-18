"""Original unpaid correction workflow, evidence and stale-state rejection."""
import re
from datetime import date
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.event import Event, BillPaidBy
from backend.models.participation import Participation
from backend.models.member import Member, Role
from backend.models.accounting import MemberClaim, ClaimStatus, FiscalYear, FiscalYearStatus
from backend.models.billbro_correction import BillBroCorrection
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed
from tests.routes.test_billbro_finalization_boundary import snapshot
from tests.conftest import auth_id


@pytest.fixture
def final_round(app, client, round_data):
    assert client.post(f'/billbro/{round_data[1]}/set_total', data={'gesamtbetrag_manual': '100'}).status_code == 302
    return round_data


def url(ids): return f'/billbro/{ids[1]}/correction'


def data(**kwargs):
    return dict(total='120', paid_by='vereinskonto', reason='Synthetic correction', **kwargs)


def preview(client, ids, form=None):
    response = client.post(url(ids), data=form or data())
    assert response.status_code == 200, response.text
    token = re.search(r'name="preview_token" value="([^"]+)"', response.text).group(1)
    return token


def confirm(client, ids, token):
    return client.post(url(ids), data={'action': 'confirm', 'preview_token': token})


def test_preview_read_only_confirm_history_and_retry(app, client, final_round):
    before = snapshot(app, final_round[1])
    with app.app_context(): engine = db.engine
    writes = []
    def record(conn, cursor, sql, *args):
        if sql.lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')): writes.append(sql)
    sa_event.listen(engine, 'before_cursor_execute', record)
    try:
        assert client.get(url(final_round)).status_code == 200
        token = preview(client, final_round)
    finally: sa_event.remove(engine, 'before_cursor_execute', record)
    assert not writes and snapshot(app, final_round[1]) == before
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        history = BillBroCorrection.query.one()
        assert history.reason == 'Synthetic correction' and history.actor_id == final_round[0]
        assert history.before_json['event']['gesamtbetrag_rappen'] == 10000
        assert history.after_json['event']['gesamtbetrag_rappen'] == 12000
        assert sum(c.expected_rappen for c in MemberClaim.query.all()) == 12000
        assert {c['id'] for c in history.before_json['claims']}.isdisjoint({c.id for c in MemberClaim.query.all()})
        assert sum(p.calculated_share_rappen for p in Participation.query.all()) == 12000
    after = snapshot(app, final_round[1])
    assert confirm(client, final_round, token).status_code == 302
    assert snapshot(app, final_round[1]) == after
    with app.app_context(): assert BillBroCorrection.query.count() == 1
    response = client.get(url(final_round))
    assert response.status_code == 200 and 'Synthetic correction' in response.text and '120.00 CHF' in response.text


def test_payer_change_creates_no_self_claim_and_preserves_participation(app, client, final_round):
    token = preview(client, final_round, {'total': '100', 'paid_by': 'mitglied', 'payer_member_id': str(final_round[0]), 'reason': 'Private payer'})
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        event = db.session.get(Event, final_round[1]); claims = MemberClaim.query.all()
        assert event.bill_paid_by == BillPaidBy.MITGLIED and len(claims) == 2
        assert all(c.member_id != final_round[0] and c.creditor_member_id == final_round[0] for c in claims)
        assert len([p for p in Participation.query.all() if p.teilnahme]) == 3
    token = preview(client, final_round, data(private_unpaid_confirmed='yes', private_unpaid_note='Synthetic clarification: no private payments'))
    assert confirm(client, final_round, token).status_code == 302
    with app.app_context():
        assert MemberClaim.query.count() == 3
        assert all(c.creditor_member_id is None for c in MemberClaim.query.all())
        assert BillBroCorrection.query.count() == 2


@pytest.mark.parametrize('change', ['payment', 'amount', 'participation', 'reason_note', 'year', 'generation'])
def test_changed_state_rejects_old_preview(app, client, final_round, change):
    token = preview(client, final_round)
    with app.app_context():
        if change == 'payment': MemberClaim.query.first().register_payment(100)
        elif change == 'amount': db.session.get(Event, final_round[1]).gesamtbetrag_rappen = 11000
        elif change == 'participation': Participation.query.first().esstyp = None
        elif change == 'reason_note': MemberClaim.query.first().note = 'Later note'
        elif change == 'year':
            db.session.add(FiscalYear(year=2026, start_date=date(2026,1,1), end_date=date(2026,12,31), status=FiscalYearStatus.CLOSED))
        else: db.session.get(Member, final_round[0]).rotate_auth_generation()
        db.session.commit()
    if change == 'generation':
        with client.session_transaction() as state: state['_user_id'] = auth_id(client, final_round[0])
    before = snapshot(app, final_round[1])
    assert confirm(client, final_round, token).status_code == 400
    assert snapshot(app, final_round[1]) == before
    with app.app_context(): assert BillBroCorrection.query.count() == 0


@pytest.mark.parametrize('bad', ['paid', 'waived', 'mismatch', 'duplicate', 'reason', 'below_invoice', 'invalid_payer', 'no_change'])
def test_invalid_or_financial_case_never_mutates(app, client, final_round, bad):
    form = data()
    with app.app_context():
        claim = MemberClaim.query.first()
        if bad == 'paid': claim.register_payment(100)
        elif bad == 'waived': claim.status = ClaimStatus.ERLASSEN
        elif bad == 'mismatch': claim.expected_rappen += 1
        elif bad == 'duplicate':
            db.session.add(MemberClaim(member_id=claim.member_id, event_id=claim.event_id, claim_type=claim.claim_type, expected_rappen=claim.expected_rappen))
        elif bad == 'reason': form['reason'] = ' '
        elif bad == 'below_invoice': form['total'] = '99'
        elif bad == 'invalid_payer': form.update(paid_by='mitglied', payer_member_id='9999')
        elif bad == 'no_change': form['total'] = '100'
        db.session.commit()
    before = snapshot(app, final_round[1])
    response = client.post(url(final_round), data=form)
    assert response.status_code == 400 and 'role="alert"' in response.text
    assert snapshot(app, final_round[1]) == before


@pytest.mark.parametrize('failure', ['claim', 'history', 'commit'])
def test_atomic_failure_preserves_old_claims_and_allows_retry(app, client, final_round, monkeypatch, failure):
    token = preview(client, final_round)
    before = snapshot(app, final_round[1])
    def fail(*args, **kwargs): raise OperationalError('synthetic', {}, Exception('SECRET-MARKER'))
    model = MemberClaim if failure == 'claim' else BillBroCorrection
    if failure == 'commit': monkeypatch.setattr(db.session, 'commit', fail)
    else: sa_event.listen(model, 'before_insert', fail)
    try:
        response = confirm(client, final_round, token)
    finally:
        if failure != 'commit': sa_event.remove(model, 'before_insert', fail)
        else: monkeypatch.undo()
    assert response.status_code == 400 and 'SECRET-MARKER' not in response.text
    assert snapshot(app, final_round[1]) == before
    with app.app_context(): assert BillBroCorrection.query.count() == 0
    assert confirm(client, final_round, token).status_code == 302


def test_tampered_token_and_unauthorized_member(app, client, final_round):
    token = preview(client, final_round)
    assert confirm(client, final_round, token + 'changed').status_code == 400
    with app.app_context(): other = Member.query.filter(Member.id != final_round[0]).first().id
    with client.session_transaction() as state: state['_user_id'] = auth_id(client, other)
    assert client.get(url(final_round)).status_code == 403
    assert confirm(client, final_round, token).status_code == 403


from tests.services.test_bank_booking_atomicity import case
from backend.models.accounting import Booking, BookingDirection, BankTransaction
from backend.models.bank_payment_allocation import BankPaymentAllocation


@pytest.mark.parametrize('linked', ['booking', 'allocation'])
def test_existing_accounting_evidence_blocks_even_zero_paid_counter(app, client, final_round, case, linked):
    with app.app_context():
        claim = MemberClaim.query.filter_by(event_id=final_round[1]).first()
        fy = FiscalYear.query.one()
        booking = Booking(fiscal_year_id=fy.id, booking_date=date(2026,10,18), description='Synthetic prior evidence',
                          amount_rappen=1, direction=BookingDirection.IN, account_id=case[1], created_by=case[0],
                          event_id=final_round[1] if linked == 'booking' else None)
        db.session.add(booking); db.session.flush()
        if linked == 'allocation':
            db.session.add(BankPaymentAllocation(bank_transaction_id=case[3], version=1, position=0, kind='claim',
                amount_rappen=1, claim_id=claim.id, booking_id=booking.id, member_id=claim.member_id, created_by=case[0]))
        db.session.commit()
    before = snapshot(app, final_round[1])
    response = client.post(url(final_round), data=data())
    assert response.status_code == 400 and 'Verbuchte Vorgänge' in response.text
    assert snapshot(app, final_round[1]) == before


def test_expired_and_other_admin_tokens_are_rejected(app, client, final_round, monkeypatch):
    from itsdangerous import TimestampSigner
    token = preview(client, final_round)
    now = TimestampSigner.get_timestamp(None)
    with monkeypatch.context() as patch:
        patch.setattr(TimestampSigner, 'get_timestamp', lambda self: now + 1801)
        assert confirm(client, final_round, token).status_code == 400
    with app.app_context():
        other = Member.query.filter(Member.id != final_round[0]).first()
        other.role = Role.ADMIN; db.session.commit(); other_id = other.id
    with client.session_transaction() as state: state['_user_id'] = auth_id(client, other_id)
    assert confirm(client, final_round, token).status_code == 400
    with app.app_context(): assert BillBroCorrection.query.count() == 0


def test_csrf_required_and_missing_confirmation_does_not_write(app, client, final_round):
    app.config['WTF_CSRF_ENABLED'] = True
    before = snapshot(app, final_round[1])
    response = client.post(url(final_round), data=data())
    assert response.status_code == 400 and 'CSRF' in response.text
    assert snapshot(app, final_round[1]) == before


def test_private_only_correction_not_bound_to_unrelated_closed_club_year(app, client, final_round):
    form = {'total': '100', 'paid_by': 'mitglied', 'payer_member_id': str(final_round[0]), 'reason': 'Private payer'}
    assert confirm(client, final_round, preview(client, final_round, form)).status_code == 302
    with app.app_context():
        db.session.add(FiscalYear(year=2026, start_date=date(2026,1,1), end_date=date(2026,12,31), status=FiscalYearStatus.CLOSED)); db.session.commit()
    form['total'] = '120'
    form.update(private_unpaid_confirmed='yes', private_unpaid_note='Synthetic clarification: no private payments')
    assert confirm(client, final_round, preview(client, final_round, form)).status_code == 302


def test_existing_year_links_and_ggl_values_survive_correction(app, client, final_round):
    with app.app_context():
        fy = FiscalYear(year=2026, start_date=date(2026,1,1), end_date=date(2026,12,31))
        db.session.add(fy); db.session.flush(); year_id = fy.id
        for claim in MemberClaim.query.all(): claim.fiscal_year_id = fy.id
        part = Participation.query.first(); part.guess_bill_amount_rappen = 9900; part.diff_amount_rappen = 100; part.rank = 1; part.points = 3
        db.session.commit(); part_id = part.id
    assert confirm(client, final_round, preview(client, final_round)).status_code == 302
    with app.app_context():
        assert {c.fiscal_year_id for c in MemberClaim.query.all()} == {year_id}
        part = db.session.get(Participation, part_id)
        assert (part.guess_bill_amount_rappen, part.diff_amount_rappen, part.rank, part.points) == (9900,100,1,3)


def test_preview_distinguishes_own_share_from_new_claim(app, client, final_round):
    response = client.post(url(final_round), data={'total':'100', 'paid_by':'mitglied', 'payer_member_id':str(final_round[0]), 'reason':'Private payer'})
    assert response.status_code == 200
    assert 'Anteil 33.34 CHF → 33.34 CHF; offener Posten 33.34 CHF → 0.00 CHF' in response.text
