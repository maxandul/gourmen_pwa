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
    BookingForm,
    ReceiptUploadForm,
    RevisionCommentForm,
)
from backend.models.accounting import (
    Account,
    Booking,
    FiscalYear,
    Receipt,
)
from backend.models.event import Event
from backend.models.member import Member
from backend.services.accounting import (
    AccountingError,
    AccountingService,
    AccountingValidationError,
)
from backend.services.drive_storage import DriveError, DriveValidationError

bp = Blueprint('accounting', __name__)

VALID_TABS = ('journal', 'belege', 'budget', 'abschluss')


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


def _group_budget_rows(rows: list[dict]) -> list[dict]:
    """Budget-Zeilen nach Kontengruppe gruppieren (Reihenfolge erhalten)."""
    groups: list[dict] = []
    by_name: dict[str, dict] = {}
    for row in rows:
        group_name = row['account'].group_name or 'Ohne Gruppe'
        group = by_name.get(group_name)
        if group is None:
            group = {
                'name': group_name,
                'kind': row['account'].kind,
                'rows': [],
                'budget_rappen': 0,
                'actual_rappen': 0,
            }
            by_name[group_name] = group
            groups.append(group)
        group['rows'].append(row)
        group['budget_rappen'] += row['budget_rappen']
        group['actual_rappen'] += row['actual_rappen']
    for group in groups:
        group['deviation_rappen'] = group['actual_rappen'] - group['budget_rappen']
    return groups


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
            active_tab='journal',
            is_treasurer=_is_treasurer(),
            is_reviewer=_is_reviewer(),
        )

    active_tab = request.args.get('tab', 'journal')
    if active_tab not in VALID_TABS:
        active_tab = 'journal'

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

    budget_groups = _group_budget_rows(
        AccountingService.get_budget_vs_actual(fy.id)
    )

    comments = AccountingService.get_comments_for_year(fy.id)
    comment_form = RevisionCommentForm()

    filter_account = (
        db.session.get(Account, filter_account_id) if filter_account_id else None
    )
    filter_event = (
        db.session.get(Event, filter_event_id) if filter_event_id else None
    )

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
        events_for_filter=_events_for_year(fy),
        filter_account_id=filter_account_id,
        filter_account=filter_account,
        filter_direction=filter_direction,
        filter_receipt_status=filter_receipt_status,
        filter_event_id=filter_event_id,
        filter_event=filter_event,
        abschluss_phase=fy.abschluss_phase,
        is_treasurer=_is_treasurer(),
        is_reviewer=_is_reviewer(),
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
        AccountingService.update_booking(
            booking.id,
            booking_date=form.booking_date.data,
            description=form.description.data,
            amount_rappen=form.amount_rappen,
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


def _receipt_upload_form_with_choices(year: int) -> ReceiptUploadForm:
    form = ReceiptUploadForm()
    form.suggested_account_id.choices = [(0, '–')] + [
        (a.id, a.name)
        for a in AccountingService.get_active_accounts(kind='expense')
    ]
    events = (
        Event.query.filter(
            Event.datum >= datetime(year, 1, 1),
            Event.datum < datetime(year + 1, 1, 1),
        )
        .order_by(Event.datum.desc())
        .all()
    )
    form.suggested_event_id.choices = [(0, '–')] + [
        (e.id, f'{e.display_date} {e.restaurant or e.event_typ.value}')
        for e in events
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
            )
            flash('Beleg eingereicht. Der Schatzmeister prüft und verbucht ihn.', 'success')
            return redirect(url_for('member.receipts'))
        except (AccountingError, DriveValidationError) as exc:
            flash(str(exc), 'error')
        except DriveError:
            current_app.logger.error('Beleg-Upload fehlgeschlagen', exc_info=True)
            flash('Upload fehlgeschlagen. Bitte später erneut versuchen.', 'error')

    return render_template('accounting/receipt_upload.html', form=form)


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
            booking = AccountingService.create_booking(
                fiscal_year_id=fy.id,
                booking_date=form.booking_date.data,
                description=form.description.data,
                amount_rappen=form.amount_rappen,
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
