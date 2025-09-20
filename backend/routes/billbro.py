from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation, Esstyp
from backend.services.money import MoneyService
from backend.services.ggl_rules import GGLService
from backend.services.security import SecurityService, AuditAction
from backend.services.notifier import NotifierService

def round_to_5_rappen(amount_rappen):
    """Round amount to nearest 5 Rappen (Swiss currency rule)"""
    return int(round(amount_rappen / 5) * 5)

def calculate_weighted_shares(event, gesamtbetrag_rappen):
    """Calculate weighted shares for BillBro participants"""
    sparsam_count = 0
    normal_count = 0
    allin_count = 0
    
    for participation in event.participations:
        if participation.teilnahme and participation.esstyp:
            if participation.esstyp == Esstyp.SPARSAM:
                sparsam_count += 1
            elif participation.esstyp == Esstyp.NORMAL:
                normal_count += 1
            elif participation.esstyp == Esstyp.ALLIN:
                allin_count += 1
    
    total_participants = sparsam_count + normal_count + allin_count
    
    if total_participants > 0:
        # Calculate weighted total
        weighted_total = (sparsam_count * event.billbro_sparsam_weight + 
                         normal_count * event.billbro_normal_weight + 
                         allin_count * event.billbro_allin_weight)
        
        # Calculate shares based on weights
        if sparsam_count > 0:
            event.betrag_sparsam_rappen = round_to_5_rappen(gesamtbetrag_rappen * event.billbro_sparsam_weight / weighted_total)
        else:
            event.betrag_sparsam_rappen = None
            
        if normal_count > 0:
            event.betrag_normal_rappen = round_to_5_rappen(gesamtbetrag_rappen * event.billbro_normal_weight / weighted_total)
        else:
            event.betrag_normal_rappen = None
            
        if allin_count > 0:
            event.betrag_allin_rappen = round_to_5_rappen(gesamtbetrag_rappen * event.billbro_allin_weight / weighted_total)
        else:
            event.betrag_allin_rappen = None
        
        # Update calculated shares for each participation
        for participation in event.participations:
            if participation.teilnahme and participation.esstyp:
                if participation.esstyp == Esstyp.SPARSAM:
                    participation.calculated_share_rappen = event.betrag_sparsam_rappen
                elif participation.esstyp == Esstyp.NORMAL:
                    participation.calculated_share_rappen = event.betrag_normal_rappen
                elif participation.esstyp == Esstyp.ALLIN:
                    participation.calculated_share_rappen = event.betrag_allin_rappen

bp = Blueprint('billbro', __name__)

class BillBroForm(FlaskForm):
    esstyp = SelectField('Ess-Typ', choices=[
        ('', '-- Bitte wählen --'),
        (Esstyp.SPARSAM.value, 'Sparsam'),
        (Esstyp.NORMAL.value, 'Normal'),
        (Esstyp.ALLIN.value, 'All-In')
    ], validators=[DataRequired()], coerce=str)
    guess_amount = StringField('Schätzung (CHF)', validators=[DataRequired()])
    submit = SubmitField('Einloggen')

