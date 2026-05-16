"""Merch v2 Kennzahlen fuer Runden-Detail und Vereinsjahresauswertung.

Spec: docs/capabilities/merch.md Sektion 14.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func

from backend.extensions import db
from backend.models.merch_v2 import (
    MerchArticle,
    MerchOrder,
    MerchOrderItem,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchVariant,
)

FINANCIAL_ORDER_STATUSES = frozenset(
    {MerchOrderStatus.INVOICED, MerchOrderStatus.PICKED_UP, MerchOrderStatus.PAID}
)


@dataclass(frozen=True)
class RoundStatistics:
    orders_total: int
    buyers_distinct: int
    gross_rappen: int
    subsidy_rappen: int
    supplier_cost_rappen: int
    margin_rappen: int
    club_net_rappen: int
    supplier_cost_complete: bool
    financial_orders_count: int
    paid_orders: int
    unpaid_orders_post_invoice: int
    picked_orders: int
    unpicked_financial_orders: int


@dataclass(frozen=True)
class YearOverview:
    season_label_year: int
    rounds_count: int
    round_ids: tuple[int, ...]
    orders_active_count: int
    buyers_distinct: int
    gross_rappen: int
    subsidy_rappen: int
    supplier_cost_rappen: int
    margin_rappen: int
    club_net_rappen: int
    subsidy_by_round_title: tuple[tuple[str, int], ...]
    supplier_cost_aggregate_complete: bool


def current_club_season_label_year(ref: datetime | None = None) -> int:
    d = ref or datetime.utcnow()
    if d.month >= 9:
        return d.year
    return d.year - 1


def club_season_utc_bounds(season_label_year: int) -> tuple[datetime, datetime]:
    start = datetime(season_label_year, 9, 1)
    end = datetime(season_label_year + 1, 8, 31, 23, 59, 59)
    return start, end


def compute_round_statistics(round_obj: MerchRound) -> RoundStatistics:
    active = [
        o
        for o in round_obj.orders
        if o.status not in (MerchOrderStatus.DRAFT, MerchOrderStatus.CANCELLED)
    ]
    orders_total = len(active)
    buyers_distinct = len({o.member_id for o in active})
    gross_rappen = sum((o.gross_amount_rappen or 0) for o in active)
    subsidy_rappen = sum((o.subsidy_amount_rappen or 0) for o in active)

    supplier_cost_rappen = 0
    margin_rappen = 0
    supplier_complete = True

    for o in active:
        for line in o.order_items:
            ri = line.round_item
            eff = ri.effective_supplier_price_rappen
            unit_mem = (
                line.unit_price_final_rappen
                if line.unit_price_final_rappen is not None
                else line.unit_price_at_confirm_rappen
            )
            if eff is None:
                supplier_complete = False
                continue
            supplier_cost_rappen += line.quantity * eff
            margin_rappen += line.quantity * (unit_mem - eff)

    club_net_rappen = margin_rappen - subsidy_rappen

    financial = [o for o in active if o.status in FINANCIAL_ORDER_STATUSES]
    fo = len(financial)
    paid_orders = sum(1 for o in financial if o.status == MerchOrderStatus.PAID)
    unpaid_orders_post_invoice = fo - paid_orders
    picked_orders = sum(1 for o in financial if o.picked_up_at is not None)
    unpicked_financial_orders = fo - picked_orders

    return RoundStatistics(
        orders_total=orders_total,
        buyers_distinct=buyers_distinct,
        gross_rappen=gross_rappen,
        subsidy_rappen=subsidy_rappen,
        supplier_cost_rappen=supplier_cost_rappen,
        margin_rappen=margin_rappen,
        club_net_rappen=club_net_rappen,
        supplier_cost_complete=supplier_complete,
        financial_orders_count=fo,
        paid_orders=paid_orders,
        unpaid_orders_post_invoice=unpaid_orders_post_invoice,
        picked_orders=picked_orders,
        unpicked_financial_orders=unpicked_financial_orders,
    )


def rounds_for_club_season(season_label_year: int) -> list[MerchRound]:
    start, end = club_season_utc_bounds(season_label_year)
    ts = func.coalesce(MerchRound.opened_at, MerchRound.created_at)
    return MerchRound.query.filter(ts >= start, ts <= end).order_by(MerchRound.id.asc()).all()


def build_year_overview(season_label_year: int) -> YearOverview:
    rounds = rounds_for_club_season(season_label_year)
    gross = subsidy = supplier = margin = 0
    aggregate_complete = True
    buyers: set[int] = set()
    orders_n = 0
    subsidy_rows: list[tuple[str, int]] = []
    ids: list[int] = []

    for r in rounds:
        ids.append(r.id)
        st = compute_round_statistics(r)
        gross += st.gross_rappen
        subsidy += st.subsidy_rappen
        supplier += st.supplier_cost_rappen
        margin += st.margin_rappen
        if not st.supplier_cost_complete:
            aggregate_complete = False
        subsidy_rows.append((r.title, st.subsidy_rappen))
        for o in r.orders:
            if o.status in (MerchOrderStatus.DRAFT, MerchOrderStatus.CANCELLED):
                continue
            buyers.add(o.member_id)
            orders_n += 1

    return YearOverview(
        season_label_year=season_label_year,
        rounds_count=len(rounds),
        round_ids=tuple(ids),
        orders_active_count=orders_n,
        buyers_distinct=len(buyers),
        gross_rappen=gross,
        subsidy_rappen=subsidy,
        supplier_cost_rappen=supplier,
        margin_rappen=margin,
        club_net_rappen=margin - subsidy,
        subsidy_by_round_title=tuple(subsidy_rows),
        supplier_cost_aggregate_complete=aggregate_complete,
    )


def top_articles_by_quantity_for_round_ids(
    round_ids: tuple[int, ...],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not round_ids:
        return []
    rows = (
        db.session.query(
            MerchArticle.id,
            MerchArticle.name,
            func.sum(MerchOrderItem.quantity).label('qty'),
        )
        .select_from(MerchOrderItem)
        .join(MerchOrder, MerchOrderItem.order_id == MerchOrder.id)
        .join(MerchRoundItem, MerchOrderItem.round_item_id == MerchRoundItem.id)
        .join(MerchVariant, MerchRoundItem.variant_id == MerchVariant.id)
        .join(MerchArticle, MerchVariant.article_id == MerchArticle.id)
        .filter(
            MerchOrder.round_id.in_(round_ids),
            MerchOrder.status.notin_((MerchOrderStatus.DRAFT, MerchOrderStatus.CANCELLED)),
        )
        .group_by(MerchArticle.id, MerchArticle.name)
        .order_by(func.sum(MerchOrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [{'article_id': r[0], 'name': r[1], 'quantity': int(r[2])} for r in rows]


def top_articles_by_margin_for_round_ids(
    round_ids: tuple[int, ...],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not round_ids:
        return []
    unit = func.coalesce(
        MerchOrderItem.unit_price_final_rappen,
        MerchOrderItem.unit_price_at_confirm_rappen,
    )
    line_margin = MerchOrderItem.quantity * (unit - MerchRoundItem.effective_supplier_price_rappen)
    rows = (
        db.session.query(
            MerchArticle.id,
            MerchArticle.name,
            func.sum(line_margin).label('marg'),
        )
        .select_from(MerchOrderItem)
        .join(MerchOrder, MerchOrderItem.order_id == MerchOrder.id)
        .join(MerchRoundItem, MerchOrderItem.round_item_id == MerchRoundItem.id)
        .join(MerchVariant, MerchRoundItem.variant_id == MerchVariant.id)
        .join(MerchArticle, MerchVariant.article_id == MerchArticle.id)
        .filter(
            MerchOrder.round_id.in_(round_ids),
            MerchOrder.status.notin_((MerchOrderStatus.DRAFT, MerchOrderStatus.CANCELLED)),
            MerchRoundItem.effective_supplier_price_rappen.is_not(None),
        )
        .group_by(MerchArticle.id, MerchArticle.name)
        .order_by(func.sum(line_margin).desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append({'article_id': r[0], 'name': r[1], 'margin_rappen': int(r[2])})
    return out
