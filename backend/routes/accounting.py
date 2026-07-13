"""Accounting-Blueprint – Buchhaltungsmodul (Phase 4).

Spezifikation: docs/capabilities/accounting.md (Routes: Sektion 16,
Berechtigungen: Sektion 5). Routes enthalten keine Geschäftslogik –
alles läuft über AccountingService.
"""

from datetime import date, datetime

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError

from backend.extensions import db, limiter
from backend.forms.accounting import (
    AccountForm,
    BankImportForm,
    BookingForm,
    ReceiptUploadForm,
    RevisionCommentForm,
)
from backend.models.accounting import (
    Account,
    Booking,
    ClaimStatus,
    ClaimType,
    FiscalYear,
    FiscalYearStatus,
    MemberClaim,
    Receipt,
)
from backend.models.event import Event
from backend.models.member import Funktion, Member
from backend.services.accounting import (
    AccountingError,
    AccountingService,
    AccountingValidationError,
)
from backend.services.bank_import import BankImportService
from backend.services.accounting_pdf import AccountingPdfService
from backend.services.drive_storage import (
    DriveError,
    DriveStorageService,
    DriveValidationError,
)
from backend.services.notifier import NotifierService

bp = Blueprint('accounting', __name__)

VALID_TABS = (
    'uebersicht', 'journal', 'belege', 'import', 'posten', 'budget',
    'abschluss', 'statistik', 'kontenplan',
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_funktion(*funktionen) -> None:
    """Berechtigungs-Guard: Admin kommt immer durch (Capability 3.8)."""
    if not current_user.is_authenticated:
        abort(403)
    if not current_user.is_admin() and not any(
        current_user.has_funktion(f) for f in funktionen
    ):
        abort(403)


def _validate_csrf_or_403() -> None:
    token = (
        request.form.get('csrf_token')
        or request.headers.get('X-CSRFToken')
        or request.headers.get('X-CSRF-Token')
    )
    try:
        validate_csrf(token)
    except (ValidationError, Exception):
        abort(403)


def _is_treasurer() -> bool:
    return current_user.is_admin() or current_user.has_funktion('SCHATZMEISTER')


def _is_reviewer() -> bool:
    return current_user.has_funktion('RECHNUNGSPRUEFER')


def _resolve_fiscal_year() -> FiscalYear | None:
    """Gewähltes Jahr aus `?year=<id>`, sonst aktuellstes Jahr."""
    year_id = request.args.get('year', type=int)
    if year_id:
        return db.session.get(FiscalYear, year_id)
    return FiscalYear.query.order_by(FiscalYear.year.desc()).first()


def _truncate_label(text: str, max_len: int = 36) -> str:
    text = (text or '').strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + '…'


def _build_stats_context(fy: FiscalYear, is_treasurer: bool) -> dict:
    timeline = AccountingService.get_saldo_timeline(fy.id)
    comparison = AccountingService.get_year_comparison()
    budget_groups = AccountingService.get_budget_grouped(fy.id)

    budget_usage = []
    for group in budget_groups:
        if group['budget_rappen'] <= 0:
            continue
        pct = round(group['actual_rappen'] / group['budget_rappen'] * 100)
        budget_usage.append({**group, 'pct': pct, 'pct_capped': min(pct, 100)})

    expense_groups = [
        g for g in budget_groups
        if g['kind'].value == 'expense' and g['actual_rappen'] > 0
    ]

    chart_data = {
        'saldo': {
            'labels': timeline['labels'],
            'values': [round(v / 100, 2) for v in timeline['values_rappen']],
        },
        'years': {
            'labels': [str(e['year']) for e in comparison],
            'income': [round(e['income_rappen'] / 100, 2) for e in comparison],
            'expense': [round(e['expense_rappen'] / 100, 2) for e in comparison],
            'result': [round(e['result_rappen'] / 100, 2) for e in comparison],
        },
        'donut': {
            'labels': [g['name'] for g in expense_groups],
            'values': [round(g['actual_rappen'] / 100, 2) for g in expense_groups],
        },
    }

    return {
        'chart_data': chart_data,
        'budget_usage': budget_usage,
        'comparison': comparison,
        'contributions': (
            AccountingService.get_member_contributions(fy.id) if is_treasurer else []
        ),
    }


def _events_for_year(fy: FiscalYear) -> list[Event]:
    return (
        Event.query.filter(
            Event.datum >= datetime(fy.year, 1, 1),
            Event.datum < datetime(fy.year + 1, 1, 1),
        )
        .order_by(Event.datum.desc())
        .all()
    )


def _booking_form_with_choices(fy: FiscalYear, obj=None) -> BookingForm:
    form = BookingForm(obj=obj)
    form.account_id.choices = [
        (a.id, f'{a.code} {a.name}') for a in AccountingService.get_active_accounts()
    ]
    form.event_id.choices = [(0, '–')] + [
        (e.id, f'{e.display_date} {e.restaurant or e.event_typ.value}')
        for e in _events_for_year(fy)
    ]
    form.member_id.choices = [(0, '–')] + [
        (m.id, m.display_name_with_spirit)
        for m in Member.query.filter_by(is_active=True)
        .order_by(Member.vorname, Member.nachname)
        .all()
    ]
    return form


# ---------------------------------------------------------------------------
# Tab-Index
# ---------------------------------------------------------------------------


@bp.route('/')
@login_required
def index():
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')

    fiscal_years = AccountingService.get_all_fiscal_years()
    accounts = AccountingService.get_active_accounts()
    fy = _resolve_fiscal_year()

    if fy is None or not accounts:
        return render_template(
            'accounting/index.html',
            fiscal_year=None,
            fiscal_years=fiscal_years,
            needs_seed=True,
            active_tab='uebersicht',
            is_treasurer=_is_treasurer(),
            is_reviewer=_is_reviewer(),
        )

    active_tab = request.args.get('tab', 'uebersicht')
    if active_tab not in VALID_TABS:
        active_tab = 'uebersicht'
    if active_tab == 'kontenplan' and not current_user.is_admin():
        abort(403)

    is_treasurer = _is_treasurer()
    is_reviewer = _is_reviewer()
    if active_tab == 'import' and not is_treasurer:
        abort(403)
    summary = AccountingService.get_year_summary(fy.id)

    # Journal-Filter
    filter_account_id = request.args.get('konto', type=int)
    filter_direction = request.args.get('richtung') or None
    if filter_direction not in ('in', 'out'):
        filter_direction = None
    bookings = AccountingService.get_journal(
        fy.id, account_id=filter_account_id, direction=filter_direction
    )

    # Belege-Filter
    filter_receipt_status = request.args.get('status') or None
    if filter_receipt_status not in ('offen', 'verbucht'):
        filter_receipt_status = None
    filter_event_id = request.args.get('event', type=int)
    booked = None
    if filter_receipt_status == 'offen':
        booked = False
    elif filter_receipt_status == 'verbucht':
        booked = True
    receipts = AccountingService.get_receipts_with_filters(
        booked=booked, event_id=filter_event_id
    )

    budget_groups = AccountingService.get_budget_grouped(fy.id)

    comments = AccountingService.get_comments_for_year(fy.id)
    comment_form = RevisionCommentForm()

    filter_account = (
        db.session.get(Account, filter_account_id) if filter_account_id else None
    )
    filter_event = (
        db.session.get(Event, filter_event_id) if filter_event_id else None
    )

    stats_ctx = _build_stats_context(fy, is_treasurer)

    # Import-Tab (Schatzmeister): Import-Historie + offene Transaktionen
    bank_imports = BankImportService.get_imports() if is_treasurer else []
    pending_tx_count = (
        len(BankImportService.get_pending_transactions()) if is_treasurer else 0
    )
    import_form = BankImportForm() if is_treasurer else None

    # Offene-Posten-Tab: Übersicht pro Mitglied
    claims_overview = AccountingService.get_claims_overview()
    membership_claims_missing = bool(
        is_treasurer
        and fy.membership_fee_rappen
        and not MemberClaim.query.filter_by(
            fiscal_year_id=fy.id, claim_type=ClaimType.MITGLIEDERBEITRAG,
        ).first()
    )

    account_form = AccountForm()
    all_accounts = []
    next_fiscal_year = None
    if current_user.is_admin():
        all_accounts = Account.query.order_by(Account.sort_order, Account.code).all()
        max_year = max(fy.year for fy in fiscal_years) if fiscal_years else fy.year
        candidate = max_year + 1
        if not FiscalYear.query.filter_by(year=candidate).first():
            next_fiscal_year = candidate

    return render_template(
        'accounting/index.html',
        fiscal_year=fy,
        fiscal_years=fiscal_years,
        needs_seed=False,
        active_tab=active_tab,
        summary=summary,
        bookings=bookings,
        receipts=receipts,
        budget_groups=budget_groups,
        comments=comments,
        comment_form=comment_form,
        accounts=accounts,
        all_accounts=all_accounts,
        account_form=account_form,
        next_fiscal_year=next_fiscal_year,
        events_for_filter=_events_for_year(fy),
        filter_account_id=filter_account_id,
        filter_account=filter_account,
        filter_direction=filter_direction,
        filter_receipt_status=filter_receipt_status,
        filter_event_id=filter_event_id,
        filter_event=filter_event,
        abschluss_phase=fy.abschluss_phase,
        is_treasurer=is_treasurer,
        is_reviewer=is_reviewer,
        bank_imports=bank_imports,
        pending_tx_count=pending_tx_count,
        import_form=import_form,
        claims_overview=claims_overview,
        membership_claims_missing=membership_claims_missing,
        **stats_ctx,
    )


# ---------------------------------------------------------------------------
# Buchungen
# ---------------------------------------------------------------------------


@bp.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id: int):
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    booking = Booking.query.get_or_404(booking_id)
    fy = booking.fiscal_year

    can_edit = _is_treasurer() and fy.is_open
    form = _booking_form_with_choices(fy, obj=booking) if can_edit else None
    if form is not None and request.method == 'GET':
        form.amount_chf.data = booking.amount_rappen / 100
        form.direction.data = booking.direction.value
        form.event_id.data = booking.event_id or 0
        form.member_id.data = booking.member_id or 0

    unbooked_receipts = AccountingService.get_inbox() if can_edit else []

    return render_template(
        'accounting/booking_detail.html',
        booking=booking,
        fiscal_year=fy,
        form=form,
        can_edit=can_edit,
        unbooked_receipts=unbooked_receipts,
        comment_form=RevisionCommentForm(),
        is_treasurer=_is_treasurer(),
        is_reviewer=_is_reviewer(),
    )


