"""Merch v2 Member-Shop: Workflow-Phase und Hinweise (4 Schritte)."""

from __future__ import annotations

from backend.models.merch_v2 import (
    MerchOrder,
    MerchOrderStatus,
    MerchRound,
    MerchRoundStatus,
)

MEMBER_WORKFLOW_STEP_LABELS: tuple[str, ...] = (
    'Bestellen',
    'Eingereicht, Preise folgen',
    'Bezahlen',
    'Abgeschlossen',
)


def compute_member_workflow_phase(
    round_obj: MerchRound,
    order: MerchOrder | None,
) -> int:
    """1–4 fuer MEMBER_WORKFLOW_STEP_LABELS; 0 bei Storno oder ohne Beteiligung."""
    if round_obj.status == MerchRoundStatus.CANCELLED:
        return 0
    if order is not None and order.status == MerchOrderStatus.CANCELLED:
        return 0

    if order is not None and order.status == MerchOrderStatus.PAID:
        return 4

    if order is not None and order.status == MerchOrderStatus.PICKED_UP:
        return 4

    if order is not None and order.status == MerchOrderStatus.INVOICED:
        return 3

    if order is not None and order.status == MerchOrderStatus.CONFIRMED:
        return 2

    if round_obj.status == MerchRoundStatus.OPEN:
        return 1

    return 0


def member_workflow_status_label(phase: int) -> str:
    if phase <= 0 or phase > len(MEMBER_WORKFLOW_STEP_LABELS):
        return '—'
    return MEMBER_WORKFLOW_STEP_LABELS[phase - 1]


def member_workflow_hint(
    round_obj: MerchRound,
    order: MerchOrder | None,
    *,
    phase: int,
) -> str:
    if round_obj.status == MerchRoundStatus.CANCELLED:
        return 'Diese Bestellrunde wurde storniert.'
    if order is not None and order.status == MerchOrderStatus.CANCELLED:
        return 'Deine Bestellung in dieser Runde wurde storniert.'

    if phase == 0:
        if round_obj.status == MerchRoundStatus.OPEN:
            return 'Wähle deine Artikel und bestätige die Bestellung.'
        return 'Du hast in dieser Runde nicht bestellt.'

    if phase == 1:
        parts = [
            'Wähle pro Artikel die Ausführung und Menge, dann bestätige deine Bestellung.',
        ]
        if round_obj.deadline_communicated:
            parts.append(
                f'Frist: {round_obj.deadline_communicated.strftime("%d.%m.%Y")}.'
            )
        return ' '.join(parts)

    if phase == 2:
        if round_obj.status == MerchRoundStatus.OPEN:
            parts = [
                'Deine Bestellung ist eingereicht. Die Bestellrunde ist noch offen — '
                'du kannst deine Bestellung noch anpassen.',
            ]
            if round_obj.deadline_communicated:
                parts.append(
                    f'Frist: {round_obj.deadline_communicated.strftime("%d.%m.%Y")}.'
                )
            return ' '.join(parts)
        return (
            'Die Bestellrunde wurde geschlossen. Sobald die effektiven Preise feststehen, '
            'siehst du den Endbetrag hier.'
        )

    if phase == 3:
        due = (order.member_amount_due_rappen or 0) if order else 0
        return (
            f'Bitte bezahle CHF {(due / 100):.2f} '
            '(Details erhältst du vom Marketingchef).'
        )

    if phase == 4:
        if order is not None and order.status == MerchOrderStatus.PAID:
            return 'Bezahlt — der Marketingchef verteilt die Artikel am Event.'
        if order is not None and order.status == MerchOrderStatus.PICKED_UP:
            due = order.member_amount_due_rappen or 0
            if due > 0:
                return (
                    f'Deine Artikel wurden verteilt. Offener Betrag: CHF {(due / 100):.2f} '
                    '(Details erhältst du vom Marketingchef).'
                )
            return 'Deine Artikel wurden verteilt.'
        return 'Abgeschlossen.'

    return ''


def member_step_back_available(
    round_obj: MerchRound,
    order: MerchOrder | None,
    *,
    phase: int,
) -> bool:
    if order is None or order.status == MerchOrderStatus.CANCELLED:
        return False
    if phase == 2:
        return (
            round_obj.status == MerchRoundStatus.OPEN
            and order.status == MerchOrderStatus.CONFIRMED
        )
    return False


def member_order_delete_available(
    round_obj: MerchRound,
    order: MerchOrder | None,
) -> bool:
    if order is None or order.status == MerchOrderStatus.CANCELLED:
        return False
    return (
        round_obj.status == MerchRoundStatus.OPEN
        and order.status in (MerchOrderStatus.DRAFT, MerchOrderStatus.CONFIRMED)
    )