@bp.route('/')
@login_required
def index():
    """BillBro main page"""
    event_id = request.args.get('event_id', type=int)
    
    if not event_id:
        flash('Event-ID erforderlich', 'error')
        return redirect(url_for('events.index'))
    
    event = Event.query.get_or_404(event_id)
    
    # Check if user is participating or is organizer
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    # Allow organizer to access BillBro even if not participating
    is_organizer = event.organisator_id == current_user.id
    
    if not participation and not is_organizer:
        flash('Sie nehmen nicht an diesem Event teil', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # For organizer view, get all active members for attendance check
    all_members = []
    if is_organizer:
        from backend.models.member import Member
        all_members = Member.query.filter_by(is_active=True).order_by(Member.nachname, Member.vorname).all()
    
    form = BillBroForm()
    
    return render_template('billbro/index.html', 
                         event=event, 
                         participation=participation,
                         all_members=all_members,
                         is_organizer=is_organizer,
                         form=form,
                         Esstyp=Esstyp)

@bp.route('/<int:event_id>/compute', methods=['POST'])
@login_required
def compute(event_id):
    """Compute BillBro results"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is participating
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not participation or not participation.teilnahme:
        return jsonify({'error': 'Keine Teilnahme'}), 400
    
    form = BillBroForm()
    if not form.validate():
        return jsonify({'error': 'Ungültige Eingabe'}), 400
    
    # Parse guess amount
    guess_rappen = MoneyService.to_rappen(form.guess_amount.data)
    if guess_rappen is None:
        return jsonify({'error': 'Ungültiger Betrag'}), 400
    
    # Check for duplicate guesses
    existing_guess = Participation.query.filter_by(
        event_id=event_id,
        guess_bill_amount_rappen=guess_rappen
    ).filter(Participation.member_id != current_user.id).first()
    
    if existing_guess:
        return jsonify({'error': 'Dieser Betrag wurde bereits geschätzt'}), 400
    
    # Validate esstyp selection
    if not form.esstyp.data or form.esstyp.data == '':
        return jsonify({'error': 'Bitte wählen Sie einen Ess-Typ'}), 400
    
    # Update participation
    participation.esstyp = Esstyp(form.esstyp.data)
    participation.guess_bill_amount_rappen = guess_rappen
    participation.responded_at = datetime.utcnow()
    
    # Calculate difference if actual bill is known
    if event.rechnungsbetrag_rappen:
        participation.diff_amount_rappen = abs(
            guess_rappen - event.rechnungsbetrag_rappen
        )
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_COMPUTE, 'participation', participation.id,
        extra_data={
            'event_id': event_id,
            'guess_amount': guess_rappen,
            'esstyp': form.esstyp.data
        }
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Schätzung gespeichert',
            'guess_amount': MoneyService.to_franken(guess_rappen),
            'esstyp': form.esstyp.data
        })
    
    flash('Schätzung gespeichert', 'success')
    return redirect(url_for('billbro.index', event_id=event_id))

# Ergebnisse-Seite entfernt; Rangliste wird direkt in BillBro angezeigt

# Import here to avoid circular imports

@bp.route('/<int:event_id>/enter_bill', methods=['POST'])
@login_required
def enter_bill(event_id):
    """Enter actual bill amount (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann den Rechnungsbetrag eingeben', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    rechnungsbetrag = request.form.get('rechnungsbetrag')
    if not rechnungsbetrag:
        flash('Rechnungsbetrag erforderlich', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Convert to Rappen
    rechnungsbetrag_rappen = MoneyService.to_rappen(rechnungsbetrag)
    if rechnungsbetrag_rappen is None:
        flash('Ungültiger Rechnungsbetrag', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Calculate tip (for display, but don't set gesamtbetrag yet)
    tip_rappen = int(rechnungsbetrag_rappen * 0.07)  # 7% tip
    
    # Update event with bill amount and suggested tip
    event.rechnungsbetrag_rappen = rechnungsbetrag_rappen
    event.trinkgeld_rappen = tip_rappen
    # Don't set gesamtbetrag_rappen yet - let user choose manual override
    
    # Calculate differences for rankings (based on bill amount only)
    participations = Participation.query.filter_by(
        event_id=event_id,
        teilnahme=True
    ).filter(
        Participation.guess_bill_amount_rappen.isnot(None)
    ).all()
    
    for participation in participations:
        participation.diff_amount_rappen = abs(
            participation.guess_bill_amount_rappen - rechnungsbetrag_rappen
        )
    
    # Use GGLService to calculate proper rankings and points
    GGLService.calculate_event_points(event_id)
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_ENTER_BILL, 'event', event.id,
        extra_data={
            'rechnungsbetrag': rechnungsbetrag_rappen,
            'tip': tip_rappen
        }
    )
    
    flash('Rechnungsbetrag eingegeben - bitte Gesamtbetrag bestätigen oder anpassen', 'info')
    return redirect(url_for('billbro.index', event_id=event_id, scroll_to='ergebnisse-section'))

@bp.route('/<int:event_id>/start_session', methods=['POST'])
@login_required
def start_session(event_id):
    """Start BillBro session and notify all participants (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann BillBro starten', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Get all participating members (teilnahme=True)
    participating_members = [p.member_id for p in event.participations if p.teilnahme]
    
    if not participating_members:
        flash('Keine Teilnehmer gefunden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Send push notifications to all participants
    success = NotifierService.send_billbro_start(event_id, participating_members)
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_START_SESSION, 'event', event.id,
        extra_data={
            'event_id': event_id,
            'participants_notified': len(participating_members),
            'notification_success': success
        }
    )
    
    if success:
        flash(f'BillBro gestartet! Push-Nachrichten an {len(participating_members)} Teilnehmer gesendet.', 'success')
    else:
        flash(f'BillBro gestartet, aber Push-Nachrichten konnten nicht gesendet werden.', 'warning')
    
    return redirect(url_for('billbro.index', event_id=event_id))

@bp.route('/<int:event_id>/send_reminder', methods=['POST'])
@login_required
def send_reminder(event_id):
    """Send reminder to participants who haven't guessed yet (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann Erinnerungen senden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Get participants who haven't guessed yet
    pending_participants = []
    for participation in event.participations:
        if (participation.teilnahme and 
            participation.guess_bill_amount_rappen is None):
            pending_participants.append(participation.member_id)
    
    if not pending_participants:
        flash('Alle Teilnehmer haben bereits geschätzt', 'info')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Send reminder notifications
    success = NotifierService.send_billbro_reminder(event_id, pending_participants)
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_SEND_REMINDER, 'event', event.id,
        extra_data={
            'event_id': event_id,
            'pending_participants': len(pending_participants),
            'notification_success': success
        }
    )
    
    if success:
        flash(f'Erinnerung an {len(pending_participants)} Teilnehmer gesendet.', 'success')
    else:
        flash('Erinnerungen konnten nicht gesendet werden.', 'warning')
    
    return redirect(url_for('billbro.index', event_id=event_id))

@bp.route('/<int:event_id>/set_total', methods=['POST'])
@login_required
def set_total(event_id):
    """Set final total amount and calculate shares (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann den Gesamtbetrag festlegen', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    if not event.rechnungsbetrag_rappen:
        flash('Rechnungsbetrag muss zuerst eingegeben werden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    gesamtbetrag_manual = request.form.get('gesamtbetrag_manual')
    if not gesamtbetrag_manual:
        # If no manual amount provided, use automatic calculation
        auto_total = event.rechnungsbetrag_rappen + event.trinkgeld_rappen
        gesamtbetrag_rappen = ((auto_total + 999) // 1000) * 1000  # Round to next 10 CHF
    else:
        # Use manual amount
        gesamtbetrag_rappen = MoneyService.to_rappen(gesamtbetrag_manual)
        if gesamtbetrag_rappen is None:
            flash('Ungültiger Gesamtbetrag', 'error')
            return redirect(url_for('billbro.index', event_id=event_id))
        
        if gesamtbetrag_rappen < event.rechnungsbetrag_rappen:
            flash('Gesamtbetrag kann nicht kleiner als Rechnungsbetrag sein', 'error')
            return redirect(url_for('billbro.index', event_id=event_id))
    
    # Update event with final total
    event.gesamtbetrag_rappen = gesamtbetrag_rappen
    # Recalculate actual tip based on final total
    event.trinkgeld_rappen = gesamtbetrag_rappen - event.rechnungsbetrag_rappen
    
    # Calculate individual shares based on weights
    sparsam_count = 0
    normal_count = 0
    allin_count = 0
    
    for participation in event.participations:
        if participation.teilnahme and participation.esstyp:
            if participation.esstyp == Esstyp.SPARSAM:
                sparsam_count += 1
            elif participation.esstyp == Esstyp.NORMAL:
                normal_count += 1
            elif participation.esstyp == Esstyp.ALLIN:
                allin_count += 1
    
    total_participants = sparsam_count + normal_count + allin_count
    
    if total_participants > 0:
        # Calculate shares based on actual participant counts
        if sparsam_count > 0:
            event.betrag_sparsam_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_sparsam_rappen = None
            
        if normal_count > 0:
            event.betrag_normal_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_normal_rappen = None
            
        if allin_count > 0:
            event.betrag_allin_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_allin_rappen = None
        
        # Update calculated shares for each participation
        for participation in event.participations:
            if participation.teilnahme and participation.esstyp:
                participation.calculated_share_rappen = int(gesamtbetrag_rappen / total_participants)
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_SET_TOTAL, 'event', event.id,
        extra_data={
            'gesamtbetrag': gesamtbetrag_rappen,
            'manual_override': gesamtbetrag_manual is not None,
            'effective_tip': event.trinkgeld_rappen,
            'tip_percentage': round((event.trinkgeld_rappen / event.rechnungsbetrag_rappen) * 100, 1)
        }
    )
    
    is_manual = gesamtbetrag_manual is not None
    flash(f'Gesamtbetrag {"manuell " if is_manual else "automatisch "}festgelegt und Anteile berechnet', 'success')
    return redirect(url_for('billbro.index', event_id=event_id, scroll_to='ergebnisse-section'))

@bp.route('/<int:event_id>/accept_suggested_total', methods=['POST'])
@login_required
def accept_suggested_total(event_id):
    """Accept the automatically suggested total amount (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann den Gesamtbetrag festlegen', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    if not event.rechnungsbetrag_rappen:
        flash('Rechnungsbetrag muss zuerst eingegeben werden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Calculate suggested total (rounded to next 10 CHF)
    auto_total = event.rechnungsbetrag_rappen + event.trinkgeld_rappen
    gesamtbetrag_rappen = ((auto_total + 999) // 1000) * 1000
    
    # Update event with final total
    event.gesamtbetrag_rappen = gesamtbetrag_rappen
    # Recalculate actual tip based on final total
    event.trinkgeld_rappen = gesamtbetrag_rappen - event.rechnungsbetrag_rappen
    
    # Calculate individual shares based on weights
    sparsam_count = 0
    normal_count = 0
    allin_count = 0
    
    for participation in event.participations:
        if participation.teilnahme and participation.esstyp:
            if participation.esstyp == Esstyp.SPARSAM:
                sparsam_count += 1
            elif participation.esstyp == Esstyp.NORMAL:
                normal_count += 1
            elif participation.esstyp == Esstyp.ALLIN:
                allin_count += 1
    
    total_participants = sparsam_count + normal_count + allin_count
    
    if total_participants > 0:
        # Calculate shares based on actual participant counts
        if sparsam_count > 0:
            event.betrag_sparsam_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_sparsam_rappen = None
            
        if normal_count > 0:
            event.betrag_normal_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_normal_rappen = None
            
        if allin_count > 0:
            event.betrag_allin_rappen = int(gesamtbetrag_rappen / total_participants)
        else:
            event.betrag_allin_rappen = None
        
        # Update calculated shares for each participation
        for participation in event.participations:
            if participation.teilnahme and participation.esstyp:
                participation.calculated_share_rappen = int(gesamtbetrag_rappen / total_participants)
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_SET_TOTAL, 'event', event.id,
        extra_data={
            'gesamtbetrag': gesamtbetrag_rappen,
            'manual_override': False,
            'effective_tip': event.trinkgeld_rappen,
            'tip_percentage': round((event.trinkgeld_rappen / event.rechnungsbetrag_rappen) * 100, 1),
            'accepted_suggested': True
        }
    )
    
    flash('Vorgeschlagenen Gesamtbetrag akzeptiert und Anteile berechnet', 'success')
    return redirect(url_for('billbro.index', event_id=event_id, scroll_to='ergebnisse-section'))

@bp.route('/<int:event_id>/share_whatsapp')
@login_required
def share_whatsapp(event_id):
    """Generate WhatsApp share link"""
    event = Event.query.get_or_404(event_id)
    
    if not event.rechnungsbetrag_rappen:
        flash('Rechnungsbetrag muss zuerst eingegeben werden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Create WhatsApp message
    # Handle both Enum and string values (migration compatibility)
    event_type = event.event_typ.value if hasattr(event.event_typ, 'value') else str(event.event_typ)
    message = f"🍽️ BillBro Ergebnisse - {event_type}\n"
    message += f"📅 {event.display_date}\n"
    if event.restaurant:
        message += f"🏪 {event.restaurant}\n"
    message += f"\n💰 Rechnungsbetrag: {event.rechnungsbetrag_rappen / 100:.2f} CHF\n"
    message += f"💡 Trinkgeld (7%): {event.trinkgeld_rappen / 100:.2f} CHF\n"
    message += f"💵 Gesamtbetrag: {event.gesamtbetrag_rappen / 100:.2f} CHF\n\n"
    
    # Add rankings
    participations = Participation.query.filter_by(
        event_id=event_id,
        teilnahme=True
    ).filter(
        Participation.guess_bill_amount_rappen.isnot(None)
    ).order_by(Participation.rank.asc()).all()
    
    if participations:
        message += "🏆 Rangliste:\n"
        for participation in participations[:5]:  # Top 5
            message += f"{participation.rank}. {participation.member.display_name}: "
            message += f"{participation.guess_bill_amount_rappen / 100:.2f} CHF "
            message += f"(±{participation.diff_amount_rappen / 100:.2f} CHF)\n"
    
    # Add individual shares with participant details
    message += f"\n💸 Anteile pro Person:\n"

    # Get all participating members grouped by esstyp
    sparsam_participants = []
    normal_participants = []
    allin_participants = []

    for participation in event.participations:
        if participation.teilnahme and participation.esstyp:
            member_info = ""
            if participation.member.spirit_animal:
                member_info += f"{participation.member.spirit_animal} "
            member_info += f"{participation.member.rufname or participation.member.vorname}"
            
            if participation.esstyp == Esstyp.SPARSAM:
                sparsam_participants.append(member_info)
            elif participation.esstyp == Esstyp.NORMAL:
                normal_participants.append(member_info)
            elif participation.esstyp == Esstyp.ALLIN:
                allin_participants.append(member_info)

    # Add shares with participant lists
    if event.betrag_sparsam_rappen and sparsam_participants:
        message += f"Sparsam: {event.betrag_sparsam_rappen / 100:.2f} CHF\n"
        for participant in sparsam_participants:
            message += f"  • {participant}\n"
    else:
        message += "Sparsam: Nicht berechnet\n"

    if event.betrag_normal_rappen and normal_participants:
        message += f"Normal: {event.betrag_normal_rappen / 100:.2f} CHF\n"
        for participant in normal_participants:
            message += f"  • {participant}\n"
    else:
        message += "Normal: Nicht berechnet\n"

    if event.betrag_allin_rappen and allin_participants:
        message += f"All-In: {event.betrag_allin_rappen / 100:.2f} CHF\n"
        for participant in allin_participants:
            message += f"  • {participant}\n"
    else:
        message += "All-In: Nicht berechnet\n"
    
    # Encode for WhatsApp
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/?text={encoded_message}"
    
    return redirect(whatsapp_url)

@bp.route('/<int:event_id>/update_guess', methods=['POST'])
@login_required
def update_guess(event_id):
    """Update existing guess"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is participating
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not participation or not participation.teilnahme:
        flash('Sie nehmen nicht an diesem Event teil', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Clear existing guess to allow new one
    participation.guess_bill_amount_rappen = None
    participation.esstyp = None
    participation.diff_amount_rappen = None
    participation.rank = None
    participation.responded_at = None
    
    db.session.commit()
    
    flash('Schätzung zurückgesetzt - neue Schätzung möglich', 'success')
    return redirect(url_for('billbro.index', event_id=event_id))

@bp.route('/<int:event_id>/record_guess/<int:member_id>', methods=['POST'])
@login_required
def record_guess(event_id, member_id):
    """Record guess for specific member (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann Schätzungen eingeben', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    participation = Participation.query.filter_by(
        member_id=member_id,
        event_id=event_id
    ).first()
    
    if not participation or not participation.teilnahme:
        flash('Teilnehmer nicht gefunden', 'error')
        return redirect(url_for('billbro.calculator', event_id=event_id))
    
    esstyp = request.form.get('esstyp')
    guess_amount = request.form.get('guess_amount')
    
    if not esstyp or not guess_amount:
        flash('Ess-Typ und Schätzung erforderlich', 'error')
        return redirect(url_for('billbro.calculator', event_id=event_id))
    
    # Convert to Rappen
    guess_rappen = MoneyService.to_rappen(guess_amount)
    if guess_rappen is None:
        flash('Ungültiger Betrag', 'error')
        return redirect(url_for('billbro.calculator', event_id=event_id))
    
    # Update participation
    participation.esstyp = Esstyp(esstyp)
    participation.guess_bill_amount_rappen = guess_rappen
    participation.responded_at = datetime.utcnow()
    
    # Calculate difference if actual bill is known
    if event.rechnungsbetrag_rappen:
        participation.diff_amount_rappen = abs(
            guess_rappen - event.rechnungsbetrag_rappen
        )
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_RECORD_GUESS, 'participation', participation.id,
        extra_data={
            'event_id': event_id,
            'member_id': member_id,
            'guess_amount': guess_rappen,
            'esstyp': esstyp
        }
    )
    
    flash(f'Schätzung für {participation.member.display_name} gespeichert', 'success')
    return redirect(url_for('billbro.calculator', event_id=event_id))

@bp.route('/<int:event_id>/calculator')
@login_required
def calculator(event_id):
    """Mobile calculator view for organizers"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann den Rechner verwenden', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    return render_template('billbro/calculator.html', event=event)

@bp.route('/<int:event_id>/export_pdf')
@login_required
def export_pdf(event_id):
    """Export results as PDF"""
    event = Event.query.get_or_404(event_id)
    
    # Check permissions (organizer or admin)
    if not (event.organisator_id == current_user.id):
        flash('Keine Berechtigung für PDF-Export', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Get all participations with guesses
    participations = Participation.query.filter_by(
        event_id=event_id,
        teilnahme=True
    ).filter(
        Participation.guess_bill_amount_rappen.isnot(None)
    ).order_by(Participation.diff_amount_rappen.asc()).all()
    
    # For now, redirect to results page
    # TODO: Implement actual PDF generation
    flash('PDF-Export noch nicht implementiert', 'info')
    return redirect(url_for('billbro.results', event_id=event_id))

@bp.route('/<int:event_id>/mark_absent/<int:member_id>', methods=['POST'])
@login_required
def mark_absent(event_id, member_id):
    """Mark member as absent (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann Teilnehmer abmelden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    participation = Participation.query.filter_by(
        member_id=member_id,
        event_id=event_id
    ).first()
    
    # Create participation record if it doesn't exist
    if not participation:
        from backend.models.member import Member
        member = Member.query.get_or_404(member_id)
        participation = Participation(
            member_id=member_id,
            event_id=event_id,
            teilnahme=False
        )
        db.session.add(participation)
    
    # Mark as absent
    participation.teilnahme = False
    # Clear BillBro data when marking absent
    participation.esstyp = None
    participation.guess_bill_amount_rappen = None
    participation.diff_amount_rappen = None
    participation.rank = None
    participation.calculated_share_rappen = None
    participation.responded_at = None
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_MARK_ABSENT, 'participation', participation.id,
        extra_data={
            'event_id': event_id,
            'member_id': member_id,
            'member_name': participation.member.display_name
        }
    )
    
    flash(f'{participation.member.display_name} als nicht anwesend markiert', 'success')
    return redirect(url_for('billbro.index', event_id=event_id))

@bp.route('/<int:event_id>/mark_present/<int:member_id>', methods=['POST'])
@login_required
def mark_present(event_id, member_id):
    """Mark member as present again (organizer only)"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann Teilnehmer anmelden', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    participation = Participation.query.filter_by(
        member_id=member_id,
        event_id=event_id
    ).first()
    
    # Create participation record if it doesn't exist
    if not participation:
        from backend.models.member import Member
        member = Member.query.get_or_404(member_id)
        participation = Participation(
            member_id=member_id,
            event_id=event_id,
            teilnahme=True
        )
        db.session.add(participation)
    
    # Mark as present
    participation.teilnahme = True
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_MARK_PRESENT, 'participation', participation.id,
        extra_data={
            'event_id': event_id,
            'member_id': member_id,
            'member_name': participation.member.display_name
        }
    )
    
    flash(f'{participation.member.display_name} wieder angemeldet', 'success')
    return redirect(url_for('billbro.index', event_id=event_id)) 

@bp.route('/<int:event_id>/toggle_status', methods=['POST'])
@login_required
def toggle_billbro_status(event_id):
    """Toggle BillBro status (close/reopen) - organizer only"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (event.organisator_id == current_user.id):
        flash('Nur der Organisator kann BillBro-Status ändern', 'error')
        return redirect(url_for('billbro.index', event_id=event_id))
    
    # Toggle status
    if event.billbro_closed:
        # Reopen BillBro
        event.billbro_closed = False
        flash('BillBro wieder geöffnet - Teilnehmer können Schätzungen ändern', 'success')
    else:
        # Close BillBro
        event.billbro_closed = True
        flash('BillBro abgeschlossen - Schätzungen können nicht mehr geändert werden', 'success')
    
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.BILLBRO_TOGGLE_STATUS, 'event', event.id,
        extra_data={
            'event_id': event_id,
            'new_status': 'closed' if event.billbro_closed else 'open'
        }
    )
    
    return redirect(url_for('billbro.index', event_id=event_id)) 