@bp.route('/booking/<int:booking_id>/edit', methods=['POST'])
@login_required
def booking_edit(booking_id: int):
    _require_funktion('SCHATZMEISTER')
    booking = Booking.query.get_or_404(booking_id)
    form = _booking_form_with_choices(booking.fiscal_year)

    if not form.validate_on_submit():
        flash('Bitte Eingaben prüfen.', 'error')
        return redirect(url_for('accounting.booking_detail', booking_id=booking.id))

    try:
        amount_rappen = form.amount_rappen
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.booking_detail', booking_id=booking.id))

    try:
        AccountingService.update_booking(
            booking.id,
            booking_date=form.booking_date.data,
            description=form.description.data,
            amount_rappen=amount_rappen,
            direction=form.direction.data,
            account_id=form.account_id.data,
            event_id=form.event_id.data or None,
            member_id=form.member_id.data or None,
        )
        flash('Buchung aktualisiert.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('accounting.booking_detail', booking_id=booking.id))


@bp.route('/booking/<int:booking_id>/receipt', methods=['POST'])
@login_required
def booking_attach_receipt(booking_id: int):
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    booking = Booking.query.get_or_404(booking_id)
    receipt_id = request.form.get('receipt_id', type=int)
    if not receipt_id:
        flash('Kein Beleg gewählt.', 'error')
        return redirect(url_for('accounting.booking_detail', booking_id=booking.id))
    try:
        AccountingService.attach_receipt_to_booking(receipt_id, booking.id)
        flash('Beleg verknüpft.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('accounting.booking_detail', booking_id=booking.id))


# ---------------------------------------------------------------------------
# Beleg-Upload (alle aktiven Mitglieder) und Beleg-Anzeige
# ---------------------------------------------------------------------------


def _open_year_bookings() -> list[Booking]:
    return (
        Booking.query.join(FiscalYear, Booking.fiscal_year_id == FiscalYear.id)
        .filter(FiscalYear.status == FiscalYearStatus.OPEN)
        .order_by(Booking.booking_date.desc(), Booking.id.desc())
        .limit(50)
        .all()
    )


def _receipt_upload_form_with_choices(year: int) -> ReceiptUploadForm:
    form = ReceiptUploadForm()
    form.suggested_account_id.choices = [(0, '–')] + [
        (a.id, _truncate_label(a.name, 40))
        for a in AccountingService.get_active_accounts(kind='expense')
    ]
    cutoff = datetime(year - 1, 1, 1)
    events = (
        Event.query.filter(Event.datum >= cutoff)
        .order_by(Event.datum.desc())
        .limit(20)
        .all()
    )
    form.suggested_event_id.choices = [(0, '–')] + [
        (
            e.id,
            _truncate_label(
                f'{e.display_date} {e.restaurant or e.event_typ.value}', 40
            ),
        )
        for e in events
    ]
    form.booking_id.choices = [(0, '–')] + [
        (
            b.id,
            _truncate_label(
                f'{b.booking_date.strftime("%d.%m.%Y")} · '
                f'{b.description} · CHF {b.amount_rappen / 100:.2f}',
                48,
            ),
        )
        for b in _open_year_bookings()
    ]
    return form


@bp.route('/receipt/upload', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per minute", methods=['POST'])
def receipt_upload():
    if not current_user.is_active:
        abort(403)

    year = date.today().year
    form = _receipt_upload_form_with_choices(year)

    # Kontext: Aufruf aus einer Buchung (Schatzmeister erfasst Beleg direkt)
    context_booking_id = request.args.get('booking', type=int)
    context_booking = (
        db.session.get(Booking, context_booking_id) if context_booking_id else None
    )
    if request.method == 'GET' and context_booking is not None:
        form.booking_id.data = context_booking.id

    if form.validate_on_submit():
        fy = AccountingService.get_or_create_fiscal_year(year)
        try:
            AccountingService.upload_receipt(
                file=form.file.data,
                uploader=current_user,
                fiscal_year_id=fy.id,
                suggested_account_id=form.suggested_account_id.data or None,
                suggested_event_id=form.suggested_event_id.data or None,
                comment=form.comment.data,
                display_name=form.display_name.data,
                booking_id=form.booking_id.data or None,
            )
            if form.booking_id.data:
                flash('Beleg eingereicht und mit der Buchung verknüpft.', 'success')
                return redirect(url_for(
                    'accounting.booking_detail', booking_id=form.booking_id.data
                ))
            flash('Beleg eingereicht. Der Schatzmeister prüft und verbucht ihn.', 'success')
            return redirect(url_for('member.receipts'))
        except (AccountingError, DriveValidationError) as exc:
            flash(str(exc), 'error')
        except DriveError:
            current_app.logger.error('Beleg-Upload fehlgeschlagen', exc_info=True)
            flash('Upload fehlgeschlagen. Bitte später erneut versuchen.', 'error')

    return render_template(
        'accounting/receipt_upload.html',
        form=form,
        context_booking=context_booking,
    )


@bp.route('/receipt/<int:receipt_id>')
@login_required
def receipt_view(receipt_id: int):
    receipt = Receipt.query.get_or_404(receipt_id)
    is_uploader = receipt.uploader_id == current_user.id
    if not is_uploader:
        _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    try:
        payload, mime, name = AccountingService.download_receipt(receipt)
    except DriveError:
        current_app.logger.error('Beleg-Download fehlgeschlagen', exc_info=True)
        flash('Beleg konnte nicht aus Drive geladen werden.', 'error')
        return redirect(request.referrer or url_for('accounting.index'))
    return Response(
        payload,
        mimetype=mime,
        headers={'Content-Disposition': f'inline; filename="{name}"'},
    )


# ---------------------------------------------------------------------------
# Buchungsworkflow (Schatzmeister)
# ---------------------------------------------------------------------------


@bp.route('/booking/new', methods=['GET', 'POST'])
@login_required
def booking_new():
    _require_funktion('SCHATZMEISTER')

    fy = _resolve_fiscal_year()
    if fy is None:
        flash('Kein Geschäftsjahr vorhanden. Bitte Seed-Script ausführen.', 'error')
        return redirect(url_for('accounting.index'))

    receipt = None
    receipt_id = request.args.get('receipt', type=int) or request.form.get(
        'receipt_id', type=int
    )
    if receipt_id:
        receipt = db.session.get(Receipt, receipt_id)

    form = _booking_form_with_choices(fy)

    if request.method == 'GET':
        form.booking_date.data = date.today()
        if receipt is not None:
            if receipt.suggested_account_id:
                form.account_id.data = receipt.suggested_account_id
                form.direction.data = 'out'
            if receipt.suggested_event_id:
                form.event_id.data = receipt.suggested_event_id
            if receipt.comment:
                form.description.data = receipt.comment[:255]

    if form.validate_on_submit():
        try:
            amount_rappen = form.amount_rappen
        except ValueError as exc:
            flash(str(exc), 'error')
        else:
            try:
                booking = AccountingService.create_booking(
                    fiscal_year_id=fy.id,
                    booking_date=form.booking_date.data,
                    description=form.description.data,
                    amount_rappen=amount_rappen,
                    direction=form.direction.data,
                    account_id=form.account_id.data,
                    event_id=form.event_id.data or None,
                    member_id=form.member_id.data or None,
                    created_by=current_user,
                )
                if receipt is not None and not receipt.is_booked:
                    AccountingService.attach_receipt_to_booking(receipt.id, booking.id)
                flash('Buchung erfasst.', 'success')
                return redirect(url_for('accounting.booking_detail', booking_id=booking.id))
            except AccountingError as exc:
                flash(str(exc), 'error')
    elif request.method == 'POST':
        flash('Bitte Eingaben prüfen.', 'error')

    return render_template(
        'accounting/booking_new.html',
        form=form,
        fiscal_year=fy,
        receipt=receipt,
    )


# ---------------------------------------------------------------------------
# Revisions-Kommentare
# ---------------------------------------------------------------------------


@bp.route('/year/<int:fiscal_year_id>/comment', methods=['POST'])
@login_required
def year_comment(fiscal_year_id: int):
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    form = RevisionCommentForm()
    booking_id = request.form.get('booking_id', type=int)

    if form.validate_on_submit():
        try:
            AccountingService.add_revision_comment(
                booking_id=booking_id,
                fiscal_year_id=None if booking_id else fy.id,
                author=current_user,
                text=form.text.data,
            )
            flash('Kommentar gespeichert.', 'success')
        except AccountingError as exc:
            flash(str(exc), 'error')
    else:
        flash('Kommentar darf nicht leer sein.', 'error')

    if booking_id:
        return redirect(url_for('accounting.booking_detail', booking_id=booking_id))
    return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))


@bp.route('/comment/<int:comment_id>/resolve', methods=['POST'])
@login_required
def comment_resolve(comment_id: int):
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    _validate_csrf_or_403()
    try:
        comment = AccountingService.resolve_comment(comment_id)
        flash('Kommentar als erledigt markiert.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index'))
    if comment.booking_id:
        return redirect(
            url_for('accounting.booking_detail', booking_id=comment.booking_id)
        )
    return redirect(
        url_for('accounting.index', year=comment.fiscal_year_id, tab='abschluss')
    )


