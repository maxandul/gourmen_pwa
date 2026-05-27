"""Merch v2 Bestellrunde: Workflow-Phase und Tabellen-Daten fuer Admin-Detail."""

from __future__ import annotations

from dataclasses import dataclass

from backend.models.merch_v2 import (
    MerchOrder,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchVariant,
)

WORKFLOW_STEP_LABELS: tuple[str, ...] = (
    'Vorbereiten',
    'Bestellungen sammeln',
    'Beim Lieferanten bestellen',
    'Effektive Preise',
    'Beleg',
    'Wareneingang',
    'Verteilung',
    'Abgeschlossen',
)


@dataclass(frozen=True)
class MerchRoundSortimentRow:
    round_item_id: int
    article_name: str
    color_label: str
    size_label: str


@dataclass(frozen=True)
class MerchRoundOrderLineRow:
    member_display: str
    article_label: str
    color_label: str
    size_label: str
    list_price_chf: str
    order_id: int
    member_id: int
    order_line_key: str


@dataclass(frozen=True)
class MerchRoundAggregateRow:
    round_item_id: int
    article_name: str
    color_label: str
    size_label: str
    quantity: int
    supplier_name: str


@dataclass(frozen=True)
class MerchRoundClosedLineRow:
    member_display: str
    article_label: str
    color_label: str
    size_label: str
    supplier_line_chf: str
    member_line_chf: str
    subsidy_chf: str | None
    due_chf: str | None
    order_id: int
    show_order_totals: bool


@dataclass(frozen=True)
class MerchRoundPricingArticleGroup:
    article_id: int
    article_name: str
    items: tuple[MerchRoundItem, ...]
    uniform_pricing: bool


def variant_color_label(variant: MerchVariant) -> str:
    if variant.color and variant.color.label:
        return variant.color.label
    attrs = variant.attributes if isinstance(variant.attributes, dict) else {}
    for key in ('farbe', 'Farbe', 'color'):
        val = attrs.get(key)
        if val:
            return str(val)
    return '—'


def variant_size_label(variant: MerchVariant) -> str:
    if variant.size and variant.size.label:
        return variant.size.label
    attrs = variant.attributes if isinstance(variant.attributes, dict) else {}
    for key in ('groesse', 'Grösse', 'grösse', 'size'):
        val = attrs.get(key)
        if val:
            return str(val)
    return '—'


def _chf_from_rappen(rappen: int | None) -> str:
    if rappen is None:
        return '—'
    return f'{(rappen / 100):.2f}'


def ordered_round_item_ids(round_obj: MerchRound) -> set[int]:
    """Round-Item-IDs mit mindestens einer bestellten Menge."""
    ids: set[int] = set()
    for o in round_obj.orders:
        if o.status in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT):
            continue
        for line in o.order_items:
            if line.quantity > 0:
                ids.add(line.round_item_id)
    return ids


def round_prices_complete(round_obj: MerchRound) -> bool:
    ordered_ids = ordered_round_item_ids(round_obj)
    if not ordered_ids:
        return False
    by_id = {ri.id: ri for ri in round_obj.round_items}
    for item_id in ordered_ids:
        ri = by_id.get(item_id)
        if ri is None or ri.effective_supplier_price_rappen is None:
            return False
    return True


def round_orders_invoiced(round_obj: MerchRound) -> bool:
    active = [
        o
        for o in round_obj.orders
        if o.status not in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT)
    ]
    if not active:
        return False
    for o in active:
        if o.status == MerchOrderStatus.CONFIRMED:
            return False
    return True


def round_invoice_recorded(round_obj: MerchRound) -> bool:
    if round_obj.supplier_invoices:
        return True
    if round_obj.supplier_invoice_drive_file_id:
        return True
    return round_obj.supplier_invoice_total_rappen is not None


def round_beleg_step_complete(round_obj: MerchRound) -> bool:
    return round_obj.supplier_invoice_completed_at is not None


def round_all_picked_up(round_obj: MerchRound) -> bool:
    for o in round_obj.orders:
        if o.status in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT):
            continue
        if o.status in (
            MerchOrderStatus.CONFIRMED,
            MerchOrderStatus.INVOICED,
            MerchOrderStatus.PICKED_UP,
            MerchOrderStatus.PAID,
        ):
            if o.picked_up_at is None:
                return False
    return True


