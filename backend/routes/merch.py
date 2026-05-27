"""Merch v2 Routes (Shop, Warenkorb, Bild-Proxy). Feature-Flag: MERCH_V2_ENABLED."""

from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, Response, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from backend.extensions import db, limiter
from backend.models.merch_v2 import (
    MerchOrder,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchVariant,
)
from backend.routes.merch_access import require_merch_v2_enabled
from backend.services.merch_image_service import MerchImageService
from backend.services.merch_member_workflow import (
    MEMBER_WORKFLOW_STEP_LABELS,
    compute_member_workflow_phase,
    member_order_delete_available,
    member_step_back_available,
    member_workflow_hint,
)
from backend.services.merch_order_service import MerchOrderService
from backend.services.security import SecurityService
from backend.models.audit_event import AuditAction

bp = Blueprint('merch', __name__)


@bp.route('/', methods=['GET'])
@login_required
def shop_index():
    """Mitgliedsshop-Uebersicht (Merch v2)."""
    require_merch_v2_enabled()
    shop_rows = MerchOrderService.build_member_shop_index_rows(current_user.id)
    return render_template(
        'merch/shop.html',
        shop_rows=shop_rows,
    )


def _round_shop_variant_sort_key(variant: MerchVariant) -> tuple:
    c_ord = variant.color.sort_order if variant.color else 10_000
    c_lbl = (variant.color.label or '').lower() if variant.color else ''
    s_ord = variant.size.sort_order if variant.size else 10_000
    s_lbl = (variant.size.label or '').lower() if variant.size else ''
    return (c_ord, c_lbl, s_ord, s_lbl, variant.id)


def _shop_article_groups(round_obj: MerchRound) -> list[tuple]:
    buckets: dict[int, list] = defaultdict(list)
    for ri in round_obj.round_items:
        buckets[ri.variant.article_id].append(ri)
    ordered_aids = sorted(
        buckets.keys(),
        key=lambda aid: (buckets[aid][0].variant.article.name or '').lower(),
    )
    out: list[tuple] = []
    for aid in ordered_aids:
        rows = buckets[aid]
        art = rows[0].variant.article
        rows_sorted = sorted(
            rows,
            key=lambda r: _round_shop_variant_sort_key(r.variant),
        )
        out.append((art, rows_sorted))
    return out


def _round_shop_default_item_id_for_config(
    items: list[MerchRoundItem], qty_by_ri: dict[int, int]
) -> int:
    """Erste Rundeneinlage mit Warenbestand im Entwurf, sonst erste Option (Sortierreihenfolge)."""
    for ri in items:
        if qty_by_ri.get(ri.id, 0) > 0:
            return ri.id
    return items[0].id


def _round_shop_preferred_item_ids(
    groups: list[tuple],
    qty_by_ri: dict[int, int],
) -> dict[int, int]:
    return {
        article.id: _round_shop_default_item_id_for_config(ris, qty_by_ri)
        for article, ris in groups
    }


@bp.route('/rounds/<int:round_id>', methods=['GET'])
@login_required
def round_shop(round_id: int):
    require_merch_v2_enabled()
    r = (
        MerchRound.query.options(
            joinedload(MerchRound.round_items)
            .joinedload(MerchRoundItem.variant)
            .options(
                joinedload(MerchVariant.article),
                joinedload(MerchVariant.color),
                joinedload(MerchVariant.size),
            ),
        )
        .filter_by(id=round_id)
        .first_or_404()
    )

    shop_article_groups = _shop_article_groups(r)
    order = None
    editable = False
    qty_by_ri: dict[int, int] = {}
    cart_blocked_reason: str | None = None

    if r.status == MerchRoundStatus.OPEN:
        res = MerchOrderService.get_or_create_draft_order(round_id, current_user.id)
        if res['success']:
            oid = res['order'].id
            db.session.commit()
            order = (
                MerchOrder.query.options(joinedload(MerchOrder.order_items))
                .filter_by(id=oid)
                .first()
            )
            editable = res['editable']
            if order:
                qty_by_ri = {li.round_item_id: li.quantity for li in order.order_items}
        else:
            cart_blocked_reason = res.get('error')
    else:
        order = (
            MerchOrder.query.options(joinedload(MerchOrder.order_items))
            .filter_by(round_id=round_id, member_id=current_user.id)
            .first()
        )
        if order:
            qty_by_ri = {li.round_item_id: li.quantity for li in order.order_items}

    preferred_round_item_id = _round_shop_preferred_item_ids(
        shop_article_groups, qty_by_ri
    )

    workflow_phase = compute_member_workflow_phase(r, order)
    workflow_hint_text = member_workflow_hint(r, order, phase=workflow_phase)
    step_back_available = member_step_back_available(r, order, phase=workflow_phase)
    order_delete_available = member_order_delete_available(r, order)

    return render_template(
        'merch/round_shop.html',
        round=r,
        shop_article_groups=shop_article_groups,
        preferred_round_item_id=preferred_round_item_id,
        order=order,
        editable=editable,
        qty_by_ri=qty_by_ri,
        cart_blocked_reason=cart_blocked_reason,
        MerchRoundStatus=MerchRoundStatus,
        workflow_phase=workflow_phase,
        workflow_step_labels=MEMBER_WORKFLOW_STEP_LABELS,
        workflow_hint_text=workflow_hint_text,
        step_back_available=step_back_available,
        order_delete_available=order_delete_available,
    )


