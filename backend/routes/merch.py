"""Merch v2 Routes (Shop, Warenkorb, Bild-Proxy). Feature-Flag: MERCH_V2_ENABLED."""

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
from backend.services.merch_order_service import MerchOrderService

bp = Blueprint('merch', __name__)


@bp.route('/', methods=['GET'])
@login_required
def shop_index():
    """Mitgliedsshop-Uebersicht (Merch v2). Legacy bleibt unter /member/merch."""
    require_merch_v2_enabled()
    open_rounds = (
        MerchRound.query.filter(MerchRound.status == MerchRoundStatus.OPEN)
        .order_by(MerchRound.id.desc())
        .all()
    )
    recent_orders = (
        MerchOrder.query.options(joinedload(MerchOrder.round))
        .filter(
            MerchOrder.member_id == current_user.id,
            MerchOrder.status != MerchOrderStatus.CANCELLED,
        )
        .order_by(MerchOrder.id.desc())
        .limit(24)
        .all()
    )
    return render_template(
        'merch/shop.html',
        open_rounds=open_rounds,
        recent_orders=recent_orders,
    )


def _sort_round_items(round_obj: MerchRound):
    return sorted(
        round_obj.round_items,
        key=lambda ri: (ri.variant.article.name.lower(), ri.variant_id),
    )


@bp.route('/rounds/<int:round_id>', methods=['GET'])
@login_required
def round_shop(round_id: int):
    require_merch_v2_enabled()
    r = (
        MerchRound.query.options(
            joinedload(MerchRound.round_items).joinedload(MerchRoundItem.variant).joinedload(
                MerchVariant.article
            ),
        )
        .filter_by(id=round_id)
        .first_or_404()
    )

    round_items_sorted = _sort_round_items(r)
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

    return render_template(
        'merch/round_shop.html',
        round=r,
        round_items_sorted=round_items_sorted,
        order=order,
        editable=editable,
        qty_by_ri=qty_by_ri,
        cart_blocked_reason=cart_blocked_reason,
        MerchRoundStatus=MerchRoundStatus,
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
    if not res_o['success'] or not res_o.get('editable'):
        db.session.rollback()
        flash(res_o.get('error') or 'Warenkorb nicht verfuegbar.', 'error')
        return redirect(url_for('merch.round_shop', round_id=round_id))

    oid = res_o['order'].id
    result = MerchOrderService.set_cart_line(oid, current_user.id, round_item_id, qty)
    if result['success']:
        db.session.commit()
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
        flash('Bestellung bestaetigt.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Bestellung fehlgeschlagen.', 'error')
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