def compute_round_workflow_phase(round_obj: MerchRound) -> int:
    """1–8 fuer WORKFLOW_STEP_LABELS; 0 bei CANCELLED."""
    st = round_obj.status
    if st == MerchRoundStatus.CANCELLED:
        return 0
    if st == MerchRoundStatus.CLOSED:
        return 8
    if st == MerchRoundStatus.DELIVERED:
        return 7
    if st == MerchRoundStatus.ORDERED_AT_SUPPLIER:
        if not round_orders_invoiced(round_obj):
            return 4
        if not round_beleg_step_complete(round_obj):
            return 5
        return 6
    if st == MerchRoundStatus.LOCKED:
        return 3
    if st == MerchRoundStatus.OPEN:
        return 2
    return 1


def workflow_hint(round_obj: MerchRound, *, phase: int, orders_count: int, buyers_count: int) -> str:
    if round_obj.status == MerchRoundStatus.CANCELLED:
        return 'Diese Runde wurde storniert.'
    if phase == 1:
        n = len(round_obj.round_items)
        if n == 0:
            return 'Füge mindestens einen Artikel hinzu, bevor du die Runde öffnest.'
        return f'Sortiment mit {n} Position{"en" if n != 1 else ""} — öffne die Runde für Mitgliederbestellungen.'
    if phase == 2:
        parts = [f'Aktuell {orders_count} Bestellung{"en" if orders_count != 1 else ""} von {buyers_count} Mitglied{"ern" if buyers_count != 1 else ""}.']
        if round_obj.deadline_communicated:
            parts.append(f'Kommunizierte Frist: {round_obj.deadline_communicated.strftime("%d.%m.%Y")}.')
        parts.append('Schliesse die Bestellrunde, wenn die Frist abgelaufen ist.')
        return ' '.join(parts)
    if phase == 3:
        return 'Exportiere die Sammelbestellung und gib sie beim Lieferanten auf. Bestätige danach die Bestellung.'
    if phase == 4:
        ordered_ids = ordered_round_item_ids(round_obj)
        if not ordered_ids:
            return (
                'Es liegen keine bestellten Positionen vor — '
                'ohne Bestellungen können keine Preise erfasst werden.'
            )
        if not round_prices_complete(round_obj):
            return (
                'Trage den fakturierten Lieferantenpreis pro bestellter Position ein. '
                'Member-Preis optional — leer lassen entspricht dem fakturierten Preis '
                '(Endbetrag pro Stück ohne Subvention).'
            )
        return 'Preise vollständig — speichere und berechne die Mitglieder-Forderungen.'
    if phase == 5:
        return 'Lade optional den Lieferantenbeleg hoch und erfasse die Rechnungssumme.'
    if phase == 6:
        return 'Bestätige den Wareneingang, sobald die Lieferung beim Verein angekommen ist.'
    if phase == 7:
        return 'Verteile die Artikel an die Mitglieder (z. B. am Event) und markiere die Auslieferung.'
    return 'Runde abgeschlossen — Übersicht unten.'


def step_back_available(round_obj: MerchRound) -> bool:
    return compute_round_workflow_phase(round_obj) > 1


def round_can_delete(round_obj: MerchRound) -> bool:
    return round_obj.status not in (
        MerchRoundStatus.CANCELLED,
        MerchRoundStatus.CLOSED,
    )


def round_delete_is_hard(round_obj: MerchRound) -> bool:
    return round_obj.status == MerchRoundStatus.DRAFT


def build_sortiment_rows(round_items: list[MerchRoundItem]) -> list[MerchRoundSortimentRow]:
    rows: list[MerchRoundSortimentRow] = []
    for ri in sorted(round_items, key=lambda x: (x.variant.article.name.lower(), x.variant_id)):
        v = ri.variant
        rows.append(
            MerchRoundSortimentRow(
                round_item_id=ri.id,
                article_name=v.article.name,
                color_label=variant_color_label(v),
                size_label=variant_size_label(v),
            )
        )
    return rows


def build_order_line_rows(orders: list[MerchOrder]) -> list[MerchRoundOrderLineRow]:
    rows: list[MerchRoundOrderLineRow] = []
    active = [
        o
        for o in orders
        if o.status not in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT)
    ]
    active.sort(key=lambda o: ((o.member.nachname or '').lower(), (o.member.vorname or '').lower(), o.id))
    for o in active:
        member_display = o.member.display_spirit_rufname
        for line in sorted(o.order_items, key=lambda ln: ln.round_item.variant.article.name.lower()):
            ri = line.round_item
            v = ri.variant
            unit = line.unit_price_at_confirm_rappen or ri.list_price_snapshot_rappen
            rows.append(
                MerchRoundOrderLineRow(
                    member_display=member_display,
                    article_label=f'{line.quantity}× {v.article.name}',
                    color_label=variant_color_label(v),
                    size_label=variant_size_label(v),
                    list_price_chf=_chf_from_rappen(unit),
                    order_id=o.id,
                    member_id=o.member_id,
                    order_line_key=f'{o.id}-{line.id}',
                )
            )
    return rows


