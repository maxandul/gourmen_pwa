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
from backend.models.member import Funktion, Member
from backend.services.accounting import (
    AccountingError,
    AccountingService,
    AccountingValidationError,
)
from backend.services.accounting_pdf import AccountingPdfService
from backend.services.drive_storage import (
    DriveError,
    DriveStorageService,
    DriveValidationError,
)
from backend.services.notifier import NotifierService

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

    budget_groups = AccountingService.get_budget_grouped(fy.id)

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

    is_treasurer = _is_treasurer()
    contributions = (
        AccountingService.get_member_contributions(fy.id) if is_treasurer else []
    )

    return render_template(
        'accounting/stats.html',
        fiscal_year=fy,
        fiscal_years=AccountingService.get_all_fiscal_years(),
        chart_data=chart_data,
        budget_usage=budget_usage,
        comparison=comparison,
        contributions=contributions,
        is_treasurer=is_treasurer,
    )


# ---------------------------------------------------------------------------
# Revisions-Workflow (Jahresfreigabe und Bestätigung)
# ---------------------------------------------------------------------------


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