# ---------------------------------------------------------------------------
# Export (CSV / PDF)
# ---------------------------------------------------------------------------


@bp.route('/export/<int:fiscal_year_id>/csv')
@login_required
def export_csv(fiscal_year_id: int):
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    csv_payload = AccountingService.export_csv(fy.id)
    return Response(
        csv_payload,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="Buchhaltung_{fy.year}.csv"'
        },
    )


@bp.route('/export/<int:fiscal_year_id>/pdf')
@login_required
def export_pdf(fiscal_year_id: int):
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    pdf_payload = AccountingPdfService.generate_report(fy)
    return Response(
        pdf_payload,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="Jahresabschluss_{fy.year}.pdf"'
        },
    )


# ---------------------------------------------------------------------------
# Kontenplan-Verwaltung (Admin)
# ---------------------------------------------------------------------------


@bp.route('/accounts', methods=['GET', 'POST'])
@login_required
def accounts():
    if not current_user.is_admin():
        abort(403)

    year_id = request.args.get('year', type=int)
    redirect_kwargs = {'tab': 'kontenplan', '_anchor': 'gourmen-tabs'}
    if year_id:
        redirect_kwargs['year'] = year_id

    if request.method == 'GET':
        return redirect(url_for('accounting.index', **redirect_kwargs))

    form = AccountForm()
    if form.validate_on_submit():
        try:
            AccountingService.create_account(
                code=form.code.data,
                name=form.name.data,
                kind=form.kind.data,
                group_name=form.group_name.data,
            )
            flash(f'Konto {form.code.data} angelegt.', 'success')
            return redirect(url_for('accounting.index', **redirect_kwargs))
        except AccountingError as exc:
            flash(str(exc), 'error')
    else:
        flash('Bitte Eingaben prüfen.', 'error')
    return redirect(url_for('accounting.index', **redirect_kwargs))


@bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def account_edit(account_id: int):
    if not current_user.is_admin():
        abort(403)

    account = Account.query.get_or_404(account_id)
    form = AccountForm(obj=account)
    if request.method == 'GET':
        form.kind.data = account.kind.value

    if form.validate_on_submit():
        try:
            AccountingService.update_account(
                account.id,
                code=form.code.data,
                name=form.name.data,
                kind=form.kind.data,
                group_name=form.group_name.data,
                is_active=form.is_active.data,
            )
            flash(f'Konto {form.code.data} gespeichert.', 'success')
            return redirect(url_for(
                'accounting.index', tab='kontenplan', _anchor='gourmen-tabs',
            ))
        except AccountingError as exc:
            flash(str(exc), 'error')
    elif request.method == 'POST':
        flash('Bitte Eingaben prüfen.', 'error')

    return render_template('accounting/account_edit.html', form=form, account=account)


# ---------------------------------------------------------------------------
# Statistik
# ---------------------------------------------------------------------------


@bp.route('/stats')
@login_required
def stats():
    _require_funktion('SCHATZMEISTER', 'RECHNUNGSPRUEFER')
    fy = _resolve_fiscal_year()
    if fy is None:
        flash('Kein Geschäftsjahr vorhanden. Bitte Seed-Script ausführen.', 'error')
        return redirect(url_for('accounting.index'))
    return redirect(url_for(
        'accounting.index',
        year=fy.id,
        tab='statistik',
        _anchor='gourmen-tabs',
    ))


