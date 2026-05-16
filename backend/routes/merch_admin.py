"""Merch v2 Admin-Cockpit. Pfad /admin/merch-v2 (Legacy bleibt /admin/merch)."""

from __future__ import annotations

import io
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO

import csv

from flask import Blueprint, Response, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import joinedload
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from backend.extensions import db, limiter
from backend.models.audit_event import AuditAction
from backend.models.member import Funktion
from backend.models.merch_v2 import (
    MerchArticle,
    MerchColor,
    MerchOrder,
    MerchOrderStatus,
    MerchRound,
    MerchRoundItem,
    MerchRoundStatus,
    MerchSize,
    MerchSupplier,
    MerchVariant,
)
from backend.routes.merch_access import (
    marketing_chief_or_admin_required,
    merch_statistics_view_required,
    require_merch_v2_enabled,
    treasury_marketing_or_admin_required,
)
from backend.services.drive_storage import DriveError, DriveStorageService, DriveValidationError
from backend.services.merch_image_service import MerchImageService
from backend.services.merch_lookup_service import MerchLookupService, MerchVariantBulkService
from backend.services.merch_order_service import MerchOrderService
from backend.services.merch_round_service import MerchRoundService
from backend.services.merch_sortiment_service import (
    MerchSortimentService,
    merged_variant_schema_from_lookups,
    lookup_color_and_size_field_ids_from_schema,
    validate_variant_schema_limits,
)
from backend.services.merch_statistics_service import (
    build_year_overview,
    club_season_utc_bounds,
    compute_round_statistics,
    current_club_season_label_year,
    top_articles_by_margin_for_round_ids,
    top_articles_by_quantity_for_round_ids,
)
from backend.services.security import SecurityService

bp = Blueprint('merch_admin', __name__, url_prefix='/admin/merch-v2')

_MERCH_HUB_MAIN_TABS = frozenset({'cockpit', 'lieferanten', 'sortiment', 'runden', 'statistik'})
# Alte Bookmarks nutzten tab= fuer innere Cockpit-Panels (vor Haupt-Tabs).
_MERCH_HUB_LEGACY_WRONG_TAB = frozenset({'uebersicht', 'kennzahlen', 'stamm'})


def _user_can_merch_marketing_hub(user) -> bool:
    if not user.is_authenticated or not getattr(user, 'is_active', False):
        return False
    if user.is_admin():
        return True
    return getattr(user, 'funktion', None) == Funktion.MARKETINGCHEF


def _user_can_merch_statistics_hub(user) -> bool:
    if not user.is_authenticated or not getattr(user, 'is_active', False):
        return False
    if user.is_admin():
        return True
    fx = getattr(user, 'funktion', None)
    return fx in (Funktion.MARKETINGCHEF, Funktion.SCHATZMEISTER)


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


class MerchSupplierForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=200)])
    contact_email = StringField('Kontakt E-Mail', validators=[Optional(), Length(max=200)])
    website_url = StringField('Webseite (URL)', validators=[Optional(), Length(max=500)])
    notes = TextAreaField('Notizen', validators=[Optional(), Length(max=10000)])
    submit = SubmitField('Speichern')


class MerchArticleForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=200)])
    supplier_id = SelectField('Lieferant', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[Optional(), Length(max=10000)])
    list_price_chf = DecimalField(
        'Listenpreis (CHF)',
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    color_choice_ids = SelectMultipleField(
        'Farben',
        coerce=int,
        validators=[Optional()],
    )
    size_choice_ids = SelectMultipleField(
        'Grössen',
        coerce=int,
        validators=[Optional()],
    )
    remove_image = BooleanField('Artikelbild entfernen')
    submit = SubmitField('Speichern')


def _populate_merch_article_variant_lookup_choices(form: MerchArticleForm) -> tuple[int, int]:
    colors = MerchLookupService.list_colors_ordered()
    sizes = MerchLookupService.list_sizes_ordered()
    form.color_choice_ids.choices = [(c.id, c.label) for c in colors]
    form.size_choice_ids.choices = [(s.id, s.label) for s in sizes]
    return len(colors), len(sizes)


def _merch_article_multiselect_rows(n_opts: int) -> int:
    if n_opts < 1:
        return 3
    return max(4, min(14, n_opts + 2))


_MERCH_ARTICLE_IMAGE_MIMES = frozenset(
    {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/heic', 'image/heif'}
)


def _supplier_select_choices(include_supplier_id: int | None = None) -> list[tuple[int, str]]:
    active = (
        MerchSupplier.query.filter_by(is_archived=False)
        .order_by(MerchSupplier.name.asc())
        .all()
    )
    ids = {s.id for s in active}
    if include_supplier_id and include_supplier_id not in ids:
        extra = db.session.get(MerchSupplier, include_supplier_id)
        if extra:
            active = sorted(active + [extra], key=lambda x: (x.name or '').lower())
    return [(s.id, s.name) for s in active]


def _article_store_image_upload(article: MerchArticle, uf) -> str | None:
    """Laedt Artikelbild nach Drive. Ohne Datei: None. Bei Fehler: Meldung (Flash durch Caller)."""
    if uf is None or not getattr(uf, 'filename', None):
        return None
    folder_id = (current_app.config.get('MERCH_ARTICLE_IMAGE_DRIVE_FOLDER_ID') or '').strip()
    if not folder_id:
        flash(
            'MERCH_ARTICLE_IMAGE_DRIVE_FOLDER_ID fehlt — Bild wurde nicht gespeichert.',
            'warning',
        )
        return None
    raw = uf.read()
    if not raw:
        return 'Leere Datei.'
    mime = ((uf.mimetype or '') or '').split(';')[0].strip().lower()
    if mime not in _MERCH_ARTICLE_IMAGE_MIMES:
        return 'Nur Bilder (JPEG, PNG, WebP, GIF, HEIC) sind erlaubt.'
    try:
        doc = DriveStorageService.upload_document(
            file_stream=io.BytesIO(raw),
            filename_stem=f'merch-artikel-{article.id}',
            drive_folder_id=folder_id,
            uploader=current_user,
            event_id=None,
            original_filename=uf.filename,
            mime_type=mime or 'image/jpeg',
        )
        article.image_drive_file_id = doc.drive_file_id
        MerchImageService.invalidate_article_cache(article.id)
        return None
    except DriveValidationError as exc:
        return str(exc)
    except DriveError as exc:
        return str(exc)
    except Exception as exc:
        current_app.logger.error('Merch Artikelbild Upload: %s', exc, exc_info=True)
        return 'Drive-Upload fehlgeschlagen.'


@bp.route('/', methods=['GET'])
@login_required
def cockpit():
    """Einheitliche Merch-Admin-Shell unter /admin/merch-v2/ (?tab=cockpit|lieferanten|sortiment|runden|statistik)."""
    require_merch_v2_enabled()
    if not getattr(current_user, 'is_active', False):
        abort(403)

    raw_tab = request.args.get('tab')
    if raw_tab is not None:
        legacy_key = raw_tab.strip().lower()
        if legacy_key in _MERCH_HUB_LEGACY_WRONG_TAB:
            return redirect(url_for('merch_admin.cockpit', tab='cockpit'))

    if raw_tab is None:
        return redirect(url_for('merch_admin.cockpit', tab='cockpit'))

    main_tab = raw_tab.strip().lower()
    if main_tab not in _MERCH_HUB_MAIN_TABS:
        return redirect(url_for('merch_admin.cockpit', tab='cockpit'))

    if main_tab == 'statistik':
        if not _user_can_merch_statistics_hub(current_user):
            abort(403)
    elif not _user_can_merch_marketing_hub(current_user):
        abort(403)

    if main_tab == 'cockpit' and request.args.get('panel'):
        return redirect(url_for('merch_admin.cockpit', tab='cockpit'))

    ctx: dict = {
        'merch_tab': main_tab,
        'MerchRoundStatus': MerchRoundStatus,
    }

    if main_tab == 'cockpit':
        ctx['supplier_count'] = MerchSupplier.query.filter_by(is_archived=False).count()
        ctx['article_count'] = MerchArticle.query.filter_by(is_archived=False).count()
    elif main_tab == 'runden':
        ctx['rounds'] = MerchRound.query.order_by(MerchRound.id.desc()).limit(50).all()
    elif main_tab == 'lieferanten':
        ctx['active_suppliers'] = (
            MerchSupplier.query.filter_by(is_archived=False).order_by(MerchSupplier.name.asc()).all()
        )
        ctx['archived_suppliers'] = (
            MerchSupplier.query.filter_by(is_archived=True).order_by(MerchSupplier.name.asc()).all()
        )
    elif main_tab == 'sortiment':
        active_list = (
            MerchArticle.query.filter_by(is_archived=False)
            .options(joinedload(MerchArticle.supplier))
            .order_by(MerchArticle.name.asc())
            .all()
        )
        archived_list = (
            MerchArticle.query.filter_by(is_archived=True)
            .options(joinedload(MerchArticle.supplier))
            .order_by(MerchArticle.name.asc())
            .all()
        )
        ctx['active_articles'] = active_list
        ctx['archived_articles'] = archived_list
        aid_sortiment = [a.id for a in active_list] + [a.id for a in archived_list]
        ctx['sortiment_article_dimensions'] = _article_archive_dimension_strings(aid_sortiment)
    elif main_tab == 'statistik':
        years = _statistics_season_years_list()
        requested = request.args.get('year', type=int)
        year = requested if requested is not None else current_club_season_label_year()
        if years and year not in years:
            year = years[0]
        overview = build_year_overview(year)
        qty_top = top_articles_by_quantity_for_round_ids(overview.round_ids, limit=5)
        marg_top = top_articles_by_margin_for_round_ids(overview.round_ids, limit=5)
        season_start, season_end = club_season_utc_bounds(year)
        ctx.update(
            season_year=year,
            season_years=years,
            overview=overview,
            top_qty=qty_top,
            top_margin=marg_top,
            season_start=season_start.date(),
            season_end=season_end.date(),
        )

    return render_template('admin/merch_v2/merch_hub.html', **ctx)


def _supplier_apply_form(form: MerchSupplierForm, model: MerchSupplier) -> None:
    raw_email = (form.contact_email.data or '').strip()
    model.name = (form.name.data or '').strip()
    model.contact_email = raw_email or None
    raw_url = (form.website_url.data or '').strip()
    model.website_url = raw_url or None
    model.notes = (form.notes.data or '').strip() or None


@bp.route('/suppliers', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def suppliers_index():
    require_merch_v2_enabled()
    return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))


@bp.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def supplier_new():
    require_merch_v2_enabled()
    form = MerchSupplierForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            s = MerchSupplier(is_archived=False)
            _supplier_apply_form(form, s)
            db.session.add(s)
            db.session.commit()
            SecurityService.log_audit_event(
                AuditAction.MERCH_SUPPLIER_CREATED,
                'merch_supplier',
                s.id,
                extra_data={'name': s.name},
            )
            flash('Lieferant angelegt.', 'success')
            return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))
        flash('Bitte Eingaben pruefen.', 'error')
    return render_template(
        'admin/merch_v2/supplier_form.html',
        form=form,
        page_title='Neuer Lieferant',
        supplier=None,
    )