def build_distribution_line_rows(orders: list[MerchOrder]) -> list[MerchRoundOrderLineRow]:
    """Wie Bestellübersicht, nur fakturierte/offene Auslieferungen."""
    rows: list[MerchRoundOrderLineRow] = []
    eligible = [
        o
        for o in orders
        if o.status
        in (
            MerchOrderStatus.INVOICED,
            MerchOrderStatus.PICKED_UP,
            MerchOrderStatus.PAID,
        )
        and o.picked_up_at is None
    ]
    eligible.sort(key=lambda o: ((o.member.nachname or '').lower(), (o.member.vorname or '').lower(), o.id))
    for o in eligible:
        member_display = o.member.display_spirit_rufname
        for line in sorted(o.order_items, key=lambda ln: ln.round_item.variant.article.name.lower()):
            ri = line.round_item
            v = ri.variant
            unit = line.unit_price_final_rappen or line.unit_price_at_confirm_rappen or ri.list_price_snapshot_rappen
            rows.append(
                MerchRoundOrderLineRow(
                    member_display=member_display,
                    article_label=f'{line.quantity}× {v.article.name}',
                    color_label=variant_color_label(v),
                    size_label=variant_size_label(v),
                    list_price_chf=_chf_from_rappen(unit),
                    order_id=o.id,
                    member_id=o.member_id,
                    order_line_key=f'{o.id}-{line.id}',
                )
            )
    return rows


def build_aggregate_rows(aggregate: list[tuple[MerchRoundItem, int]]) -> list[MerchRoundAggregateRow]:
    rows: list[MerchRoundAggregateRow] = []
    for ri, qty in aggregate:
        if qty <= 0:
            continue
        v = ri.variant
        sup = v.article.supplier.name if v.article.supplier else '—'
        rows.append(
            MerchRoundAggregateRow(
                round_item_id=ri.id,
                article_name=v.article.name,
                color_label=variant_color_label(v),
                size_label=variant_size_label(v),
                quantity=qty,
                supplier_name=sup,
            )
        )
    return rows


def build_pricing_article_groups(round_items: list[MerchRoundItem]) -> list[MerchRoundPricingArticleGroup]:
    by_article: dict[int, list[MerchRoundItem]] = {}
    for ri in round_items:
        by_article.setdefault(ri.variant.article_id, []).append(ri)
    groups: list[MerchRoundPricingArticleGroup] = []
    for aid in sorted(by_article, key=lambda k: by_article[k][0].variant.article.name.lower()):
        items = tuple(sorted(by_article[aid], key=lambda x: x.variant_id))
        effs = {ri.effective_supplier_price_rappen for ri in items}
        mems = {ri.member_price_rappen for ri in items}
        uniform = len(effs) <= 1 and len(mems) <= 1
        groups.append(
            MerchRoundPricingArticleGroup(
                article_id=aid,
                article_name=items[0].variant.article.name,
                items=items,
                uniform_pricing=uniform,
            )
        )
    return groups


def build_closed_line_rows(orders: list[MerchOrder]) -> list[MerchRoundClosedLineRow]:
    rows: list[MerchRoundClosedLineRow] = []
    active = [
        o
        for o in orders
        if o.status not in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT)
    ]
    active.sort(key=lambda o: ((o.member.nachname or '').lower(), (o.member.vorname or '').lower(), o.id))
    for o in active:
        member_display = o.member.display_spirit_rufname
        subsidy = _chf_from_rappen(o.subsidy_amount_rappen)
        due = _chf_from_rappen(o.member_amount_due_rappen)
        lines = sorted(o.order_items, key=lambda ln: ln.round_item.variant.article.name.lower())
        for idx, line in enumerate(lines):
            ri = line.round_item
            v = ri.variant
            eff = ri.effective_supplier_price_rappen
            mem = (
                line.unit_price_final_rappen
                or ri.member_price_rappen
                or ri.effective_supplier_price_rappen
            )
            rows.append(
                MerchRoundClosedLineRow(
                    member_display=member_display,
                    article_label=f'{line.quantity}× {v.article.name}',
                    color_label=variant_color_label(v),
                    size_label=variant_size_label(v),
                    supplier_line_chf=_chf_from_rappen(eff * line.quantity if eff is not None else None),
                    member_line_chf=_chf_from_rappen(mem * line.quantity if mem is not None else None),
                    subsidy_chf=subsidy if idx == 0 else None,
                    due_chf=due if idx == 0 else None,
                    order_id=o.id,
                    show_order_totals=idx == 0,
                )
            )
    return rows
