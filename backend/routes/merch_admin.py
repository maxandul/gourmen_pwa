"""Merch v2 Admin-Cockpit. Pfad /admin/merch-v2 (Legacy bleibt /admin/merch)."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.orm import joinedload
from wtforms import DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from backend.extensions import db, limiter
from backend.models.merch_v2 import (
    MerchArticle,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchSupplier,
    MerchVariant,
)
from backend.routes.merch_access import marketing_chief_or_admin_required, require_merch_v2_enabled
from backend.services.merch_round_service import MerchRoundService

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
            flash('Runde angelegt.', 'success')
            return redirect(url_for('merch_admin.round_detail', round_id=result['round'].id))
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
        )
        .filter_by(id=round_id)
        .first_or_404()
    )


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
    return render_template(
        'admin/merch_v2/round_detail.html',
        round=r,
        MerchRoundStatus=MerchRoundStatus,
        add_round_item_form=add_form,
        round_items_sorted=round_items_sorted,
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
        flash('Runde ist jetzt offen fuer Bestellungen.', 'success')
    else:
        db.session.rollback()
        flash(result.get('error') or 'Aktion nicht moeglich.', 'error')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))
