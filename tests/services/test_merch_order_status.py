"""Atomic original status endpoints, financial history and retry boundaries."""
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.merch_order import MerchOrder, OrderStatus
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import MemberClaim, ClaimType, ClaimStatus
from tests.routes.test_merch_read_only import catalogue
from tests.services.test_audit_failure_boundary import seed


@pytest.fixture(params=['status', 'status-update'])
def endpoint(request, catalogue):
    return f'/admin/merch/orders/{catalogue[3]}/{request.param}'


def post(client, endpoint, target):
    return client.post(endpoint, data={'status': target, 'next': '/admin/merch?tab=orders'})


def test_success_and_retry_have_one_claim_and_stable_delivery(app, client, catalogue, endpoint):
    assert post(client, endpoint, 'WIRD_GELIEFERT').status_code == 302
    with app.app_context():
        claim = MemberClaim.query.one()
        assert claim.expected_rappen == 1900 and claim.paid_rappen == 0
        claim.register_payment(500)
        db.session.commit()
        claim_id = claim.id
    assert post(client, endpoint, 'GELIEFERT').status_code == 302
    with app.app_context():
        order = db.session.get(MerchOrder, catalogue[3])
        delivered = order.delivered_at
        assert delivered is not None and order.status == OrderStatus.GELIEFERT
        claim = MemberClaim.query.one()
        assert claim.id == claim_id and claim.paid_rappen == 500 and claim.status == ClaimStatus.TEILWEISE
        engine = db.engine
    statements = []
    def record(conn, cursor, sql, *args): statements.append(sql.lstrip().upper())
    sa_event.listen(engine, 'before_cursor_execute', record)
    try:
        assert post(client, endpoint, 'GELIEFERT').status_code == 302
    finally:
        sa_event.remove(engine, 'before_cursor_execute', record)
    assert not any(sql.startswith(('INSERT', 'UPDATE', 'DELETE')) for sql in statements)
    with app.app_context():
        assert db.session.get(MerchOrder, catalogue[3]).delivered_at == delivered
        assert MemberClaim.query.one().paid_rappen == 500


@pytest.mark.parametrize('failure', ['insert', 'commit'])
def test_failure_rolls_back_status_timestamp_and_claim(app, client, catalogue, endpoint, monkeypatch, failure):
    def fail(*args, **kwargs): raise OperationalError('synthetic', {}, Exception('PRIVATE-MARKER'))
    with app.app_context(): engine = db.engine
    def before(conn, cursor, sql, *args):
        if sql.lower().startswith('insert into member_claims'): fail()
    if failure == 'commit': monkeypatch.setattr(db.session, 'commit', fail)
    else: sa_event.listen(engine, 'before_cursor_execute', before)
    try:
        response = post(client, endpoint, 'GELIEFERT')
    finally:
        if failure == 'insert': sa_event.remove(engine, 'before_cursor_execute', before)
    assert response.status_code == 302
    with client.session_transaction() as state:
        messages = str(state.get('_flashes'))
        assert 'nicht gespeichert' in messages and 'PRIVATE-MARKER' not in messages
    with app.app_context():
        order = db.session.get(MerchOrder, catalogue[3])
        assert order.status == OrderStatus.BESTELLT and order.delivered_at is None
        assert MemberClaim.query.count() == 0


@pytest.mark.parametrize('target', ['BESTELLT', 'WIRD_GELIEFERT', 'INVALID'])
def test_backward_and_invalid_preserve_paid_history(app, client, catalogue, endpoint, target):
    assert post(client, endpoint, 'GELIEFERT').status_code == 302
    with app.app_context():
        claim = MemberClaim.query.one(); claim.register_payment(1900); db.session.commit()
        delivered = db.session.get(MerchOrder, catalogue[3]).delivered_at
    assert post(client, endpoint, target).status_code == 302
    with app.app_context():
        order = db.session.get(MerchOrder, catalogue[3])
        assert order.status == OrderStatus.GELIEFERT and order.delivered_at == delivered
        claim = MemberClaim.query.one()
        assert claim.paid_rappen == 1900 and claim.status == ClaimStatus.BEGLICHEN


@pytest.mark.parametrize('mismatch', ['line', 'order', 'empty', 'amount', 'creditor', 'type', 'duplicate'])
def test_inconsistent_history_not_repaired(app, client, catalogue, endpoint, mismatch):
    with app.app_context():
        order = db.session.get(MerchOrder, catalogue[3])
        if mismatch == 'line': db.session.get(MerchOrderItem, catalogue[4]).total_member_price_rappen = 1234
        elif mismatch == 'order': order.total_member_price_rappen = 1234
        elif mismatch == 'empty': db.session.delete(db.session.get(MerchOrderItem, catalogue[4]))
        else:
            claim = MemberClaim(member_id=order.member_id, merch_order_id=order.id, claim_type=ClaimType.MERCH, expected_rappen=1900, paid_rappen=500)
            if mismatch == 'amount': claim.expected_rappen = 1234
            if mismatch == 'creditor': claim.creditor_member_id = order.member_id
            if mismatch == 'type': claim.claim_type = ClaimType.ESSENSANTEIL
            db.session.add(claim)
            if mismatch == 'duplicate':
                db.session.add(MemberClaim(member_id=order.member_id, merch_order_id=order.id, claim_type=ClaimType.MERCH, expected_rappen=1900, paid_rappen=0))
        db.session.commit()
        before = [(c.id, c.expected_rappen, c.paid_rappen) for c in MemberClaim.query.order_by(MemberClaim.id)]
    assert post(client, endpoint, 'GELIEFERT').status_code == 302
    with app.app_context():
        assert db.session.get(MerchOrder, catalogue[3]).status == OrderStatus.BESTELLT
        assert [(c.id, c.expected_rappen, c.paid_rappen) for c in MemberClaim.query.order_by(MemberClaim.id)] == before


def test_zero_member_total_without_fake_claim(app, client, catalogue, endpoint):
    with app.app_context():
        item = db.session.get(MerchOrderItem, catalogue[4]); item.unit_member_price_rappen = 0; item.calculate_totals()
        db.session.get(MerchOrder, catalogue[3]).calculate_totals(); db.session.commit()
    assert post(client, endpoint, 'GELIEFERT').status_code == 302
    with app.app_context():
        assert db.session.get(MerchOrder, catalogue[3]).status == OrderStatus.GELIEFERT
        assert MemberClaim.query.count() == 0
