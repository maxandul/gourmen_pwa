"""Merch v2 Bestellrunden (Lifecycle). Orchestration folgt in spaeteren Schritten."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import joinedload

from backend.extensions import db
from backend.models.merch_v2 import (
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchVariant,
)
from backend.services.merch_sortiment_service import MerchSortimentService


class MerchRoundService:
    """Validierung und Status-Uebergaenge (ergaenzen wenn Routes anbinden)."""

    #: Vorwaerts-Kanten ohne explizites CANCELLED (siehe `is_forward_transition`).
    _FORWARD: dict[MerchRoundStatus, frozenset[MerchRoundStatus]] = {
        MerchRoundStatus.DRAFT: frozenset({MerchRoundStatus.OPEN}),
        MerchRoundStatus.OPEN: frozenset({MerchRoundStatus.LOCKED}),
        MerchRoundStatus.LOCKED: frozenset(
            {
                MerchRoundStatus.OPEN,
                MerchRoundStatus.ORDERED_AT_SUPPLIER,
            }
        ),
        MerchRoundStatus.ORDERED_AT_SUPPLIER: frozenset({MerchRoundStatus.DELIVERED}),
        MerchRoundStatus.DELIVERED: frozenset({MerchRoundStatus.CLOSED}),
        MerchRoundStatus.CLOSED: frozenset(),
        MerchRoundStatus.CANCELLED: frozenset(),
    }

    @classmethod
    def is_forward_transition(cls, current: MerchRoundStatus, target: MerchRoundStatus) -> bool:
        if current == target:
            return True
        if target == MerchRoundStatus.CANCELLED:
            return current not in (
                MerchRoundStatus.CLOSED,
                MerchRoundStatus.CANCELLED,
            )
        return target in cls._FORWARD.get(current, frozenset())

    @classmethod
    def create_draft_round(
        cls,
        *,
        title: str,
        marketing_chief_id: int,
        description: str | None = None,
        deadline_communicated=None,
        subsidy_per_member_rappen: int = 0,
    ) -> dict:
        """Legt eine Runde in `DRAFT` an (Caller macht `commit`)."""
        title_clean = (title or '').strip()
        if not title_clean:
            return {'success': False, 'error': 'Titel fehlt.', 'round': None}
        if subsidy_per_member_rappen < 0:
            return {'success': False, 'error': 'Subvention darf nicht negativ sein.', 'round': None}

        r = MerchRound(
            title=title_clean[:200],
            description=(description or '').strip() or None,
            status=MerchRoundStatus.DRAFT,
            deadline_communicated=deadline_communicated,
            subsidy_per_member_rappen=subsidy_per_member_rappen,
            marketing_chief_id=marketing_chief_id,
        )
        db.session.add(r)
        db.session.flush()
        return {'success': True, 'error': None, 'round': r}

    @classmethod
    def apply_transition(
        cls,
        round_obj: MerchRound,
        target: MerchRoundStatus,
        *,
        cancellation_reason: str | None = None,
    ) -> dict:
        """
        Setzt neuen Status wenn erlaubt; aktualisiert Zeitstempel.
        Caller macht `commit`. Bei Fehler keine Aenderung am Objekt.
        """
        if target == MerchRoundStatus.CANCELLED:
            reason = (cancellation_reason or '').strip()
            if not reason:
                return {'success': False, 'error': 'Storno ist nur mit Begruendung moeglich.'}

        if not cls.is_forward_transition(round_obj.status, target):
            return {'success': False, 'error': 'Statusuebergang ist nicht erlaubt.'}

        if target == MerchRoundStatus.OPEN:
            if MerchRoundItem.query.filter_by(round_id=round_obj.id).count() == 0:
                return {
                    'success': False,
                    'error': 'Mindestens eine Sortimentsposition ist noetig.',
                }

        now = datetime.utcnow()
        round_obj.status = target
        if target == MerchRoundStatus.OPEN:
            round_obj.opened_at = now
        elif target == MerchRoundStatus.LOCKED:
            round_obj.locked_at = now
        elif target == MerchRoundStatus.ORDERED_AT_SUPPLIER:
            round_obj.ordered_at = now
        elif target == MerchRoundStatus.DELIVERED:
            round_obj.delivered_at = now
        elif target == MerchRoundStatus.CLOSED:
            round_obj.closed_at = now
        elif target == MerchRoundStatus.CANCELLED:
            round_obj.cancelled_at = now
            round_obj.cancellation_reason = (cancellation_reason or '').strip()

        return {'success': True, 'error': None}

    @classmethod
    def add_variant_to_round(cls, round_id: int, variant_id: int) -> dict:
        """
        Erzeugt MerchRoundItem mit Listenpreis-Snapshot.
        Nur bei Status DRAFT. Caller macht commit.
        """
        r = db.session.get(MerchRound, round_id)
        if not r:
            return {'success': False, 'error': 'Runde nicht gefunden.', 'item': None}
        if r.status != MerchRoundStatus.DRAFT:
            return {
                'success': False,
                'error': 'Sortiment ist nur bei Entwurf-Runden aenderbar.',
                'item': None,
            }

        v = (
            MerchVariant.query.options(joinedload(MerchVariant.article))
            .filter_by(id=variant_id)
            .first()
        )
        if not v:
            return {'success': False, 'error': 'Variante nicht gefunden.', 'item': None}
        art = v.article
        if art.is_archived:
            return {'success': False, 'error': 'Artikel ist archiviert.', 'item': None}
        if not v.is_active:
            return {'success': False, 'error': 'Variante ist deaktiviert.', 'item': None}

        dup = MerchRoundItem.query.filter_by(round_id=round_id, variant_id=variant_id).first()
        if dup:
            return {'success': False, 'error': 'Variante ist bereits in dieser Runde.', 'item': None}

        snap = MerchSortimentService.list_price_rappen_for_variant(art, v)
        item = MerchRoundItem(
            round_id=round_id,
            variant_id=variant_id,
            list_price_snapshot_rappen=snap,
        )
        db.session.add(item)
        db.session.flush()
        return {'success': True, 'error': None, 'item': item}

    @classmethod
    def remove_round_item(cls, round_id: int, round_item_id: int) -> dict:
        """Entfernt eine Position aus der Runde. Nur DRAFT."""
        r = db.session.get(MerchRound, round_id)
        if not r:
            return {'success': False, 'error': 'Runde nicht gefunden.'}
        if r.status != MerchRoundStatus.DRAFT:
            return {'success': False, 'error': 'Sortiment ist nur bei Entwurf-Runden aenderbar.'}

        item = MerchRoundItem.query.filter_by(id=round_item_id, round_id=round_id).first()
        if not item:
            return {'success': False, 'error': 'Position nicht gefunden.'}

        db.session.delete(item)
        return {'success': True, 'error': None}