# ---------------------------------------------------------------------------
# Revisions-Workflow (Jahresfreigabe und Bestätigung)
# ---------------------------------------------------------------------------


@bp.route('/year/<int:fiscal_year_id>/withdraw', methods=['POST'])
@login_required
def year_withdraw(fiscal_year_id: int):
    """Freigabe zurückziehen: in_review → open."""
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    try:
        AccountingService.withdraw_from_review(fy.id, current_user)
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))
    flash(
        f'Jahr {fy.year} ist wieder offen. Buchungen und Belege können bearbeitet werden.',
        'success',
    )
    return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))


@bp.route('/year/<int:fiscal_year_id>/revoke', methods=['POST'])
@login_required
def year_revoke(fiscal_year_id: int):
    """Abschluss rückgängig: closed → in_review."""
    _require_funktion('RECHNUNGSPRUEFER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    try:
        AccountingService.revoke_approval(fy.id, current_user)
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))
    flash(
        f'Abschluss {fy.year} rückgängig. Das Jahr ist wieder in Prüfung.',
        'success',
    )
    return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))


@bp.route('/year/create', methods=['POST'])
@login_required
def year_create():
    """Neues Geschäftsjahr anlegen (Admin)."""
    if not current_user.is_admin():
        abort(403)
    _validate_csrf_or_403()
    year = request.form.get('year', type=int)
    if not year:
        flash('Ungültiges Jahr.', 'error')
        return redirect(url_for('accounting.index'))
    try:
        fy = AccountingService.create_fiscal_year(year, current_user)
        flash(
            f'Geschäftsjahr {fy.year} eröffnet. Der Budget-Vorschlag basiert auf den '
            'Vorjahres-Zahlen und kann im Budget-Tab angepasst werden.',
            'success',
        )
        return redirect(url_for('accounting.index', year=fy.id, tab='uebersicht'))
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index'))


