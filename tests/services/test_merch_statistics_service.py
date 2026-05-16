"""Tests Merch v2 Statistics (Kennzahlen ohne UI)."""

from __future__ import annotations

from datetime import datetime

from werkzeug.security import generate_password_hash

from backend.extensions import db
from backend.models.member import Member
from backend.models.merch_v2 import (
    MerchArticle,
    MerchOrder,
    MerchOrderItem,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchSupplier,
    MerchVariant,
)
from backend.services.merch_statistics_service import (
    compute_round_statistics,
    current_club_season_label_year,
)


def test_current_club_season_label_year():
    assert current_club_season_label_year(datetime(2026, 5, 10)) == 2025
    assert current_club_season_label_year(datetime(2026, 9, 1)) == 2026


def test_compute_round_statistics_empty_orders(app):
    with app.app_context():
        m = Member(
            vorname='a',
            nachname='b',
            email='stats-empty@test.local',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(m)
        db.session.flush()
        r = MerchRound(title='SR', marketing_chief_id=m.id)
        db.session.add(r)
        db.session.commit()

        db.session.refresh(r)
        st = compute_round_statistics(r)
        assert st.orders_total == 0
        assert st.gross_rappen == 0


def test_compute_round_statistics_margin_and_supplier_cost(app):
    with app.app_context():
        mc = Member(
            vorname='m',
            nachname='c',
            email='stats-lines@test.local',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        buyer = Member(
            vorname='b',
            nachname='u',
            email='stats-buyer@test.local',
            passwort_hash=generate_password_hash('TestPasswortMind12'),
        )
        db.session.add(mc)
        db.session.add(buyer)
        db.session.flush()

        s = MerchSupplier(name='Sup')
        db.session.add(s)
        db.session.flush()
        art = MerchArticle(name='A', supplier_id=s.id, list_price_rappen=1000)
        db.session.add(art)
        db.session.flush()
        v = MerchVariant(article_id=art.id, attributes={}, is_active=True)
        db.session.add(v)
        db.session.flush()

        r = MerchRound(title='R1', marketing_chief_id=mc.id, subsidy_per_member_rappen=0)
        db.session.add(r)
        db.session.flush()
        ri = MerchRoundItem(
            round_id=r.id,
            variant_id=v.id,
            list_price_snapshot_rappen=1000,
            effective_supplier_price_rappen=400,
            member_price_rappen=1000,
        )
        db.session.add(ri)
        db.session.flush()

        o = MerchOrder(
            round_id=r.id,
            member_id=buyer.id,
            status=MerchOrderStatus.CONFIRMED,
            gross_amount_rappen=2000,
            subsidy_amount_rappen=0,
            member_amount_due_rappen=2000,
        )
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

        db.session.refresh(r)
        st = compute_round_statistics(r)
        assert st.orders_total == 1
        assert st.supplier_cost_complete is True
        assert st.supplier_cost_rappen == 800  # 2 * 400
        assert st.margin_rappen == 1200  # 2 * (1000 - 400)
        assert st.club_net_rappen == st.margin_rappen
