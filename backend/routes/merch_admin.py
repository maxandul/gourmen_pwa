"""Merch v2 Admin-Cockpit. Pfad /admin/merch-v2 (Legacy bleibt /admin/merch)."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO

import csv

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from backend.extensions import db, limiter
from backend.models.audit_event import AuditAction
from backend.models.merch_v2 import (
    MerchArticle,
    MerchOrder,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchSupplier,
    MerchVariant,
)
from backend.routes.merch_access import (
    marketing_chief_or_admin_required,
    require_merch_v2_enabled,
    treasury_marketing_or_admin_required,
)
from backend.services.merch_order_service import MerchOrderService
from backend.services.merch_round_service import MerchRoundService
from backend.services.security import SecurityService

bp = Blueprint('merch_admin', __name__, url_prefix='/admin/merch-v2')


def _subsidy_chf_to_rappen(val) -> int:
    if val is None:
        return 0
    d = Decimal(str(val))
    q = (d * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(q)


def _variant_attrs_label(attrs: dict | None) -> str:
    if not attrs:
        return 'Standard'
    return ', '.join(f'{k}: {v}' for k, v in sorted(attrs.items()))


def _round_item_add_choices(round_obj: MerchRound) -> list[tuple[int, str]]:
    used = {ri.variant_id for ri in round_obj.round_items}
    variants = (
        MerchVariant.query.join(MerchArticle)
        .filter(MerchArticle.is_archived.is_(False), MerchVariant.is_active.is_(True))
        .order_by(MerchArticle.name, MerchVariant.id)
        .all()
    )
    choices: list[tuple[int, str]] = []
    for v in variants:
        if v.id in used:
            continue
        label = f'{v.article.name} — {_variant_attrs_label(v.attributes)}'
        choices.append((v.id, label))
    return choices


class MerchRoundForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Beschreibung', validators=[Optional(), Length(max=10000)])
    deadline_communicated = DateField('Kommunizierte Frist', validators=[Optional()])
    subsidy_chf = DecimalField(
        'Subvention pro Mitglied (CHF)',
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        default=Decimal('0'),
    )
    submit = SubmitField('Runde speichern')


class AddRoundItemForm(FlaskForm):
    variant_id = SelectField('Variante', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Position hinzufuegen')


@bp.route('/', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def cockpit():
    require_merch_v2_enabled()
    rounds = MerchRound.query.order_by(MerchRound.id.desc()).limit(50).all()
    supplier_count = MerchSupplier.query.filter_by(is_archived=False).count()
    article_count = MerchArticle.query.filter_by(is_archived=False).count()
    return render_template(
        'admin/merch_v2/cockpit.html',
        rounds=rounds,
        supplier_count=supplier_count,
        article_count=article_count,
        MerchRoundStatus=MerchRoundStatus,
    )


@bp.route('/rounds/new', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def round_new():
    require_merch_v2_enabled()
    form = MerchRoundForm()
    return render_template('admin/merch_v2/round_form.html', form=form)


@bp.route('/rounds', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def round_create():
    require_merch_v2_enabled()
    form = MerchRoundForm()
    if form.validate_on_submit():
        rappen = _subsidy_chf_to_rappen(form.subsidy_chf.data)
        result = MerchRoundService.create_draft_round(
            title=form.title.data,
            marketing_chief_id=current_user.id,
            description=form.description.data,
            deadline_communicated=form.deadline_communicated.data,
            subsidy_per_member_rappen=rappen,
        )
        if result['success']:
            db.session.commit()
            rid = result['round'].id
            SecurityService.log_audit_event(
                AuditAction.MERCH_ROUND_CREATED,
                'merch_round',
                rid,
                extra_data={'title': result['round'].title},
            )
            flash('Runde angelegt.', 'success')
            return redirect(url_for('merch_admin.round_detail', round_id=rid))
        db.session.rollback()
        flash(result.get('error') or 'Runde konnte nicht angelegt werden.', 'error')
    else:
        flash('Bitte Eingaben pruefen.', 'error')
    return render_template('admin/merch_v2/round_form.html', form=form)


def _load_round_detail(round_id: int) -> MerchRound:
    return (
        MerchRound.query.options(
            joinedload(MerchRound.round_items).joinedload(MerchRoundItem.variant).joinedload(
                MerchVariant.article
            ),
            joinedload(MerchRound.orders).joinedload(MerchOrder.order_items),
            joinedload(MerchRound.orders).joinedload(MerchOrder.member),
        )
        .filter_by(id=round_id)
        .first_or_404()
    )


def _round_aggregate_rows(round_obj: MerchRound) -> list[tuple[MerchRoundItem, int]]:
    qty_by_item: dict[int, int] = defaultdict(int)
    for o in round_obj.orders:
        if o.status in (MerchOrderStatus.CANCELLED, MerchOrderStatus.DRAFT):
            continue
        for line in o.order_items:
            qty_by_item[line.round_item_id] += line.quantity
    rows: list[tuple[MerchRoundItem, int]] = []
    for ri in sorted(
        round_obj.round_items,
        key=lambda x: (x.variant.article.name.lower(), x.variant_id),
    ):
        rows.append((ri, qty_by_item.get(ri.id, 0)))
    return rows


@bp.route('/rounds/<int:round_id>', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def round_detail(round_id: int):
    require_merch_v2_enabled()
    r = _load_round_detail(round_id)
    add_form = None
    if r.status == MerchRoundStatus.DRAFT:
        choices = _round_item_add_choices(r)
        if choices:
            add_form = AddRoundItemForm()
            add_form.variant_id.choices = choices
    round_items_sorted = sorted(
        r.round_items,
        key=lambda ri: (ri.variant.article.name.lower(), ri.variant_id),
    )
    aggregate_rows = _round_aggregate_rows(r)
    orders_sorted = sorted(
        [o for o in r.orders],
        key=lambda o: ((o.member.nachname or '').lower(), (o.member.vorname or '').lower(), o.id),
    )
    return render_template(
        'admin/merch_v2/round_detail.html',
        round=r,
        MerchRoundStatus=MerchRoundStatus,
        MerchOrderStatus=MerchOrderStatus,
        add_round_item_form=add_form,
        round_items_sorted=round_items_sorted,
        aggregate_rows=aggregate_rows,
        orders_sorted=orders_sorted,
    )


@bp.route('/rounds/<int:round_id>/items', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('60 per minute', methods=['POST'])
def round_add_item(round_id: int):
    require_merch_v2_enabled()
    r = _load_round_detail(round_id)
    form = AddRoundItemForm()
    form.variant_id.choices = _round_item_add_choices(r)
    if not form.variant_id.choices:
        flash('Keine weiteren Varianten verfuegbar.', 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))
    if form.validate_on_submit():
        result = MerchRoundService.add_variant_to_round(round_id, form.variant_id.data)
        if result['success']:
            db.session.commit()
            flash('Position hinzugefuegt.', 'success')
        else:
            db.session.rollback()
            flash(result.get('error') or 'Position konnte nicht hinzugefuegt werden.', 'error')
    else:
        flash('Bitte Variante waehlen.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/items/<int:item_id>/remove', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('60 per minute', methods=['POST'])
def round_remove_item(round_id: int, item_id: int):
    require_merch_v2_enabled()
    result = MerchRoundService.remove_round_item(round_id, item_id)
    if result['success']:
        db.session.commit()
        flash('Position entfernt.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Position konnte nicht entfernt werden.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/open', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def round_open(round_id: int):
    require_merch_v2_enabled()
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(r, MerchRoundStatus.OPEN)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ROUND_OPENED, 'merch_round', round_id
        )
        flash('Runde ist jetzt offen fuer Bestellungen.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


def _parse_transition_reason(min_len: int = 3) -> tuple[str | None, str | None]:
    """Returns (reason, error_message)."""
    reason = (request.form.get('reason') or '').strip()
    if len(reason) < min_len:
        return None, 'Bitte eine Begruendung eingeben (mindestens %s Zeichen).' % min_len
    return reason, None


@bp.route('/rounds/<int:round_id>/lock', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def round_lock(round_id: int):
    require_merch_v2_enabled()
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(r, MerchRoundStatus.LOCKED)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(AuditAction.MERCH_ROUND_LOCKED, 'merch_round', round_id)
        flash('Runde ist geschlossen (Lock). Entwuerfe wurden verworfen.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/reopen', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('20 per minute', methods=['POST'])
def round_reopen(round_id: int):
    require_merch_v2_enabled()
    reason, err = _parse_transition_reason()
    if err:
        flash(err, 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(
        r, MerchRoundStatus.OPEN, transition_reason=reason
    )
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ROUND_REOPENED,
            'merch_round',
            round_id,
            extra_data={'reason': reason[:500]},
        )
        flash('Runde wieder geoeffnet. Mitglieder muessen erneut bestaetigen.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/cancel', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('10 per minute', methods=['POST'])
def round_cancel(round_id: int):
    require_merch_v2_enabled()
    reason, err = _parse_transition_reason()
    if err:
        flash(err, 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(
        r, MerchRoundStatus.CANCELLED, cancellation_reason=reason
    )
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ROUND_CANCELLED,
            'merch_round',
            round_id,
            extra_data={'reason': reason[:500]},
        )
        flash('Runde wurde storniert.', 'warning')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/pricing', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('60 per minute', methods=['POST'])
def round_pricing(round_id: int):
    require_merch_v2_enabled()
    r = _load_round_detail(round_id)
    if r.status != MerchRoundStatus.LOCKED:
        flash('Preise sind nur bei gesperrter Runde editierbar.', 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    action = (request.form.get('pricing_action') or '').strip()

    def parse_chf(field: str) -> int | None:
        raw = (request.form.get(field) or '').strip()
        if raw == '':
            return None
        try:
            return _subsidy_chf_to_rappen(Decimal(raw.replace(',', '.')))
        except Exception:
            return None

    for ri in r.round_items:
        eff = parse_chf(f'effective_chf_{ri.id}')
        mem = parse_chf(f'member_chf_{ri.id}')
        if eff is not None:
            ri.effective_supplier_price_rappen = eff
        if mem is not None:
            ri.member_price_rappen = mem

    if action == 'confirm_ordered':
        result = MerchRoundService.apply_transition(r, MerchRoundStatus.ORDERED_AT_SUPPLIER)
        if result['success']:
            db.session.commit()
            SecurityService.log_audit_event(
                AuditAction.MERCH_ROUND_ORDERED_AT_SUPPLIER,
                'merch_round',
                round_id,
            )
            flash('Lieferantenbestellung bestaetigt; Mitglieder-Forderungen festgeschrieben.', 'success')
        else:
            db.session.rollback()
            flash(result.get('error') or 'Uebergang nicht moeglich.', 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    db.session.commit()
    flash('Preise gespeichert.', 'success')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/delivered', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def round_delivered(round_id: int):
    require_merch_v2_enabled()
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(r, MerchRoundStatus.DELIVERED)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ROUND_DELIVERED, 'merch_round', round_id
        )
        flash('Wareneingang bestaetigt.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/close', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def round_close(round_id: int):
    require_merch_v2_enabled()
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    result = MerchRoundService.apply_transition(r, MerchRoundStatus.CLOSED)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(AuditAction.MERCH_ROUND_CLOSED, 'merch_round', round_id)
        flash('Runde abgeschlossen.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/aggregate.csv', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def round_aggregate_csv(round_id: int):
    require_merch_v2_enabled()
    r = _load_round_detail(round_id)
    rows = _round_aggregate_rows(r)
    buf = StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(['Artikel', 'Variante', 'Stueckzahl', 'Listenpreis_CHF', 'Effektiv_CHF', 'Mitglied_CHF'])
    for ri, qty in rows:
        attr = _variant_attrs_label(ri.variant.attributes)
        w.writerow(
            [
                ri.variant.article.name,
                attr,
                qty,
                f'{ri.list_price_snapshot_rappen / 100:.2f}',
                ''
                if ri.effective_supplier_price_rappen is None
                else f'{ri.effective_supplier_price_rappen / 100:.2f}',
                ''
                if ri.member_price_rappen is None
                else f'{ri.member_price_rappen / 100:.2f}',
            ]
        )
    data = buf.getvalue().encode('utf-8-sig')
    resp = Response(data, mimetype='text/csv; charset=utf-8')
    safe_title = ''.join(c if c.isalnum() or c in '-_' else '_' for c in r.title)[:60]
    resp.headers['Content-Disposition'] = (
        f'attachment; filename=merch-runde-{round_id}-{safe_title}-aggregat.csv'
    )
    return resp


@bp.route('/rounds/<int:round_id>/orders/<int:order_id>/picked_up', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('120 per minute', methods=['POST'])
def order_mark_picked_up(round_id: int, order_id: int):
    require_merch_v2_enabled()
    MerchOrder.query.filter_by(id=order_id, round_id=round_id).first_or_404()
    result = MerchOrderService.mark_picked_up(order_id, current_user.id)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(
            AuditAction.MERCH_ORDER_PICKED_UP, 'merch_order', order_id
        )
        r2 = db.session.get(MerchRound, round_id)
        ac = MerchRoundService.try_auto_close_if_complete(r2) if r2 else {'changed': False}
        if ac.get('changed'):
            db.session.commit()
            flash('Abgeholt. Runde automatisch abgeschlossen.', 'success')
        else:
            flash('Als abgeholt markiert.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/rounds/<int:round_id>/orders/<int:order_id>/paid', methods=['POST'])
@login_required
@treasury_marketing_or_admin_required
@limiter.limit('120 per minute', methods=['POST'])
def order_mark_paid(round_id: int, order_id: int):
    require_merch_v2_enabled()
    MerchOrder.query.filter_by(id=order_id, round_id=round_id).first_or_404()
    result = MerchOrderService.mark_paid(order_id, current_user.id)
    if result['success']:
        db.session.commit()
        SecurityService.log_audit_event(AuditAction.MERCH_ORDER_PAID, 'merch_order', order_id)
        r2 = db.session.get(MerchRound, round_id)
        ac = MerchRoundService.try_auto_close_if_complete(r2) if r2 else {'changed': False}
        if ac.get('changed'):
            db.session.commit()
            flash('Bezahlt. Runde automatisch abgeschlossen.', 'success')
        else:
            flash('Als bezahlt markiert.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))