@bp.route('/rounds/<int:round_id>/cart', methods=['POST'])
@login_required
@limiter.limit('120 per minute', methods=['POST'])
def round_cart(round_id: int):
    require_merch_v2_enabled()
    round_item_id = request.form.get('round_item_id', type=int)
    qty = request.form.get('quantity', type=int, default=0)
    if round_item_id is None:
        flash('Ungueltige Position.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    res_o = MerchOrderService.get_or_create_draft_order(round_id, current_user.id)
    if not res_o['success'] or not res_o.get('order'):
        db.session.rollback()
        flash(res_o.get('error') or 'Warenkorb nicht verfuegbar.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    if not MerchOrderService.member_cart_editable(res_o['order']):
        db.session.rollback()
        flash('Warenkorb ist nicht mehr aenderbar.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    oid = res_o['order'].id
    was_confirmed = res_o['order'].status == MerchOrderStatus.CONFIRMED
    result = MerchOrderService.set_cart_line(oid, current_user.id, round_item_id, qty)
    if result['success']:
        db.session.commit()
        if was_confirmed:
            flash('Bestellung zur Bearbeitung geöffnet — bitte erneut bestätigen.', 'info')
        else:
            flash('Warenkorb aktualisiert.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktualisierung fehlgeschlagen.', 'error')
    return redirect(url_for('merch.round_shop', round_id=round_id))


@bp.route('/rounds/<int:round_id>/confirm', methods=['POST'])
@login_required
@limiter.limit('30 per minute', methods=['POST'])
def round_confirm(round_id: int):
    require_merch_v2_enabled()
    res_o = MerchOrderService.get_or_create_draft_order(round_id, current_user.id)
    if not res_o['success'] or not res_o.get('editable'):
        db.session.rollback()
        flash(res_o.get('error') or 'Bestellung nicht moeglich.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    oid = res_o['order'].id
    result = MerchOrderService.confirm_order(oid, current_user.id)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ORDER_CONFIRMED, 'merch_order', oid
        )
        flash('Bestellung bestaetigt.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Bestellung fehlgeschlagen.', 'error')
    return redirect(url_for('merch.round_shop', round_id=round_id))


@bp.route('/rounds/<int:round_id>/step-back', methods=['POST'])
@login_required
@limiter.limit('30 per minute', methods=['POST'])
def round_step_back(round_id: int):
    require_merch_v2_enabled()
    o = MerchOrder.query.filter_by(round_id=round_id, member_id=current_user.id).first()
    if not o:
        flash('Keine Bestellung in dieser Runde.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    result = MerchOrderService.revert_member_workflow_step(o.id, current_user.id)
    if result['success']:
        db.session.commit()
        flash('Zurück zum vorherigen Schritt.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht möglich.', 'error')
    return redirect(url_for('merch.round_shop', round_id=round_id))


@bp.route('/rounds/<int:round_id>/delete-order', methods=['POST'])
@login_required
@limiter.limit('30 per minute', methods=['POST'])
def round_delete_order(round_id: int):
    require_merch_v2_enabled()
    o = MerchOrder.query.filter_by(round_id=round_id, member_id=current_user.id).first()
    if not o:
        flash('Keine Bestellung in dieser Runde.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    result = MerchOrderService.cancel_order_by_member(o.id, current_user.id)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ORDER_CANCELLED, 'merch_order', o.id
        )
        flash('Bestellung gelöscht.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Löschen nicht möglich.', 'error')
    return redirect(url_for('merch.round_shop', round_id=round_id))


@bp.route('/rounds/<int:round_id>/cancel-order', methods=['POST'])
@login_required
@limiter.limit('30 per minute', methods=['POST'])
def round_cancel_order(round_id: int):
    require_merch_v2_enabled()
    o = MerchOrder.query.filter_by(round_id=round_id, member_id=current_user.id).first()
    if not o:
        flash('Keine Bestellung in dieser Runde.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    result = MerchOrderService.cancel_order_by_member(o.id, current_user.id)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ORDER_CANCELLED, 'merch_order', o.id
        )
        flash('Bestellung storniert.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Storno nicht moeglich.', 'error')
    return redirect(url_for('merch.round_shop', round_id=round_id))


def _normalize_if_none_match(header_val: str | None) -> str:
    if not header_val:
        return ''
    h = header_val.strip()
    if h.startswith('W/'):
        h = h[2:].strip()
    if len(h) >= 2 and h[0] == '"' and h[-1] == '"':
        h = h[1:-1]
    return h


@bp.route('/image/<int:article_id>', methods=['GET'])
@login_required
@limiter.limit('120 per minute', methods=['GET'], override_defaults=True)
def article_image(article_id: int):
    """Binaeres Artikelbild aus Drive (Redis-Cache, ETag). Nur wenn MERCH_V2_ENABLED."""
    if not current_app.config.get('MERCH_V2_ENABLED'):
        abort(404)

    result = MerchImageService.load_image_for_article(article_id)
    if not result.get('success'):
        abort(404)

    etag = result['etag']
    max_age = int(current_app.config.get('MERCH_IMAGE_CACHE_TTL_SECONDS', 86400))
    cc = f'private, max-age={max_age}'

    inm = _normalize_if_none_match(request.headers.get('If-None-Match'))
    if inm and inm == etag:
        resp = Response(status=304)
        resp.headers['ETag'] = f'"{etag}"'
        resp.headers['Cache-Control'] = cc
        return resp

    resp = Response(result['payload'], mimetype=result['mime'])
    resp.headers['ETag'] = f'"{etag}"'
    resp.headers['Cache-Control'] = cc
    return resp