@bp.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def supplier_edit(supplier_id: int):
    require_merch_v2_enabled()
    s = MerchSupplier.query.filter_by(id=supplier_id).first_or_404()
    if request.method == 'POST':
        form = MerchSupplierForm()
        if form.validate_on_submit():
            _supplier_apply_form(form, s)
            db.session.commit()
            SecurityService.log_audit_event(
                AuditAction.MERCH_SUPPLIER_UPDATED,
                'merch_supplier',
                s.id,
                extra_data={'name': s.name},
            )
            flash('Lieferant gespeichert.', 'success')
            return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))
        flash('Bitte Eingaben pruefen.', 'error')
    else:
        form = MerchSupplierForm(obj=s)
    return render_template(
        'admin/merch_v2/supplier_form.html',
        form=form,
        page_title='Lieferant bearbeiten',
        supplier=s,
    )


@bp.route('/suppliers/<int:supplier_id>/archive', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def supplier_archive(supplier_id: int):
    require_merch_v2_enabled()
    s = MerchSupplier.query.filter_by(id=supplier_id).first_or_404()
    if s.is_archived:
        flash('Lieferant ist bereits archiviert.', 'warning')
        return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))
    blocked = MerchArticle.query.filter_by(supplier_id=s.id, is_archived=False).count()
    if blocked > 0:
        flash('Lieferant hat noch aktive Artikel — bitte zuerst alle Artikel archivieren.', 'error')
        return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))
    s.is_archived = True
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_SUPPLIER_UPDATED,
        'merch_supplier',
        s.id,
        extra_data={'archived': True, 'name': s.name},
    )
    flash('Lieferant archiviert.', 'success')
    return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))


@bp.route('/suppliers/<int:supplier_id>/restore', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def supplier_restore(supplier_id: int):
    require_merch_v2_enabled()
    s = MerchSupplier.query.filter_by(id=supplier_id).first_or_404()
    if not s.is_archived:
        flash('Lieferant ist bereits aktiv.', 'warning')
        return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))
    s.is_archived = False
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_SUPPLIER_UPDATED,
        'merch_supplier',
        s.id,
        extra_data={'restored': True, 'name': s.name},
    )
    flash('Lieferant wieder aktiviert.', 'success')
    return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))


def _article_apply_core(form: MerchArticleForm, article: MerchArticle) -> None:
    article.name = (form.name.data or '').strip()
    article.supplier_id = int(form.supplier_id.data)
    article.description = (form.description.data or '').strip() or None
    article.list_price_rappen = _subsidy_chf_to_rappen(form.list_price_chf.data)


def _article_active_variant_rows(article: MerchArticle | None) -> list[MerchVariant]:
    if article is None:
        return []
    rows = [v for v in (article.variants or []) if v.is_active]
    return sorted(rows, key=lambda v: (_variant_attrs_label(v.attributes).lower(), v.id))


def _article_variant_pricing_rows(article: MerchArticle | None) -> list[tuple[MerchVariant, str]]:
    return [(v, _variant_attrs_label(v.attributes)) for v in _article_active_variant_rows(article)]


