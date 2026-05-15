"""Unit-Tests Merch v2 Services (Subvention, Sortiment-Kombinatorik, Round-Graph)."""

from __future__ import annotations

import pytest

from backend.extensions import db
from backend.services.merch_order_service import MerchOrderService
from backend.services.merch_round_service import MerchRoundService
from backend.services.merch_sortiment_service import MerchSortimentService
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
