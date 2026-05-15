"""Merch v2 Mitgliedsbestellungen (Warenkorb, Bestaetigung, Subvention)."""

from __future__ import annotations

from datetime import datetime

from backend.extensions import db
from backend.models.merch_v2 import (
    MerchOrder,
    MerchOrderItem,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
)


class MerchOrderService:
    """Gemaess docs/capabilities/merch.md Sektion 7 (Preise, Subvention)."""

    @staticmethod
    def subsidy_and_member_due_rappen(
        gross_amount_rappen: int,
        subsidy_cap_per_member_rappen: int,
    ) -> tuple[int, int]:
        """
        Subvention = min(Subventionscap pro Mitglied, Bruttobetrag).
        Forderung = Brutto - Subvention (nie negativ bei gueltigen Eingaben).
        """
        cap = max(0, subsidy_cap_per_member_rappen)
        gross = max(0, gross_amount_rappen)
        subsidy = min(cap, gross)
        member_due = gross - subsidy
        return subsidy, member_due

    @classmethod
    def _preview_unit_rappen(cls, ri: MerchRoundItem) -> int:
        if ri.member_price_rappen is not None:
            return ri.member_price_rappen
        return ri.list_price_snapshot_rappen

    @classmethod
    def recalculate_draft_totals(cls, order: MerchOrder) -> None:
        gross = 0
        for line in order.order_items:
            gross += line.quantity * line.unit_price_at_confirm_rappen
        cap = order.round.subsidy_per_member_rappen
        sub, due = cls.subsidy_and_member_due_rappen(gross, cap)
        order.gross_amount_rappen = gross
        order.subsidy_amount_rappen = sub
        order.member_amount_due_rappen = due

    @classmethod
    def get_or_create_draft_order(cls, round_id: int, member_id: int) -> dict:
        """Liefert Bestellung fuer diese Runde; editable nur bei DRAFT und OPEN."""
        r = db.session.get(MerchRound, round_id)
        if not r:
            return {'success': False, 'error': 'Runde nicht gefunden.', 'order': None, 'editable': False}

        if r.status != MerchRoundStatus.OPEN:
            return {
                'success': False,
                'error': 'In dieser Runde sind keine Bestellungen mehr moeglich.',
                'order': None,
                'editable': False,
            }

        o = MerchOrder.query.filter_by(round_id=round_id, member_id=member_id).first()
        if o:
            if o.status == MerchOrderStatus.CANCELLED:
                return {
                    'success': False,
                    'error': 'Deine Bestellung in dieser Runde wurde storniert.',
                    'order': None,
                    'editable': False,
                }
            editable = o.status == MerchOrderStatus.DRAFT and r.status == MerchRoundStatus.OPEN
            return {'success': True, 'error': None, 'order': o, 'editable': editable}

        o = MerchOrder(
            round_id=round_id,
            member_id=member_id,
            status=MerchOrderStatus.DRAFT,
        )
        db.session.add(o)
        db.session.flush()
        return {'success': True, 'error': None, 'order': o, 'editable': True}

    @classmethod
    def set_cart_line(
        cls,
        order_id: int,
        member_id: int,
        round_item_id: int,
        quantity: int,
    ) -> dict:
        """Setzt Menge fuer eine Rund-Position (0 entfernt Zeile). Nur DRAFT + OPEN."""
        o = db.session.get(MerchOrder, order_id)
        if not o or o.member_id != member_id:
            return {'success': False, 'error': 'Bestellung nicht gefunden.'}
        if o.status != MerchOrderStatus.DRAFT:
            return {'success': False, 'error': 'Warenkorb ist nicht mehr aenderbar.'}

        r = o.round
        if r.status != MerchRoundStatus.OPEN:
            return {'success': False, 'error': 'Runde ist nicht offen.'}

        ri = MerchRoundItem.query.filter_by(id=round_item_id, round_id=o.round_id).first()
        if not ri:
            return {'success': False, 'error': 'Position nicht in dieser Runde.'}

        qty = max(0, int(quantity))
        unit = cls._preview_unit_rappen(ri)

        line = MerchOrderItem.query.filter_by(order_id=order_id, round_item_id=round_item_id).first()
        if qty == 0:
            if line:
                db.session.delete(line)
            db.session.flush()
            db.session.expire(o, ['order_items'])
            if not o.order_items:
                o.gross_amount_rappen = 0
                o.subsidy_amount_rappen = 0
                o.member_amount_due_rappen = 0
            else:
                cls.recalculate_draft_totals(o)
            return {'success': True, 'error': None}

        if not line:
            line = MerchOrderItem(
                order_id=order_id,
                round_item_id=round_item_id,
                quantity=qty,
                unit_price_at_confirm_rappen=unit,
            )
            db.session.add(line)
        else:
            line.quantity = qty
            line.unit_price_at_confirm_rappen = unit

        cls.recalculate_draft_totals(o)
        return {'success': True, 'error': None}

    @classmethod
    def confirm_order(cls, order_id: int, member_id: int) -> dict:
        """DRAFT -> CONFIRMED, Preise aus Rund-Position (Memberpreis oder Snapshot)."""
        o = db.session.get(MerchOrder, order_id)
        if not o or o.member_id != member_id:
            return {'success': False, 'error': 'Bestellung nicht gefunden.'}
        if o.status != MerchOrderStatus.DRAFT:
            return {'success': False, 'error': 'Bestellung ist bereits bestaetigt oder nicht mehr offen.'}

        r = o.round
        if r.status != MerchRoundStatus.OPEN:
            return {'success': False, 'error': 'Runde ist nicht mehr offen fuer Bestellungen.'}

        if not o.order_items:
            return {'success': False, 'error': 'Warenkorb ist leer.'}

        for line in o.order_items:
            ri = line.round_item
            unit = cls._preview_unit_rappen(ri)
            line.unit_price_at_confirm_rappen = unit

        cls.recalculate_draft_totals(o)
        o.status = MerchOrderStatus.CONFIRMED
        o.confirmed_at = datetime.utcnow()
        return {'success': True, 'error': None}