_VARIANT_PRICE_FIELD_PREFIX = 'variant_list_price_chf_'


def _apply_variant_list_price_overrides(article_id: int) -> str | None:
    """POST-Felder variant_list_price_chf_<id>; leer = Artikel-Default (NULL in DB)."""
    for key in request.form:
        if not key.startswith(_VARIANT_PRICE_FIELD_PREFIX):
            continue
        try:
            vid = int(key[len(_VARIANT_PRICE_FIELD_PREFIX) :])
        except ValueError:
            continue
        v = db.session.get(MerchVariant, vid)
        if not v or v.article_id != article_id:
            continue
        raw = (request.form.get(key) or '').strip()
        if raw == '':
            v.list_price_rappen = None
            continue
        try:
            d = Decimal(raw.replace(',', '.'))
            if d < 0:
                return 'Variantenpreis darf nicht negativ sein.'
            v.list_price_rappen = _subsidy_chf_to_rappen(d)
        except Exception:
            return 'Ungueltiger Variantenpreis (CHF).'
    return None


def _article_archive_dimension_strings(article_ids: list[int]) -> dict[int, tuple[str, str]]:
    """Pro Artikel: (Farben kommasepariert, Grössen kommasepariert) fuer Archiv-Tabelle."""
    if not article_ids:
        return {}
    variants = (
        MerchVariant.query.filter(MerchVariant.article_id.in_(article_ids))
        .options(joinedload(MerchVariant.color), joinedload(MerchVariant.size))
        .all()
    )
    color_rank: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)
    size_rank: dict[int, dict[str, tuple[int, str]]] = defaultdict(dict)
    attr_colors: dict[int, set[str]] = defaultdict(set)
    attr_sizes: dict[int, set[str]] = defaultdict(set)

    def _take_best(store: dict[str, tuple[int, str]], label: str, sort_order: int) -> None:
        prev = store.get(label)
        if prev is None or sort_order < prev[0]:
            store[label] = (sort_order, label)

    for v in variants:
        aid = v.article_id
        if v.color_id and v.color:
            _take_best(color_rank[aid], v.color.label, int(v.color.sort_order))
        elif isinstance(v.attributes, dict):
            raw = v.attributes.get('farbe')
            if raw is not None and str(raw).strip():
                attr_colors[aid].add(str(raw).strip())

        if v.size_id and v.size:
            _take_best(size_rank[aid], v.size.label, int(v.size.sort_order))
        elif isinstance(v.attributes, dict):
            raw = v.attributes.get('groesse')
            if raw is not None and str(raw).strip():
                attr_sizes[aid].add(str(raw).strip())

    out: dict[int, tuple[str, str]] = {}
    for aid in article_ids:
        c_sorted = sorted(color_rank.get(aid, {}).values(), key=lambda t: (t[0], t[1].lower()))
        color_labels = [t[1] for t in c_sorted]
        for extra in sorted(attr_colors.get(aid, set()), key=str.lower):
            if extra not in color_labels:
                color_labels.append(extra)

        s_sorted = sorted(size_rank.get(aid, {}).values(), key=lambda t: (t[0], t[1].lower()))
        size_labels = [t[1] for t in s_sorted]
        for extra in sorted(attr_sizes.get(aid, set()), key=str.lower):
            if extra not in size_labels:
                size_labels.append(extra)

        out[aid] = (', '.join(color_labels), ', '.join(size_labels))
    return out


def _article_bulk_color_size_lists(
    article: MerchArticle | None,
) -> tuple[list[MerchColor], list[MerchSize]]:
    """Distinct Farben/Groessen, die bei Varianten dieses Artikels vorkommen."""
    if article is None:
        return [], []
    c_ids = list(
        db.session.scalars(
            select(distinct(MerchVariant.color_id)).where(
                MerchVariant.article_id == article.id,
                MerchVariant.color_id.isnot(None),
            )
        ).all()
    )
    s_ids = list(
        db.session.scalars(
            select(distinct(MerchVariant.size_id)).where(
                MerchVariant.article_id == article.id,
                MerchVariant.size_id.isnot(None),
            )
        ).all()
    )
    colors: list[MerchColor] = []
    sizes: list[MerchSize] = []
    if c_ids:
        colors = (
            MerchColor.query.filter(MerchColor.id.in_(sorted(c_ids)))
            .order_by(MerchColor.sort_order.asc(), MerchColor.label.asc())
            .all()
        )
    if s_ids:
        sizes = (
            MerchSize.query.filter(MerchSize.id.in_(sorted(s_ids)))
            .order_by(MerchSize.sort_order.asc(), MerchSize.label.asc())
            .all()
        )
    return colors, sizes


