"""Unit-Tests Merch v2 Services (Subvention, Sortiment-Kombinatorik, Round-Graph)."""

from __future__ import annotations

import pytest

from backend.extensions import db
from backend.services.merch_order_service import MerchOrderService
from backend.services.merch_round_service import MerchRoundService
from backend.services.merch_sortiment_service import (
    MerchSortimentService,
    parse_variant_schema_text,
    variant_schema_to_lines,
)
from backend.models.merch_v2 import MerchRoundStatus


@pytest.mark.parametrize(
    'gross,cap,expected_subsidy,expected_due',
    [
        (3700, 1500, 1500, 2200),
        (1200, 1500, 1200, 0),
        (0, 1500, 0, 0),
        (5000, 0, 0, 5000),
    ],
)
def test_subsidy_matches_capability_examples(gross, cap, expected_subsidy, expected_due):
    sub, due = MerchOrderService.subsidy_and_member_due_rappen(gross, cap)
    assert sub == expected_subsidy
    assert due == expected_due


def test_variant_combinations_empty_schema():
    assert MerchSortimentService.variant_attribute_combinations(None) == [{}]
    assert MerchSortimentService.variant_attribute_combinations({}) == [{}]


def test_variant_combinations_cartesian():
    schema = {'farbe': ['schwarz', 'weiss'], 'groesse': ['S', 'M']}
    combos = MerchSortimentService.variant_attribute_combinations(schema)
    assert len(combos) == 4
    assert {'farbe': 'schwarz', 'groesse': 'M'} in combos


def test_parse_variant_schema_lines_ok():
    raw = 'farbe: schwarz, weiss\ngroesse: S, M'
    schema, err = parse_variant_schema_text(raw)
    assert err is None
    assert schema == {'farbe': ['schwarz', 'weiss'], 'groesse': ['S', 'M']}


def test_parse_variant_schema_empty_means_standard():
    schema, err = parse_variant_schema_text('  \n')
    assert err is None
    assert schema == {}


def test_parse_variant_schema_duplicate_dimension():
    schema, err = parse_variant_schema_text('a: 1\nx: 2\na: 3')
    assert schema is None
    assert err is not None


def test_parse_variant_schema_combination_cap():
    opts = ', '.join(str(i) for i in range(16))
    raw = f'a: {opts}\nb: {opts}'
    schema, err = parse_variant_schema_text(raw)
    assert schema is None
    assert err and 'Kombinationen' in err


def test_variant_schema_round_trip_lines():
    s = {'farbe': ['a', 'b'], 'groesse': ['S']}
    assert parse_variant_schema_text(variant_schema_to_lines(s))[0] == s


