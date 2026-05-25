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

    @classmethod
    def cancel_order_by_member(cls, order_id: int, member_id: int) -> dict:
        """Mitglied storniert waehrend Runde OPEN (DRAFT oder CONFIRMED)."""
        o = db.session.get(MerchOrder, order_id)
        if not o or o.member_id != member_id:
            return {'success': False, 'error': 'Bestellung nicht gefunden.'}
        r = o.round
        if r.status != MerchRoundStatus.OPEN:
            return {'success': False, 'error': 'Storno ist nur solange die Runde offen ist moeglich.'}
        if o.status not in (MerchOrderStatus.DRAFT, MerchOrderStatus.CONFIRMED):
            return {'success': False, 'error': 'Diese Bestellung kann nicht mehr storniert werden.'}

        now = datetime.utcnow()
        for line in list(o.order_items):
            db.session.delete(line)
        o.status = MerchOrderStatus.CANCELLED
        o.cancelled_at = now
        o.cancellation_reason = 'Mitglied'
        o.gross_amount_rappen = 0
        o.subsidy_amount_rappen = 0
        o.member_amount_due_rappen = 0
        o.confirmed_at = None
        return {'success': True, 'error': None}

    @classmethod
    def discard_draft_orders_for_round(cls, round_id: int) -> None:
        """OPEN -> LOCKED: nicht bestaetigte Warenkoerbe loeschen."""
        drafts = MerchOrder.query.filter_by(round_id=round_id, status=MerchOrderStatus.DRAFT).all()
        for o in drafts:
            db.session.delete(o)

    @classmethod
    def reset_confirmed_orders_to_draft_for_round(cls, round_id: int) -> None:
        """LOCKED -> OPEN: CONFIRMED zurueck auf DRAFT (Neu-Bestaetigung)."""
        orders = MerchOrder.query.filter_by(round_id=round_id, status=MerchOrderStatus.CONFIRMED).all()
        for o in orders:
            o.status = MerchOrderStatus.DRAFT
            o.confirmed_at = None
            for line in o.order_items:
                ri = line.round_item
                unit = cls._preview_unit_rappen(ri)
                line.unit_price_at_confirm_rappen = unit
                line.unit_price_final_rappen = None
            cls.recalculate_draft_totals(o)

    @classmethod
    def reset_invoiced_orders_to_confirmed_for_round(cls, round_id: int) -> None:
        """Fakturierte Bestellungen zurueck auf bestaetigt (Schritt zurueck vor Beleg)."""
        orders = MerchOrder.query.filter_by(
            round_id=round_id,
            status=MerchOrderStatus.INVOICED,
        ).all()
        for o in orders:
            o.status = MerchOrderStatus.CONFIRMED
            o.invoiced_at = None
            for line in o.order_items:
                line.unit_price_final_rappen = None
            cls.recalculate_draft_totals(o)

    @classmethod
    def reset_pickup_for_round(cls, round_id: int) -> None:
        """Auslieferungs-Markierungen zuruecksetzen (Schritt zurueck vor Verteilung)."""
        orders = (
            MerchOrder.query.filter_by(round_id=round_id)
            .filter(MerchOrder.picked_up_at.isnot(None))
            .all()
        )
        for o in orders:
            o.picked_up_at = None
            o.picked_up_by_member_id = None
            if o.status == MerchOrderStatus.PICKED_UP:
                o.status = MerchOrderStatus.INVOICED

    @classmethod
    def validate_round_items_for_supplier_order(cls, round_obj: MerchRound) -> dict:
        """Alle Rund-Positionen brauchen Effektiv- und Mitgliederpreis (Rappen)."""
        for ri in round_obj.round_items:
            if ri.effective_supplier_price_rappen is None or ri.member_price_rappen is None:
                return {
                    'success': False,
                    'error': 'Jede Sortimentsposition braucht Effektivpreis und Mitgliederpreis.',
                }
            if ri.effective_supplier_price_rappen < 0 or ri.member_price_rappen < 0:
                return {'success': False, 'error': 'Preise duerfen nicht negativ sein.'}
        return {'success': True, 'error': None}

    @classmethod
    def invoice_confirmed_orders_for_round(cls, round_obj: MerchRound) -> dict:
        """
        LOCKED -> ORDERED_AT_SUPPLIER: CONFIRMED -> INVOICED mit definitiven Mitgliederpreisen.
        """
        vr = cls.validate_round_items_for_supplier_order(round_obj)
        if not vr['success']:
            return vr

        now = datetime.utcnow()
        for o in round_obj.orders:
            if o.status != MerchOrderStatus.CONFIRMED:
                continue
            gross = 0
            for line in o.order_items:
                mp = line.round_item.member_price_rappen
                if mp is None:
                    return {
                        'success': False,
                        'error': 'Mitgliederpreis fuer eine Position fehlt.',
                    }
                line.unit_price_final_rappen = mp
                gross += line.quantity * mp
            cap = round_obj.subsidy_per_member_rappen
            sub, due = cls.subsidy_and_member_due_rappen(gross, cap)
            o.gross_amount_rappen = gross
            o.subsidy_amount_rappen = sub
            o.member_amount_due_rappen = due
            o.status = MerchOrderStatus.INVOICED
            o.invoiced_at = now
        return {'success': True, 'error': None}

    @classmethod
    def cancel_active_orders_for_round(cls, round_id: int) -> None:
        """Runde CANCELLED: aktive Orders stornieren; PAID bleibt PAID."""
        now = datetime.utcnow()
        active = (
            MerchOrder.query.filter_by(round_id=round_id)
            .filter(
                MerchOrder.status.in_(
                    (
                        MerchOrderStatus.DRAFT,
                        MerchOrderStatus.CONFIRMED,
                        MerchOrderStatus.INVOICED,
                        MerchOrderStatus.PICKED_UP,
                    )
                )
            )
            .all()
        )
        for o in active:
            o.status = MerchOrderStatus.CANCELLED
            o.cancelled_at = now
            o.cancellation_reason = 'Runde storniert'

    @classmethod
    def mark_picked_up(cls, order_id: int, actor_member_id: int) -> dict:
        """Marketingchef/Admin: Abholung."""
        o = db.session.get(MerchOrder, order_id)
        if not o:
            return {'success': False, 'error': 'Bestellung nicht gefunden.'}
        if o.status == MerchOrderStatus.CANCELLED:
            return {'success': False, 'error': 'Bestellung ist storniert.'}
        if o.status == MerchOrderStatus.DRAFT or o.status == MerchOrderStatus.CONFIRMED:
            return {'success': False, 'error': 'Bestellung ist noch nicht fakturiert.'}

        now = datetime.utcnow()
        o.picked_up_at = now
        o.picked_up_by_member_id = actor_member_id
        if o.status == MerchOrderStatus.INVOICED:
            o.status = MerchOrderStatus.PICKED_UP
        elif o.status == MerchOrderStatus.PAID:
            pass
        return {'success': True, 'error': None}

    @classmethod
    def mark_paid(cls, order_id: int, actor_member_id: int) -> dict:
        """Marketingchef/Schatzmeister/Admin: Bezahlt."""
        o = db.session.get(MerchOrder, order_id)
        if not o:
            return {'success': False, 'error': 'Bestellung nicht gefunden.'}
        if o.status == MerchOrderStatus.CANCELLED:
            return {'success': False, 'error': 'Bestellung ist storniert.'}
        if o.status == MerchOrderStatus.DRAFT or o.status == MerchOrderStatus.CONFIRMED:
            return {'success': False, 'error': 'Bestellung ist noch nicht fakturiert.'}

        now = datetime.utcnow()
        o.paid_at = now
        o.paid_by_member_id = actor_member_id
        o.status = MerchOrderStatus.PAID
        return {'success': True, 'error': None}

    @classmethod
    def round_ready_for_auto_close(cls, round_obj: MerchRound) -> bool:
        """Alle nicht-stornierten fakturierten Orders sind abgeholt."""
        if round_obj.status != MerchRoundStatus.DELIVERED:
            return False
        for o in round_obj.orders:
            if o.status == MerchOrderStatus.CANCELLED:
                continue
            if o.status in (
                MerchOrderStatus.DRAFT,
                MerchOrderStatus.CONFIRMED,
            ):
                continue
            if o.picked_up_at is None:
                return False
        return True

    @classmethod
    def mark_all_distributed_for_round(cls, round_obj: MerchRound, actor_member_id: int) -> dict:
        """Alle fakturierten, noch nicht abgeholten Orders als verteilt markieren."""
        touched = 0
        for o in round_obj.orders:
            if o.status not in (
                MerchOrderStatus.INVOICED,
                MerchOrderStatus.PICKED_UP,
                MerchOrderStatus.PAID,
            ):
                continue
            if o.picked_up_at is not None:
                continue
            res = cls.mark_picked_up(o.id, actor_member_id)
            if not res['success']:
                return res
            touched += 1
        return {'success': True, 'error': None, 'touched': touched}