@bp.route('/year/<int:fiscal_year_id>/submit', methods=['POST'])
@login_required
def year_submit(fiscal_year_id: int):
    """Jahr zur Revision freigeben (Schatzmeister/Admin) → in_review."""
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    try:
        AccountingService.submit_for_review(fy.id, current_user)
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))

    reviewers = Member.query.filter_by(
        funktion=Funktion.RECHNUNGSPRUEFER, is_active=True
    ).all()
    for reviewer in reviewers:
        try:
            NotifierService.send_push_notification(
                reviewer.id,
                f'Revision {fy.year} bereit',
                f'Der Schatzmeister hat das Geschäftsjahr {fy.year} zur Prüfung freigegeben.',
                data={'url': url_for('accounting.index', year=fy.id, tab='abschluss')},
                notification_type='accounting',
            )
        except Exception:
            current_app.logger.warning(
                'Revisor-Notification fehlgeschlagen (Member %s)', reviewer.id,
                exc_info=True,
            )

    flash(f'Jahr {fy.year} ist zur Prüfung freigegeben. Der Revisor wurde benachrichtigt.', 'success')
    return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))


@bp.route('/year/<int:fiscal_year_id>/approve', methods=['POST'])
@login_required
def year_approve(fiscal_year_id: int):
    """Jahr bestätigen (Revisor) → closed + Revisorenbericht-PDF in Drive."""
    _require_funktion('RECHNUNGSPRUEFER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    try:
        fy = AccountingService.approve_year(fy.id, current_user)
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))

    try:
        pdf_bytes = AccountingPdfService.generate_report(
            fy, approval=fy.revision_approval
        )
        folder_id = AccountingService.get_receipt_folder_id(fy.year)
        drive_meta = DriveStorageService.upload_bytes(
            payload=pdf_bytes,
            filename_stem=f'Revisorenbericht_{fy.year}',
            drive_folder_id=folder_id,
            mime_type='application/pdf',
            extension='pdf',
            actor=current_user,
        )
        AccountingService.set_approval_report(fy.id, drive_meta['id'])
        flash(f'Jahr {fy.year} bestätigt. Revisorenbericht wurde in Drive abgelegt.', 'success')
    except Exception:
        current_app.logger.error(
            'Revisorenbericht-Upload fehlgeschlagen (Jahr %s)', fy.year, exc_info=True
        )
        flash(
            f'Jahr {fy.year} ist bestätigt, aber der Revisorenbericht konnte nicht '
            'in Drive abgelegt werden. Bitte Admin informieren.',
            'warning',
        )
    return redirect(url_for('accounting.index', year=fy.id, tab='abschluss'))