def test_sync_variants_deactivates_removed_combo(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import MerchArticle, MerchSupplier, MerchVariant

    with app.app_context():
        m = Member(
            vorname='x',
            nachname='y',
            email='sync-var@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        sup = MerchSupplier(name='S2')
        db.session.add(sup)
        db.session.flush()
        art = MerchArticle(name='Art', supplier_id=sup.id, list_price_rappen=100, variant_schema={})
        db.session.add(art)
        db.session.flush()
        MerchSortimentService.sync_variants_for_article(art, {'farbe': ['x', 'y']})
        db.session.commit()
        aid = art.id
        assert MerchVariant.query.filter_by(article_id=aid, is_active=True).count() == 2

        art2 = db.session.get(MerchArticle, aid)
        MerchSortimentService.sync_variants_for_article(art2, {'farbe': ['x']})
        db.session.commit()
        active = MerchVariant.query.filter_by(article_id=aid, is_active=True).all()
        assert len(active) == 1
        assert active[0].attributes == {'farbe': 'x'}


def test_round_cancel_allowed_from_draft_not_from_closed():
    assert MerchRoundService.is_forward_transition(
        MerchRoundStatus.DRAFT,
        MerchRoundStatus.CANCELLED,
    )
    assert not MerchRoundService.is_forward_transition(
        MerchRoundStatus.CLOSED,
        MerchRoundStatus.CANCELLED,
    )


def test_round_cancel_requires_reason(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='round-cancel@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()
        created = MerchRoundService.create_draft_round(title='X', marketing_chief_id=m.id)
        db.session.commit()
        r = created['round']
        bad = MerchRoundService.apply_transition(r, MerchRoundStatus.CANCELLED)
        assert not bad['success']
        ok = MerchRoundService.apply_transition(r, MerchRoundStatus.CANCELLED, cancellation_reason='Zu frueh')
        assert ok['success']
        assert r.status == MerchRoundStatus.CANCELLED
        db.session.commit()


def test_revert_workflow_step_from_locked_preserves_confirmed_orders(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRound,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-locked@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-back', supplier_id=s.id, list_price_rappen=1500)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Locked', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=2,
                unit_price_at_confirm_rappen=1500,
            )
        )
        o.gross_amount_rappen = 3000
        o.subsidy_amount_rappen = 0
        o.member_amount_due_rappen = 3000
        db.session.commit()
        oid = o.id

        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        db.session.commit()

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        r2 = db.session.get(MerchRound, r.id)
        o2 = db.session.get(MerchOrder, oid)
        assert r2.status == MerchRoundStatus.OPEN
        assert r2.locked_at is None
        assert o2.status == MerchOrderStatus.DRAFT


def test_revert_workflow_step_from_open_preserves_orders(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-open@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-open-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-open', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Open', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()
        oid = o.id

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert r.status == MerchRoundStatus.DRAFT
        o2 = db.session.get(MerchOrder, oid)
        assert o2.status == MerchOrderStatus.DRAFT


def test_revert_workflow_step_from_ordered_at_supplier_preserves_confirmed_orders(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-ordered@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-ord-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-ord', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Ordered', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()
        oid = o.id

        assert compute_round_workflow_phase(r) == 4

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert r.status == MerchRoundStatus.LOCKED
        assert r.ordered_at is None
        o2 = db.session.get(MerchOrder, oid)
        assert o2.status == MerchOrderStatus.CONFIRMED


def test_revert_workflow_step_from_invoiced_keeps_orders_as_confirmed(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-invoiced@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-inv-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-inv', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Inv', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()
        ri.effective_supplier_price_rappen = 800
        ri.member_price_rappen = 1000

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()

        inv = MerchOrderService.invoice_confirmed_orders_for_round(r)
        assert inv['success']
        db.session.commit()
        oid = o.id

        assert compute_round_workflow_phase(r) == 5

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert r.status == MerchRoundStatus.ORDERED_AT_SUPPLIER
        assert compute_round_workflow_phase(r) == 4
        o2 = db.session.get(MerchOrder, oid)
        assert o2.status == MerchOrderStatus.CONFIRMED
        assert o2.invoiced_at is None


def test_revert_workflow_step_from_pricing_preserves_round_item_prices(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-pricing-prices@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-prices-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-prices', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Prices-Back', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()
        ri.effective_supplier_price_rappen = 800
        ri.member_price_rappen = 950

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()
        MerchOrderService.invoice_confirmed_orders_for_round(r)
        db.session.commit()

        assert compute_round_workflow_phase(r) == 5

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert compute_round_workflow_phase(r) == 4
        ri2 = db.session.get(MerchRoundItem, ri.id)
        assert ri2.effective_supplier_price_rappen == 800
        assert ri2.member_price_rappen == 950
        o2 = db.session.get(MerchOrder, o.id)
        assert o2.status == MerchOrderStatus.CONFIRMED
        assert o2.gross_amount_rappen == 950
        assert o2.member_amount_due_rappen == 950
        assert o2.order_items[0].unit_price_at_confirm_rappen == 950


def test_revert_workflow_step_from_beleg_with_saved_total_returns_to_beleg(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-beleg-saved@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-beleg-saved')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-beleg', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Beleg-Saved', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()
        ri.effective_supplier_price_rappen = 800
        ri.member_price_rappen = 1000

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()
        MerchOrderService.invoice_confirmed_orders_for_round(r)
        r.supplier_invoice_total_rappen = 12345
        MerchRoundService.complete_supplier_invoice_step(r)
        db.session.commit()

        assert compute_round_workflow_phase(r) == 6

        res6 = MerchRoundService.revert_workflow_step(r)
        assert res6['success']
        db.session.commit()
        assert compute_round_workflow_phase(r) == 5
        assert r.supplier_invoice_total_rappen == 12345
        o2 = db.session.get(MerchOrder, o.id)
        assert o2.status == MerchOrderStatus.INVOICED
        assert o2.gross_amount_rappen == 1000
        assert o2.subsidy_amount_rappen == 0
        assert o2.member_amount_due_rappen == 1000
        assert o2.order_items[0].unit_price_final_rappen == 1000


def test_supplier_invoice_total_save_does_not_complete_beleg_step(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='beleg-save-only@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-beleg-save-only')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-beleg-save', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Beleg-Save-Only', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()
        ri.effective_supplier_price_rappen = 800
        ri.member_price_rappen = 1000

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()
        MerchOrderService.invoice_confirmed_orders_for_round(r)
        r.supplier_invoice_total_rappen = 9999
        db.session.commit()

        assert compute_round_workflow_phase(r) == 5
        assert r.supplier_invoice_completed_at is None

        step = MerchRoundService.complete_supplier_invoice_step(r)
        assert step['success']
        db.session.commit()
        assert compute_round_workflow_phase(r) == 6
        assert r.supplier_invoice_completed_at is not None


def test_supplier_invoice_add_and_delete(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchRoundItem,
        MerchRoundStatus,
        MerchRoundSupplierInvoice,
        MerchSupplier,
        MerchVariant,
    )

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='beleg-multi@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-beleg-multi')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-beleg-multi', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Beleg-Multi', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        db.session.commit()

        MerchRoundService.add_supplier_invoice_upload(
            r,
            drive_file_id='drive-file-1',
            original_filename='rechnung-1.pdf',
        )
        MerchRoundService.add_supplier_invoice_upload(
            r,
            drive_file_id='drive-file-2',
            original_filename='rechnung-2.pdf',
        )
        db.session.commit()
        db.session.refresh(r)

        assert len(r.supplier_invoices) == 2
        assert r.supplier_invoice_drive_file_id == 'drive-file-1'

        inv2 = MerchRoundSupplierInvoice.query.filter_by(
            round_id=r.id,
            drive_file_id='drive-file-2',
        ).one()
        result = MerchRoundService.delete_supplier_invoice(r, inv2.id)
        assert result['success']
        assert result['drive_file_id'] == 'drive-file-2'
        db.session.commit()
        db.session.refresh(r)

        assert len(r.supplier_invoices) == 1
        assert r.supplier_invoice_drive_file_id == 'drive-file-1'


def test_revert_workflow_step_from_delivered_preserves_invoiced_orders(app):
    from datetime import datetime

    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-delivered@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-del-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-del', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Del', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        MerchRoundService.apply_transition(r, MerchRoundStatus.DELIVERED)
        db.session.commit()

        o = MerchOrder(
            round_id=r.id,
            member_id=m.id,
            status=MerchOrderStatus.PICKED_UP,
            picked_up_at=datetime.utcnow(),
            picked_up_by_member_id=m.id,
        )
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
                unit_price_final_rappen=1000,
            )
        )
        db.session.commit()
        oid = o.id

        assert compute_round_workflow_phase(r) == 7

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert r.status == MerchRoundStatus.ORDERED_AT_SUPPLIER
        assert r.delivered_at is None
        o2 = db.session.get(MerchOrder, oid)
        assert o2.status == MerchOrderStatus.INVOICED
        assert o2.picked_up_at is None


def test_revert_workflow_step_from_closed_resets_pickup(app):
    from datetime import datetime

    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import compute_round_workflow_phase

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='step-back-closed@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-closed-back')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-closed', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back-Closed', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        MerchRoundService.apply_transition(r, MerchRoundStatus.DELIVERED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.CLOSED)
        db.session.commit()

        o = MerchOrder(
            round_id=r.id,
            member_id=m.id,
            status=MerchOrderStatus.PICKED_UP,
            picked_up_at=datetime.utcnow(),
            picked_up_by_member_id=m.id,
        )
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
                unit_price_final_rappen=1000,
            )
        )
        db.session.commit()
        oid = o.id

        assert compute_round_workflow_phase(r) == 8

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        assert r.status == MerchRoundStatus.DELIVERED
        assert r.closed_at is None
        assert compute_round_workflow_phase(r) == 7
        o2 = db.session.get(MerchOrder, oid)
        assert o2.status == MerchOrderStatus.INVOICED
        assert o2.picked_up_at is None


def test_round_item_add_duplicate_and_open_blocks_second_add(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import MerchArticle, MerchSupplier, MerchVariant

    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='round-items@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='S')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='A', supplier_id=s.id, list_price_rappen=100)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        rd = MerchRoundService.create_draft_round(title='R', marketing_chief_id=m.id)
        db.session.commit()
        r = rd['round']

        first = MerchRoundService.add_variant_to_round(r.id, v.id)
        assert first['success']
        assert first['item'].list_price_snapshot_rappen == 100
        db.session.commit()

        dup = MerchRoundService.add_variant_to_round(r.id, v.id)
        assert not dup['success']

        open_ok = MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        assert open_ok['success']
        db.session.commit()

        bad_add = MerchRoundService.add_variant_to_round(r.id, v.id)
        assert not bad_add['success']


def test_open_without_items_rejected(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member

    with app.app_context():
        m = Member(
            vorname='o',
            nachname='p',
            email='open-empty@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()
        rd = MerchRoundService.create_draft_round(title='E', marketing_chief_id=m.id)
        db.session.commit()
        r = rd['round']
        blocked = MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        assert not blocked['success']


def test_round_forward_transitions_open_locked():
    assert MerchRoundService.is_forward_transition(
        MerchRoundStatus.OPEN,
        MerchRoundStatus.LOCKED,
    )
    assert MerchRoundService.is_forward_transition(
        MerchRoundStatus.LOCKED,
        MerchRoundStatus.OPEN,
    )
    assert not MerchRoundService.is_forward_transition(
        MerchRoundStatus.ORDERED_AT_SUPPLIER,
        MerchRoundStatus.OPEN,
    )


def test_confirm_order_rejects_empty_cart(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import MerchArticle, MerchRound, MerchRoundStatus, MerchSupplier, MerchVariant
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='c',
            nachname='o',
            email='confirm-empty@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='CS')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='CA', supplier_id=s.id, list_price_rappen=500)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='CEmpty', marketing_chief_id=m.id)
        db.session.commit()
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        res_o = MerchOrderService.get_or_create_draft_order(rid, m.id)
        assert res_o['success']
        oid = res_o['order'].id
        db.session.commit()

        bad = MerchOrderService.confirm_order(oid, m.id)
        assert not bad['success']


def test_invoice_uses_effective_price_when_member_price_empty(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import round_prices_complete

    with app.app_context():
        m = Member(
            vorname='p',
            nachname='x',
            email='pricing-default-mem@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-pricing')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-pricing', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Pricing-Default', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()
        ri.effective_supplier_price_rappen = 850
        ri.member_price_rappen = None

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=2,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()

        assert round_prices_complete(r)

        inv = MerchOrderService.invoice_confirmed_orders_for_round(r)
        assert inv['success']
        db.session.commit()

        assert ri.member_price_rappen == 850
        assert o.gross_amount_rappen == 1700
        assert o.status == MerchOrderStatus.INVOICED


def test_round_prices_complete_ignores_unordered_variants(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchRoundItem,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import round_prices_complete

    with app.app_context():
        m = Member(
            vorname='u',
            nachname='n',
            email='pricing-unordered@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        s = MerchSupplier(name='S-unordered')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Art-unordered', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v1 = MerchVariant(article_id=art.id, attributes={'farbe': 'schwarz'}, is_active=True)
        v2 = MerchVariant(article_id=art.id, attributes={'farbe': 'weiss'}, is_active=True)
        db.session.add_all([v1, v2])
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Unordered-Variant', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v1.id)
        MerchRoundService.add_variant_to_round(r.id, v2.id)
        db.session.commit()

        ri_ordered = MerchRoundItem.query.filter_by(round_id=r.id, variant_id=v1.id).one()
        ri_unordered = MerchRoundItem.query.filter_by(round_id=r.id, variant_id=v2.id).one()
        ri_ordered.effective_supplier_price_rappen = 800
        ri_unordered.effective_supplier_price_rappen = None

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        db.session.commit()

        from backend.models.merch_v2 import MerchOrder, MerchOrderItem, MerchOrderStatus

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri_ordered.id,
                quantity=1,
                unit_price_at_confirm_rappen=1000,
            )
        )
        db.session.commit()

        assert round_prices_complete(r)


def test_member_shop_index_rows_open_round_and_order_lines(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchColor,
        MerchRound,
        MerchRoundStatus,
        MerchSize,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='Shop',
            nachname='Index',
            email='shop-index@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='ShopSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Hoodie', supplier_id=s.id, list_price_rappen=5000)
        db.session.add(art)
        db.session.flush()
        color = MerchColor(slug='rot', label='Rot')
        size = MerchSize(slug='m', label='M')
        db.session.add_all([color, size])
        db.session.flush()
        v = MerchVariant(
            article_id=art.id,
            color_id=color.id,
            size_id=size.id,
            attributes={},
            is_active=True,
        )
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(
            title='Frühling 2026',
            marketing_chief_id=m.id,
        )
        db.session.commit()
        rid = cr['round'].id
        rnd = db.session.get(MerchRound, rid)
        rnd.subsidy_per_member_rappen = 1500
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        res_o = MerchOrderService.get_or_create_draft_order(rid, m.id)
        assert res_o['success']
        oid = res_o['order'].id
        ri = rnd.round_items[0]
        MerchOrderService.set_cart_line(oid, m.id, ri.id, 2)
        db.session.commit()

        rows = MerchOrderService.build_member_shop_index_rows(m.id)
        assert len(rows) == 1
        row = rows[0]
        assert row.round_title == 'Frühling 2026'
        assert row.status_value == 'Bestellen'
        assert row.article_lines == ('2x Hoodie, Rot, M',)
        assert row.list_total_chf == '100.00'
        assert row.member_total_chf == '100.00'
        assert row.subsidy_chf == '15.00'
        assert row.due_chf == '85.00'

        other = Member(
            vorname='Leer',
            nachname='Member',
            email='shop-empty@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(other)
        db.session.commit()
        empty_rows = MerchOrderService.build_member_shop_index_rows(other.id)
        assert len(empty_rows) == 1
        assert empty_rows[0].article_lines == ()
        assert empty_rows[0].list_total_chf is None


def test_member_workflow_phases(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRound,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_member_workflow import (
        MEMBER_WORKFLOW_STEP_LABELS,
        compute_member_workflow_phase,
        member_workflow_status_label,
    )
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='Flow',
            nachname='Test',
            email='member-flow@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='FlowSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Cap', supplier_id=s.id, list_price_rappen=2000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Flow-Runde', marketing_chief_id=m.id)
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)

        assert compute_member_workflow_phase(rnd, None) == 1
        assert member_workflow_status_label(1) == MEMBER_WORKFLOW_STEP_LABELS[0]

        o = MerchOrder(round_id=rid, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        ri = rnd.round_items[0]
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=1,
                unit_price_at_confirm_rappen=2000,
            )
        )
        db.session.commit()

        assert compute_member_workflow_phase(rnd, o) == 2

        MerchRoundService.apply_transition(rnd, MerchRoundStatus.LOCKED)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        assert compute_member_workflow_phase(rnd, o) == 2

        o.status = MerchOrderStatus.INVOICED
        o.gross_amount_rappen = 1800
        o.subsidy_amount_rappen = 500
        o.member_amount_due_rappen = 1300
        db.session.commit()
        assert compute_member_workflow_phase(rnd, o) == 3

        o.status = MerchOrderStatus.PICKED_UP
        db.session.commit()
        assert compute_member_workflow_phase(rnd, o) == 4

        o.status = MerchOrderStatus.PAID
        db.session.commit()
        assert compute_member_workflow_phase(rnd, o) == 4


def test_set_cart_line_reopens_confirmed_during_open(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderStatus,
        MerchRound,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='Edit',
            nachname='After',
            email='cart-reopen@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='ReopenSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Polo', supplier_id=s.id, list_price_rappen=3000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Reopen', marketing_chief_id=m.id)
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        res_o = MerchOrderService.get_or_create_draft_order(rid, m.id)
        oid = res_o['order'].id
        ri = rnd.round_items[0]
        MerchOrderService.set_cart_line(oid, m.id, ri.id, 1)
        MerchOrderService.confirm_order(oid, m.id)
        db.session.commit()

        o = db.session.get(MerchOrder, oid)
        assert o.status == MerchOrderStatus.CONFIRMED

        MerchOrderService.set_cart_line(oid, m.id, ri.id, 2)
        db.session.commit()
        o = db.session.get(MerchOrder, oid)
        assert o.status == MerchOrderStatus.DRAFT
        assert o.confirmed_at is None
        assert o.order_items[0].quantity == 2


def test_revert_member_workflow_step_from_confirmed(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderStatus,
        MerchRound,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_member_workflow import (
        compute_member_workflow_phase,
        member_step_back_available,
    )
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='Back',
            nachname='One',
            email='step-back-1@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='BackSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Tee', supplier_id=s.id, list_price_rappen=2500)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back1', marketing_chief_id=m.id)
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        res_o = MerchOrderService.get_or_create_draft_order(rid, m.id)
        oid = res_o['order'].id
        ri = rnd.round_items[0]
        MerchOrderService.set_cart_line(oid, m.id, ri.id, 1)
        MerchOrderService.confirm_order(oid, m.id)
        db.session.commit()

        o = db.session.get(MerchOrder, oid)
        phase = compute_member_workflow_phase(rnd, o)
        assert phase == 2
        assert member_step_back_available(rnd, o, phase=phase)
        result = MerchOrderService.revert_member_workflow_step(oid, m.id)
        assert result['success']
        db.session.commit()

        o = db.session.get(MerchOrder, oid)
        assert o.status == MerchOrderStatus.DRAFT
        assert len(o.order_items) == 1
        assert o.order_items[0].quantity == 1
        assert compute_member_workflow_phase(rnd, o) == 1


def test_revert_member_workflow_step_blocked_after_invoice(app):
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRound,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_member_workflow import (
        compute_member_workflow_phase,
        member_step_back_available,
    )
    from backend.services.merch_order_service import MerchOrderService
    from backend.services.merch_round_service import MerchRoundService

    with app.app_context():
        m = Member(
            vorname='Back',
            nachname='Three',
            email='step-back-3@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='InvSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Bag', supplier_id=s.id, list_price_rappen=4000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='Back3', marketing_chief_id=m.id)
        rid = cr['round'].id
        MerchRoundService.add_variant_to_round(rid, v.id)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)
        ri = rnd.round_items[0]
        ri.member_price_rappen = 3500
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.OPEN)
        db.session.commit()

        o = MerchOrder(round_id=rid, member_id=m.id, status=MerchOrderStatus.INVOICED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=2,
                unit_price_at_confirm_rappen=3500,
                unit_price_final_rappen=3500,
            )
        )
        o.gross_amount_rappen = 7000
        o.subsidy_amount_rappen = 1500
        o.member_amount_due_rappen = 5500
        db.session.commit()

        rnd = db.session.get(MerchRound, rid)
        MerchRoundService.apply_transition(rnd, MerchRoundStatus.LOCKED)
        db.session.commit()
        rnd = db.session.get(MerchRound, rid)

        phase = compute_member_workflow_phase(rnd, o)
        assert phase == 3
        assert not member_step_back_available(rnd, o, phase=phase)

        result = MerchOrderService.revert_member_workflow_step(o.id, m.id)
        assert not result['success']

        o = db.session.get(MerchOrder, o.id)
        assert o.status == MerchOrderStatus.INVOICED


def test_pricing_article_groups_from_aggregate_rows(app):
    """Regression: aggregate_rows liefert (MerchRoundItem, qty) — Filter muss item.id nutzen."""
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRound,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import build_pricing_article_groups

    with app.app_context():
        m = Member(
            vorname='Price',
            nachname='Groups',
            email='pricing-groups@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='PGSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Jacke', supplier_id=s.id, list_price_rappen=9900)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='PricingGroups', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        aggregate_rows = [(ri, 2), (ri, 0)]
        ordered_ids = {item.id for item, qty in aggregate_rows if qty > 0}
        filtered = [ri for ri in [ri] if ri.id in ordered_ids]
        groups = build_pricing_article_groups(filtered)
        assert len(groups) == 1
        assert groups[0].article_name == 'Jacke'


def test_lock_auto_confirms_draft_with_items_after_reopen(app):
    """Nach Re-Open (DRAFT) und erneutem Schliessen ohne Neu-Bestaetigung Positionen behalten."""
    from werkzeug.security import generate_password_hash

    from backend.models.member import Member
    from backend.models.merch_v2 import (
        MerchArticle,
        MerchOrder,
        MerchOrderItem,
        MerchOrderStatus,
        MerchRound,
        MerchRoundItem,
        MerchRoundStatus,
        MerchSupplier,
        MerchVariant,
    )
    from backend.services.merch_round_workflow import ordered_round_item_ids

    with app.app_context():
        m = Member(
            vorname='Re',
            nachname='Lock',
            email='relock@test',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.commit()

        s = MerchSupplier(name='ReSup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='Socken', supplier_id=s.id, list_price_rappen=1200)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        cr = MerchRoundService.create_draft_round(title='ReLock', marketing_chief_id=m.id)
        r = cr['round']
        MerchRoundService.add_variant_to_round(r.id, v.id)
        db.session.commit()
        ri = MerchRoundItem.query.filter_by(round_id=r.id).one()

        MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
        db.session.commit()

        o = MerchOrder(round_id=r.id, member_id=m.id, status=MerchOrderStatus.CONFIRMED)
        db.session.add(o)
        db.session.flush()
        db.session.add(
            MerchOrderItem(
                order_id=o.id,
                round_item_id=ri.id,
                quantity=3,
                unit_price_at_confirm_rappen=1200,
            )
        )
        db.session.commit()
        oid = o.id

        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        db.session.commit()

        res = MerchRoundService.revert_workflow_step(r)
        assert res['success']
        db.session.commit()

        o = db.session.get(MerchOrder, oid)
        assert o.status == MerchOrderStatus.DRAFT
        assert o.order_items[0].quantity == 3

        r = db.session.get(MerchRound, r.id)
        MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
        db.session.commit()

        o = db.session.get(MerchOrder, oid)
        assert o.status == MerchOrderStatus.CONFIRMED
        assert o.order_items[0].quantity == 3

        r = db.session.get(MerchRound, r.id)
        assert ri.id in ordered_round_item_ids(r)