@bp.route('/articles', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def articles_index():
    require_merch_v2_enabled()
    return redirect(url_for('merch_admin.cockpit', tab='sortiment'))


@bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_new():
    require_merch_v2_enabled()
    form = MerchArticleForm()
    form.supplier_id.choices = _supplier_select_choices()
    n_colors, n_sizes = _populate_merch_article_variant_lookup_choices(form)
    if not form.supplier_id.choices:
        flash('Bitte zuerst mindestens einen aktiven Lieferanten anlegen.', 'warning')
        return redirect(url_for('merch_admin.cockpit', tab='lieferanten'))

    if request.method == 'POST':
        form.supplier_id.choices = _supplier_select_choices()
        n_colors, n_sizes = _populate_merch_article_variant_lookup_choices(form)
        merged = merged_variant_schema_from_lookups(
            color_ids=form.color_choice_ids.data,
            size_ids=form.size_choice_ids.data,
            preserved_legacy_schema=None,
        )
        v_err = validate_variant_schema_limits(merged)
        if v_err:
            flash(v_err, 'error')
        elif form.validate_on_submit():
            art = MerchArticle(is_archived=False)
            _article_apply_core(form, art)
            db.session.add(art)
            db.session.flush()
            MerchSortimentService.sync_variants_for_article(art, merged)
            db.session.flush()
            price_err = _apply_variant_list_price_overrides(art.id)
            if price_err:
                db.session.rollback()
                flash(price_err, 'error')
            else:
                img_err = _article_store_image_upload(art, request.files.get('article_image'))
                if img_err:
                    db.session.rollback()
                    flash(img_err, 'error')
                else:
                    db.session.commit()
                    SecurityService.log_audit_event(
                        AuditAction.MERCH_ARTICLE_CREATED,
                        'merch_article',
                        art.id,
                        extra_data={'name': art.name},
                    )
                    flash('Artikel angelegt. Optional: Variantenpreise anpassen.', 'success')
                    return redirect(url_for('merch_admin.article_edit', article_id=art.id))
        else:
            flash('Bitte Eingaben pruefen.', 'error')
    return render_template(
        'admin/merch_v2/article_form.html',
        form=form,
        page_title='Neuer Artikel',
        article=None,
        variant_pricing_rows=[],
        bulk_colors=[],
        bulk_sizes=[],
        merch_variant_color_select_rows=_merch_article_multiselect_rows(n_colors),
        merch_variant_size_select_rows=_merch_article_multiselect_rows(n_sizes),
        merch_variant_lookups_url=url_for('merch_admin.lookups_index'),
    )


@bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_edit(article_id: int):
    require_merch_v2_enabled()
    art = (
        MerchArticle.query.options(joinedload(MerchArticle.variants))
        .filter_by(id=article_id)
        .first_or_404()
    )
    legacy_schema = art.variant_schema if isinstance(art.variant_schema, dict) else {}

    if request.method == 'GET':
        form = MerchArticleForm(
            name=art.name,
            supplier_id=art.supplier_id,
            description=art.description or '',
            list_price_chf=Decimal(art.list_price_rappen) / Decimal('100'),
            remove_image=False,
        )
    else:
        form = MerchArticleForm()

    form.supplier_id.choices = _supplier_select_choices(include_supplier_id=art.supplier_id)
    n_colors, n_sizes = _populate_merch_article_variant_lookup_choices(form)

    if request.method == 'GET':
        c_sel, s_sel = lookup_color_and_size_field_ids_from_schema(legacy_schema)
        form.color_choice_ids.data = c_sel
        form.size_choice_ids.data = s_sel

    if request.method == 'POST':
        merged = merged_variant_schema_from_lookups(
            color_ids=form.color_choice_ids.data,
            size_ids=form.size_choice_ids.data,
            preserved_legacy_schema=legacy_schema,
        )
        v_err = validate_variant_schema_limits(merged)
        if v_err:
            flash(v_err, 'error')
        elif form.validate_on_submit():
            _article_apply_core(form, art)
            MerchSortimentService.sync_variants_for_article(art, merged)
            db.session.flush()
            price_err = _apply_variant_list_price_overrides(art.id)
            if price_err:
                db.session.rollback()
                flash(price_err, 'error')
            else:
                if form.remove_image.data:
                    art.image_drive_file_id = None
                    MerchImageService.invalidate_article_cache(art.id)
                img_err = _article_store_image_upload(art, request.files.get('article_image'))
                if img_err:
                    db.session.rollback()
                    flash(img_err, 'error')
                else:
                    db.session.commit()
                    SecurityService.log_audit_event(
                        AuditAction.MERCH_ARTICLE_UPDATED,
                        'merch_article',
                        art.id,
                        extra_data={'name': art.name},
                    )
                    flash('Artikel gespeichert.', 'success')
                    return redirect(url_for('merch_admin.article_edit', article_id=art.id))
        else:
            flash('Bitte Eingaben pruefen.', 'error')
    bulk_colors, bulk_sizes = _article_bulk_color_size_lists(art)
    return render_template(
        'admin/merch_v2/article_form.html',
        form=form,
        page_title='Artikel bearbeiten',
        article=art,
        variant_pricing_rows=_article_variant_pricing_rows(art),
        bulk_colors=bulk_colors,
        bulk_sizes=bulk_sizes,
        merch_variant_color_select_rows=_merch_article_multiselect_rows(n_colors),
        merch_variant_size_select_rows=_merch_article_multiselect_rows(n_sizes),
        merch_variant_lookups_url=url_for('merch_admin.lookups_index'),
    )


@bp.route('/articles/<int:article_id>/archive', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_archive(article_id: int):
    require_merch_v2_enabled()
    art = MerchArticle.query.filter_by(id=article_id).first_or_404()
    if art.is_archived:
        flash('Artikel ist bereits archiviert.', 'warning')
        return redirect(url_for('merch_admin.cockpit', tab='sortiment'))
    art.is_archived = True
    for v in art.variants:
        v.is_active = False
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_ARTICLE_ARCHIVED,
        'merch_article',
        art.id,
        extra_data={'name': art.name},
    )
    flash('Artikel archiviert.', 'success')
    return redirect(url_for('merch_admin.cockpit', tab='sortiment'))


@bp.route('/articles/<int:article_id>/restore', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_restore(article_id: int):
    require_merch_v2_enabled()
    art = MerchArticle.query.filter_by(id=article_id).first_or_404()
    if not art.is_archived:
        flash('Artikel ist bereits aktiv.', 'warning')
        return redirect(url_for('merch_admin.cockpit', tab='sortiment'))
    if art.supplier and art.supplier.is_archived:
        flash('Lieferant ist archiviert — bitte zuerst Lieferant wieder aktivieren.', 'error')
        return redirect(url_for('merch_admin.cockpit', tab='sortiment'))
    art.is_archived = False
    schema = art.variant_schema if isinstance(art.variant_schema, dict) else {}
    MerchSortimentService.sync_variants_for_article(art, schema)
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_ARTICLE_UPDATED,
        'merch_article',
        art.id,
        extra_data={'restored': True, 'name': art.name},
    )
    flash('Artikel wieder aktiv.', 'success')
    return redirect(url_for('merch_admin.cockpit', tab='sortiment'))


@bp.route('/lookups', methods=['GET'])
@login_required
@marketing_chief_or_admin_required
def lookups_index():
    require_merch_v2_enabled()
    return render_template(
        'admin/merch_v2/lookups_hub.html',
        page_title='Farben und Groessen',
        colors=MerchLookupService.list_colors_ordered(),
        sizes=MerchLookupService.list_sizes_ordered(),
        merch_tab='sortiment',
    )


@bp.route('/lookups/colors/new', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def lookups_color_new():
    require_merch_v2_enabled()
    res = MerchLookupService.create_color(request.form.get('label', ''))
    if res['success']:
        db.session.commit()
        flash('Farbe angelegt.', 'success')
    else:
        db.session.rollback()
        flash(res.get('error') or 'Farbe konnte nicht angelegt werden.', 'error')
    return redirect(url_for('merch_admin.lookups_index'))


@bp.route('/lookups/colors/<int:color_id>/rename', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def lookups_color_rename(color_id: int):
    require_merch_v2_enabled()
    res = MerchLookupService.rename_color(color_id, request.form.get('label', ''))
    if res['success']:
        db.session.commit()
        flash('Farbe umbenannt.', 'success')
    else:
        db.session.rollback()
        flash(res.get('error') or 'Umbenennen fehlgeschlagen.', 'error')
    return redirect(url_for('merch_admin.lookups_index'))


@bp.route('/lookups/sizes/new', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def lookups_size_new():
    require_merch_v2_enabled()
    res = MerchLookupService.create_size(request.form.get('label', ''))
    if res['success']:
        db.session.commit()
        flash('Grösse angelegt.', 'success')
    else:
        db.session.rollback()
        flash(res.get('error') or 'Grösse konnte nicht angelegt werden.', 'error')
    return redirect(url_for('merch_admin.lookups_index'))


@bp.route('/lookups/sizes/<int:size_id>/rename', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def lookups_size_rename(size_id: int):
    require_merch_v2_enabled()
    res = MerchLookupService.rename_size(size_id, request.form.get('label', ''))
    if res['success']:
        db.session.commit()
        flash('Grösse umbenannt.', 'success')
    else:
        db.session.rollback()
        flash(res.get('error') or 'Umbenennen fehlgeschlagen.', 'error')
    return redirect(url_for('merch_admin.lookups_index'))


@bp.route('/articles/<int:article_id>/variants/bulk-deactivate-color', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_variants_bulk_deactivate_color(article_id: int):
    require_merch_v2_enabled()
    art = MerchArticle.query.filter_by(id=article_id).first_or_404()
    cid = request.form.get('color_id', type=int)
    if not cid:
        flash('Bitte eine Farbe wählen.', 'error')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    hit = MerchVariant.query.filter_by(
        article_id=art.id, color_id=cid
    ).first()
    if hit is None:
        flash('Für diesen Artikel gibt es keine Variante mit dieser Farbe.', 'warning')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    n, err = MerchVariantBulkService.deactivate_variants_with_color(
        article_id=art.id, color_id=cid
    )
    if err:
        db.session.rollback()
        flash(err, 'error')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_ARTICLE_UPDATED,
        'merch_article',
        art.id,
        extra_data={
            'bulk_deactivate_color_id': cid,
            'variants_touched': n,
        },
    )
    if n:
        flash(f'{n} Variante(n) mit dieser Farbe deaktiviert.', 'success')
    else:
        flash('Keine passenden Varianten (bereits inaktiv).', 'info')
    return redirect(url_for('merch_admin.article_edit', article_id=article_id))


@bp.route('/articles/<int:article_id>/variants/bulk-deactivate-size', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('30 per minute', methods=['POST'])
def article_variants_bulk_deactivate_size(article_id: int):
    require_merch_v2_enabled()
    art = MerchArticle.query.filter_by(id=article_id).first_or_404()
    sid = request.form.get('size_id', type=int)
    if not sid:
        flash('Bitte eine Grösse wählen.', 'error')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    hit = MerchVariant.query.filter_by(article_id=art.id, size_id=sid).first()
    if hit is None:
        flash('Für diesen Artikel gibt es keine Variante mit dieser Grösse.', 'warning')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    n, err = MerchVariantBulkService.deactivate_variants_with_size(
        article_id=art.id, size_id=sid
    )
    if err:
        db.session.rollback()
        flash(err, 'error')
        return redirect(url_for('merch_admin.article_edit', article_id=article_id))
    db.session.commit()
    SecurityService.log_audit_event(
        AuditAction.MERCH_ARTICLE_UPDATED,
        'merch_article',
        art.id,
        extra_data={
            'bulk_deactivate_size_id': sid,
            'variants_touched': n,
        },
    )
    if n:
        flash(f'{n} Variante(n) mit dieser Grösse deaktiviert.', 'success')
    else:
        flash('Keine passenden Varianten (bereits inaktiv).', 'info')
    return redirect(url_for('merch_admin.article_edit', article_id=article_id))


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


def _supplier_invoice_web_link_safe(file_id: str | None) -> str | None:
    fid = (file_id or '').strip()
    if not fid:
        return None
    try:
        ln = DriveStorageService.get_web_view_link_by_file_id(fid)
        return ln or None
    except DriveError:
        return None


def _aggregate_clipboard_columns(aggregate_rows: list[tuple[MerchRoundItem, int]]) -> str:
    sep = ';'
    header = sep.join(['Artikel', 'Variante', 'Stueckzahl', 'Listenpreis_CHF', 'Effektiv_CHF', 'Mitglied_CHF'])
    lines = [header]
    for ri, qty in aggregate_rows:
        attr = _variant_attrs_label(ri.variant.attributes)
        lines.append(
            sep.join(
                [
                    ri.variant.article.name,
                    attr,
                    str(qty),
                    f'{ri.list_price_snapshot_rappen / 100:.2f}',
                    ''
                    if ri.effective_supplier_price_rappen is None
                    else f'{ri.effective_supplier_price_rappen / 100:.2f}',
                    ''
                    if ri.member_price_rappen is None
                    else f'{ri.member_price_rappen / 100:.2f}',
                ]
            )
        )
    return '\n'.join(lines)


def _statistics_season_years_list() -> list[int]:
    min_ts = db.session.query(func.min(func.coalesce(MerchRound.opened_at, MerchRound.created_at))).scalar()
    latest = current_club_season_label_year()
    if min_ts is None:
        return [latest]
    oldest = current_club_season_label_year(min_ts)
    if oldest > latest:
        oldest = latest
    return list(range(latest, oldest - 1, -1))


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
    round_stats = compute_round_statistics(r)
    invoice_web_link = _supplier_invoice_web_link_safe(r.supplier_invoice_drive_file_id)
    invoice_folder_configured = bool(
        (current_app.config.get('MERCH_SUPPLIER_INVOICE_DRIVE_FOLDER_ID') or '').strip()
    )
    aggregate_clipboard_text = _aggregate_clipboard_columns(aggregate_rows)
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
        round_stats=round_stats,
        aggregate_clipboard_text=aggregate_clipboard_text,
        invoice_web_link=invoice_web_link,
        invoice_folder_configured=invoice_folder_configured,
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


@bp.route('/rounds/<int:round_id>/supplier-invoice', methods=['POST'])
@login_required
@marketing_chief_or_admin_required
@limiter.limit('20 per minute', methods=['POST'])
def round_supplier_invoice(round_id: int):
    require_merch_v2_enabled()
    r = MerchRound.query.filter_by(id=round_id).first_or_404()
    if r.status in (MerchRoundStatus.DRAFT, MerchRoundStatus.OPEN, MerchRoundStatus.CANCELLED):
        flash('Lieferantenbeleg ist ab gesperrter Runde (Lock) vorgesehen.', 'error')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    uf = request.files.get('invoice_file')
    invoice_upload = bool(uf and uf.filename)
    total_raw = (request.form.get('invoice_total_chf') or '').strip()
    if not invoice_upload and not total_raw:
        flash('Bitte Datei waehlen oder Rechnungs-Summe eintragen.', 'warning')
        return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    folder_id = (current_app.config.get('MERCH_SUPPLIER_INVOICE_DRIVE_FOLDER_ID') or '').strip()

    changed = False
    if invoice_upload:
        if not folder_id:
            flash('MERCH_SUPPLIER_INVOICE_DRIVE_FOLDER_ID fehlt (Drive-Zielordner).', 'error')
            return redirect(url_for('merch_admin.round_detail', round_id=round_id))
        raw = uf.read()
        if not raw:
            flash('Leere Datei.', 'error')
            return redirect(url_for('merch_admin.round_detail', round_id=round_id))
        try:
            doc = DriveStorageService.upload_document(
                file_stream=io.BytesIO(raw),
                filename_stem=f'merch-lieferant-runde-{round_id}',
                drive_folder_id=folder_id,
                uploader=current_user,
                event_id=None,
                original_filename=uf.filename,
                mime_type=uf.mimetype or 'application/octet-stream',
            )
            r.supplier_invoice_drive_file_id = doc.drive_file_id
            changed = True
        except DriveError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
            return redirect(url_for('merch_admin.round_detail', round_id=round_id))
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error('Merch Lieferantenbeleg Upload: %s', exc, exc_info=True)
            flash('Drive-Upload fehlgeschlagen.', 'error')
            return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    if total_raw:
        try:
            r.supplier_invoice_total_rappen = _subsidy_chf_to_rappen(
                Decimal(total_raw.replace(',', '.'))
            )
            changed = True
        except Exception:
            flash('Rechnungs-Summe CHF ist ungueltig.', 'error')
            return redirect(url_for('merch_admin.round_detail', round_id=round_id))

    if changed:
        db.session.commit()
        if invoice_upload:
            SecurityService.log_audit_event(
                AuditAction.MERCH_SUPPLIER_INVOICE_UPLOADED,
                'merch_round',
                round_id,
                extra_data={'drive_file_id': r.supplier_invoice_drive_file_id},
            )
        flash('Lieferantenbeleg / Summe aktualisiert.', 'success')
    return redirect(url_for('merch_admin.round_detail', round_id=round_id))


@bp.route('/statistics', methods=['GET'])
@login_required
@merch_statistics_view_required
def statistics_year():
    require_merch_v2_enabled()
    args = request.args.to_dict(flat=True)
    args['tab'] = 'statistik'
    return redirect(url_for('merch_admin.cockpit', **args))


@bp.route('/statistics/export.csv', methods=['GET'])
@login_required
@merch_statistics_view_required
def statistics_export_csv():
    require_merch_v2_enabled()
    years = _statistics_season_years_list()
    requested = request.args.get('year', type=int)
    year = requested if requested is not None else current_club_season_label_year()
    if years and year not in years:
        year = years[0]
    ov = build_year_overview(year)
    buf = StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow(['Vereinsjahr_Kennzahl', ov.season_label_year])
    w.writerow(['Runden_Anzahl', ov.rounds_count])
    w.writerow(['Bestellungen_Anzahl_Aktive', ov.orders_active_count])
    w.writerow(['Besteller_Unterschiedlich', ov.buyers_distinct])
    w.writerow(['Brutto_Mitgliederpreise_Rappen', ov.gross_rappen])
    w.writerow(['Subventionsverbrauch_Rappen', ov.subsidy_rappen])
    w.writerow(['Lieferanten_Kosten_Stueck_Summe_Rappen', ov.supplier_cost_rappen])
    w.writerow(['Marge_Rappen', ov.margin_rappen])
    w.writerow(['Vereins_Netto_Rappen', ov.club_net_rappen])
    for title, sub in ov.subsidy_by_round_title:
        safe = ''.join(c if c.isalnum() or c in '-_' else '_' for c in title)[:72]
        w.writerow([f'Subvention_Runde_{safe}', sub])
    data = buf.getvalue().encode('utf-8-sig')
    resp = Response(data, mimetype='text/csv; charset=utf-8')
    resp.headers['Content-Disposition'] = (
        f'attachment; filename=merch-jahresreport-{ov.season_label_year}.csv'
    )
    return resp