# ---------------------------------------------------------------------------
# ZKB-Kontoauszug-Import (Schatzmeister) – Spec Sektion 11
# ---------------------------------------------------------------------------


def _review_context(pending):
    """Wahl-Listen für den Review-Screen (Konten, Mitglieder, offene Posten)."""
    accounts = AccountingService.get_active_accounts()
    members = (
        Member.query.filter_by(is_active=True)
        .order_by(Member.vorname, Member.nachname)
        .all()
    )
    open_claims = (
        MemberClaim.query.filter(
            MemberClaim.creditor_member_id.is_(None),
            MemberClaim.status.in_((ClaimStatus.OFFEN, ClaimStatus.TEILWEISE)),
        )
        .order_by(MemberClaim.created_at)
        .all()
    )
    years = {tx.booked_date.year for tx in pending}
    events = []
    if years:
        events = (
            Event.query.filter(
                Event.datum >= datetime(min(years), 1, 1),
                Event.datum < datetime(max(years) + 1, 1, 1),
            )
            .order_by(Event.datum.desc())
            .all()
        )
    # Vorgeschlagener Posten pro Transaktion (exakter Betrag / ältester Posten)
    suggested_claims = {}
    for tx in pending:
        if tx.suggested_member is not None and tx.is_income:
            claim = BankImportService.match_open_claim(
                tx.suggested_member, tx.amount_rappen
            )
            if claim is not None:
                suggested_claims[tx.id] = claim.id
    return {
        'accounts': accounts,
        'members': members,
        'open_claims': open_claims,
        'events': events,
        'suggested_claims': suggested_claims,
    }


