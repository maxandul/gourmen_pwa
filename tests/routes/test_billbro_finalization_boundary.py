"""No simple mutation can rewrite persisted BillBro settlement history."""
import pytest
from sqlalchemy import event as sa_event
from backend.extensions import db
from backend.models.event import Event, BillPaidBy
from backend.models.participation import Participation
from backend.models.accounting import MemberClaim, ClaimType
from tests.services.test_billbro_shares import round_data
from tests.services.test_audit_failure_boundary import seed


ACTIONS = [
    ('/events/{event}/rsvp', {}),
    ('/events/{event}/cleanup/rsvp', {'status': 'no'}),
    ('/billbro/{event}/mark_absent/{member}', {}),
    ('/billbro/{event}/mark_present/{member}', {}),
    ('/billbro/{event}/compute', {'esstyp': 'SPARSAM', 'guess_amount': '99'}),
    ('/billbro/{event}/update_guess', {'guess_amount': '99'}),
    ('/billbro/{event}/record_guess/{member}', {'esstyp': 'SPARSAM', 'guess_amount': '99'}),
    ('/billbro/{event}/enter_bill', {'rechnungsbetrag': '150'}),
    ('/billbro/{event}/set_payment', {'paid_by': BillPaidBy.MITGLIED.value}),
    ('/billbro/{event}/undo_final', {}),
    ('/billbro/{event}/reset_bill', {}),
    ('/billbro/{event}/toggle_status', {}),
]


def snapshot(app, event_id):
    with app.app_context():
        def row(obj): return tuple(getattr(obj, col.name) for col in obj.__table__.columns)
        return (row(db.session.get(Event, event_id)),
                tuple(row(p) for p in Participation.query.order_by(Participation.id)),
                tuple(row(c) for c in MemberClaim.query.order_by(MemberClaim.id)))


@pytest.mark.parametrize('path,data', ACTIONS)
@pytest.mark.parametrize('history', ['final', 'claim_only', 'share_only'])
def test_original_mutations_preserve_settlement(app, client, round_data, path, data, history):
    member, event_id = round_data[:2]
    with app.app_context():
        event = db.session.get(Event, event_id)
        # Legacy states can have an open round even though settlement history exists.
        event.billbro_closed = False
        if history == 'final': event.gesamtbetrag_rappen = 10000
        if history in ('claim_only', 'final'):
            db.session.add(MemberClaim(event_id=event_id, member_id=member,
                claim_type=ClaimType.ESSENSANTEIL, expected_rappen=3334, paid_rappen=500))
        if history == 'share_only': Participation.query.first().calculated_share_rappen = 3334
        db.session.commit(); engine = db.engine
    before = snapshot(app, event_id)
    statements = []
    def record(conn, cursor, sql, *args): statements.append(sql.lstrip().upper())
    sa_event.listen(engine, 'before_cursor_execute', record)
    try:
        for _ in range(2):
            response = client.post(path.format(event=event_id, member=member), data={**data, 'payer_member_id': member})
            assert response.status_code == 302
    finally:
        sa_event.remove(engine, 'before_cursor_execute', record)
    assert not any(sql.startswith(('INSERT', 'UPDATE', 'DELETE')) for sql in statements)
    assert snapshot(app, event_id) == before


def test_ajax_explicit_conflict(app, client, round_data):
    with app.app_context():
        db.session.get(Event, round_data[1]).gesamtbetrag_rappen = 10000; db.session.commit()
    response = client.post(f'/events/{round_data[1]}/rsvp', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response.status_code == 409 and response.json['correction_required'] is True


def test_prefinal_closed_round_allows_payment_and_attendance(app, client, round_data):
    member, event_id = round_data[:2]
    with app.app_context():
        db.session.get(Event, event_id).billbro_closed = True; db.session.commit()
    assert client.post(f'/billbro/{event_id}/set_payment', data={'paid_by': BillPaidBy.MITGLIED.value, 'payer_member_id': member}).status_code == 302
    assert client.post(f'/billbro/{event_id}/mark_absent/{member}').status_code == 302
    assert client.post(f'/billbro/{event_id}/mark_present/{member}').status_code == 302
    with app.app_context():
        event = db.session.get(Event, event_id)
        assert event.bill_paid_by == BillPaidBy.MITGLIED and event.bill_payer_member_id == member
        assert Participation.query.filter_by(member_id=member).one().teilnahme
        assert MemberClaim.query.count() == 0


@pytest.mark.parametrize('endpoint', ['set_total', 'accept_suggested_total'])
def test_old_share_only_state_cannot_be_re_finalized(app, client, round_data, endpoint):
    with app.app_context():
        Participation.query.first().calculated_share_rappen = 777; db.session.commit()
    before = snapshot(app, round_data[1])
    response = client.post(f'/billbro/{round_data[1]}/{endpoint}', data={'gesamtbetrag_manual': '100'})
    assert response.status_code == 400
    assert snapshot(app, round_data[1]) == before