@bp.route('/import', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def bank_import_upload():
    _require_funktion('SCHATZMEISTER')
    form = BankImportForm()
    if not form.validate_on_submit():
        flash('Bitte CSV-Datei auswählen.', 'error')
        return redirect(url_for('accounting.index', tab='import', _anchor='gourmen-tabs'))
    try:
        statement = BankImportService.import_statement(form.file.data, current_user)
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', tab='import', _anchor='gourmen-tabs'))
    flash(
        f'{statement.filename}: {statement.new_count} neue Transaktionen, '
        f'{statement.duplicate_count} bereits bekannt.',
        'success',
    )
    if statement.pending_count:
        return redirect(url_for('accounting.bank_import_review', import_id=statement.id))
    return redirect(url_for('accounting.index', tab='import', _anchor='gourmen-tabs'))


@bp.route('/import/<int:import_id>/review')
@login_required
def bank_import_review(import_id: int):
    _require_funktion('SCHATZMEISTER')
    try:
        statement = BankImportService.get_statement(import_id)
    except AccountingError:
        abort(404)
    pending = BankImportService.get_pending_transactions(statement.id)
    return render_template(
        'accounting/import_review.html',
        statement=statement,
        pending=pending,
        **_review_context(pending),
    )


@bp.route('/import/review')
@login_required
def bank_review_all():
    """Alle offenen Transaktionen (import-übergreifend)."""
    _require_funktion('SCHATZMEISTER')
    pending = BankImportService.get_pending_transactions()
    return render_template(
        'accounting/import_review.html',
        statement=None,
        pending=pending,
        **_review_context(pending),
    )


def _review_redirect(tx):
    if request.form.get('all') == '1':
        return redirect(url_for('accounting.bank_review_all'))
    return redirect(url_for('accounting.bank_import_review', import_id=tx.import_id))


@bp.route('/import/tx/<int:tx_id>/book', methods=['POST'])
@login_required
def bank_tx_book(tx_id: int):
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    tx = BankImportService.get_transaction(tx_id)
    account_id = request.form.get('account_id', type=int)
    if not account_id:
        flash('Bitte ein Konto wählen.', 'error')
        return _review_redirect(tx)
    try:
        booking = BankImportService.book_transaction(
            tx.id,
            account_id=account_id,
            member_id=request.form.get('member_id', type=int) or None,
            event_id=request.form.get('event_id', type=int) or None,
            claim_id=request.form.get('claim_id', type=int) or None,
            booked_by=current_user,
        )
        flash(f'Verbucht: {booking.description} (CHF {booking.amount_rappen / 100:.2f}).', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
    return _review_redirect(tx)


@bp.route('/import/tx/<int:tx_id>/ignore', methods=['POST'])
@login_required
def bank_tx_ignore(tx_id: int):
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    try:
        tx = BankImportService.ignore_transaction(tx_id)
        flash('Transaktion ignoriert.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('accounting.index', tab='import', _anchor='gourmen-tabs'))
    return _review_redirect(tx)


# ---------------------------------------------------------------------------
# Offene Posten (MemberClaims)
# ---------------------------------------------------------------------------


@bp.route('/year/<int:fiscal_year_id>/claims/create', methods=['POST'])
@login_required
def year_claims_create(fiscal_year_id: int):
    """Beitrags-Claims für alle aktiven Mitglieder anlegen."""
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    try:
        created = AccountingService.create_claims_for_fiscal_year(fy.id, current_user)
        flash(f'{len(created)} Beitrags-Posten für {fy.year} angelegt.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('accounting.index', year=fy.id, tab='posten', _anchor='gourmen-tabs'))


@bp.route('/claims/<int:claim_id>/settle', methods=['POST'])
@login_required
def claim_settle(claim_id: int):
    """Posten manuell abschliessen (beglichen oder erlassen)."""
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    waive = request.form.get('waive') == '1'
    try:
        claim = AccountingService.settle_claim(claim_id, waive=waive)
        flash(
            f'Posten «{claim.type_display}» von {claim.member.display_name} '
            f'als {"erlassen" if waive else "beglichen"} markiert.',
            'success',
        )
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('accounting.index', tab='posten', _anchor='gourmen-tabs'))


@bp.route('/claims/<int:claim_id>/confirm', methods=['POST'])
@login_required
def claim_confirm(claim_id: int):
    """Privatzahler bestätigt den Eingang eines Anteils (vom Dashboard)."""
    _validate_csrf_or_403()
    try:
        claim = AccountingService.confirm_private_payment(claim_id, current_user)
        flash(
            f'Eingang von {claim.member.display_name} bestätigt.',
            'success',
        )
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(request.referrer or url_for('dashboard.index'))


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------


@bp.route('/year/<int:fiscal_year_id>/budget', methods=['POST'])
@login_required
def year_budget(fiscal_year_id: int):
    _require_funktion('SCHATZMEISTER')
    _validate_csrf_or_403()
    fy = FiscalYear.query.get_or_404(fiscal_year_id)
    account_id = request.form.get('account_id', type=int)
    amount_raw = (request.form.get('amount_chf') or '').strip().replace(',', '.')
    try:
        amount_rappen = int(round(float(amount_raw or '0') * 100))
    except ValueError:
        flash('Ungültiger Betrag.', 'error')
        return redirect(url_for('accounting.index', year=fy.id, tab='budget'))
    try:
        AccountingService.set_budget(fy.id, account_id, amount_rappen, current_user)
        flash('Budget gespeichert.', 'success')
    except AccountingError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('accounting.index', year=fy.id, tab='budget'))
