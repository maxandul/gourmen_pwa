import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf

from wtforms import StringField, SelectField, BooleanField, DateField, SubmitField, PasswordField, FieldList
from wtforms.validators import DataRequired, Email, Length
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.event import Event, EventType
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.audit_event import AuditEvent
from backend.services.security import SecurityService, AuditAction, require_step_up

bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    from flask import abort
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard overview"""
    return render_template('admin/index.html')

class MemberForm(FlaskForm):
    # Basic info
    vorname = StringField('Vorname', validators=[DataRequired()])
    nachname = StringField('Nachname', validators=[DataRequired()])
    rufname = StringField('Rufname')
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    telefon = StringField('Telefon')
    
    # Personal data
    geburtsdatum = DateField('Geburtsdatum')
    nationalitaet = StringField('Nationalität')
    
    # Address
    strasse = StringField('Strasse')
    hausnummer = StringField('Hausnummer')
    plz = StringField('PLZ')
    ort = StringField('Ort')
    
    # Association data
    funktion = SelectField('Funktion', choices=[
        (Funktion.MEMBER.value, 'Member'),
        (Funktion.VEREINSPRAESIDENT.value, 'Vereinspräsident'),
        (Funktion.KOMMISSIONSPRAESIDENT.value, 'Kommissionspräsident'),
        (Funktion.SCHATZMEISTER.value, 'Schatzmeister'),
        (Funktion.MARKETINGCHEF.value, 'Marketingchef'),
        (Funktion.REISEKOMMISSAR.value, 'Reisekommissar'),
        (Funktion.RECHNUNGSPRUEFER.value, 'Rechnungsprüfer')
    ])
    beitrittsjahr = StringField('Beitrittsjahr')
    vorstandsmitglied = BooleanField('Vorstandsmitglied')
    
    # Physical data
    koerpergroesse = StringField('Körpergrösse (cm)')
    koerpergewicht = StringField('Körpergewicht (kg)')
    schuhgroesse = StringField('Schuhgrösse')
    
    # Clothing
    kleider_oberteil = StringField('Kleider Oberteil')
    kleider_hosen = StringField('Kleider Hosen')
    kleider_cap = StringField('Kleider Cap')
    
    # Preferences
    zimmerwunsch = StringField('Zimmerwunsch')
    spirit_animal = StringField('Spirit Animal')
    fuehrerschein = StringField('Führerschein-Kategorien (z.B. A, B, C)')
    
    # System
    role = SelectField('Rolle', choices=[
        (Role.MEMBER.value, 'Mitglied'),
        (Role.ADMIN.value, 'Admin')
    ], validators=[DataRequired()])
    is_active = BooleanField('Aktiv')
    submit = SubmitField('Speichern')

class MemberCreateForm(MemberForm):
    password = PasswordField('Passwort', validators=[DataRequired(), Length(min=12)])

class EventForm(FlaskForm):
    datum = DateField('Datum', validators=[DataRequired()])
    event_typ = SelectField('Event-Typ', choices=[
        (EventType.MONATSESSEN.value, 'Monatsessen'),
        (EventType.AUSFLUG.value, 'Ausflug'),
        (EventType.GENERALVERSAMMLUNG.value, 'Generalversammlung')
    ], validators=[DataRequired()])
    organisator_id = SelectField('Organisator', coerce=int, validators=[DataRequired()])
    
    # Restaurant fields
    restaurant = StringField('Restaurant/Location')
    kueche = StringField('Küche/Beschreibung')
    website = StringField('Website')
    
    # Google Places fields (hidden, populated by JavaScript)
    place_id = StringField('Place ID')
    place_name = StringField('Place Name')
    place_address = StringField('Place Address')
    place_lat = StringField('Place Latitude')
    place_lng = StringField('Place Longitude')
    place_types = StringField('Place Types')
    place_website = StringField('Place Website')
    place_maps_url = StringField('Place Maps URL')
    place_price_level = StringField('Place Price Level')
    place_street_number = StringField('Place Street Number')
    place_route = StringField('Place Route')
    place_postal_code = StringField('Place Postal Code')
    place_locality = StringField('Place Locality')
    place_country = StringField('Place Country')
    
    notizen = StringField('Notizen/Reservationsdetails')
    submit = SubmitField('Erstellen')

@bp.route('/members')
@login_required
@admin_required
def members():
    """Admin members list"""
    members = Member.query.order_by(Member.nachname, Member.vorname).all()
    return render_template('admin/members.html', members=members)



@bp.route('/members/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_member():
    """Create new member"""
    form = MemberCreateForm()
    
    if form.validate_on_submit():
        member = Member(
            # Basic info
            vorname=form.vorname.data,
            nachname=form.nachname.data,
            rufname=form.rufname.data or None,
            email=form.email.data,
            telefon=form.telefon.data or None,
            
            # Personal data
            geburtsdatum=form.geburtsdatum.data if form.geburtsdatum.data else None,
            nationalitaet=form.nationalitaet.data or None,
            
            # Address
            strasse=form.strasse.data or None,
            hausnummer=form.hausnummer.data or None,
            plz=form.plz.data or None,
            ort=form.ort.data or None,
            
            # Association data
            funktion=form.funktion.data if form.funktion.data else None,
            beitrittsjahr=int(form.beitrittsjahr.data) if form.beitrittsjahr.data and form.beitrittsjahr.data.strip() and form.beitrittsjahr.data.strip() != '' else None,
            vorstandsmitglied=form.vorstandsmitglied.data,
            
            # Physical data
            koerpergroesse=int(form.koerpergroesse.data) if form.koerpergroesse.data and form.koerpergroesse.data.strip() and form.koerpergroesse.data.strip() != '' else None,
            koerpergewicht=int(form.koerpergewicht.data) if form.koerpergewicht.data and form.koerpergewicht.data.strip() and form.koerpergewicht.data.strip() != '' else None,
            schuhgroesse=float(form.schuhgroesse.data) if form.schuhgroesse.data and form.schuhgroesse.data.strip() and form.schuhgroesse.data.strip() != '' else None,
            
            # Clothing
            kleider_oberteil=form.kleider_oberteil.data or None,
            kleider_hosen=form.kleider_hosen.data or None,
            kleider_cap=form.kleider_cap.data or None,
            
            # Preferences
            zimmerwunsch=form.zimmerwunsch.data or None,
            spirit_animal=form.spirit_animal.data or None,
            fuehrerschein=form.fuehrerschein.data or None,
            
            # System
            role=Role(form.role.data),
            is_active=form.is_active.data
        )
        member.set_password(form.password.data)
        
        db.session.add(member)
        db.session.commit()

        # Save sensitive data from request (encrypted)
        try:
            sensitive_payload = {
                'pass_nummer': request.form.get('pass_nummer') or None,
                'pass_ausgestellt': request.form.get('pass_ausgestellt') or None,
                'pass_ablauf': request.form.get('pass_ablauf') or None,
                'id_nummer': request.form.get('id_nummer') or None,
                'id_ausgestellt': request.form.get('id_ausgestellt') or None,
                'id_ablauf': request.form.get('id_ablauf') or None,
                'allergien': request.form.get('allergien') or None,
            }
            if any(sensitive_payload.values()):
                from backend.models.member_sensitive import MemberSensitive
                encrypted = SecurityService.encrypt_json(sensitive_payload)
                sensitive = MemberSensitive(member_id=member.id, payload_encrypted=encrypted)
                db.session.add(sensitive)
                db.session.commit()
        except Exception as e:
            # don't fail creation; log and continue
            from flask import current_app
            current_app.logger.error(f"Failed to save sensitive data for member {member.id}: {e}")
        
        SecurityService.log_audit_event(
            AuditAction.ADMIN_CREATE_MEMBER, 'member', member.id
        )
        
        flash('Mitglied erfolgreich erstellt', 'success')
        return redirect(url_for('admin.members'))
    
    return render_template('admin/create_member.html', form=form)

@bp.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_member(member_id):
    """Edit member"""
    member = Member.query.get_or_404(member_id)
    form = MemberForm()
    
    # Populate form with existing data
    if request.method == 'GET':
        form.vorname.data = member.vorname
        form.nachname.data = member.nachname
        form.rufname.data = member.rufname
        form.email.data = member.email
        form.telefon.data = member.telefon
        form.geburtsdatum.data = member.geburtsdatum
        form.nationalitaet.data = member.nationalitaet
        form.strasse.data = member.strasse
        form.hausnummer.data = member.hausnummer
        form.plz.data = member.plz
        form.ort.data = member.ort
        form.funktion.data = member.funktion if member.funktion else Funktion.MEMBER.value
        form.beitrittsjahr.data = str(member.beitrittsjahr) if member.beitrittsjahr else ''
        form.vorstandsmitglied.data = member.vorstandsmitglied
        form.koerpergroesse.data = str(member.koerpergroesse) if member.koerpergroesse else ''
        form.koerpergewicht.data = str(member.koerpergewicht) if member.koerpergewicht else ''
        form.schuhgroesse.data = str(member.schuhgroesse) if member.schuhgroesse else ''
        form.kleider_oberteil.data = member.kleider_oberteil
        form.kleider_hosen.data = member.kleider_hosen
        form.kleider_cap.data = member.kleider_cap
        form.zimmerwunsch.data = member.zimmerwunsch
        form.spirit_animal.data = member.spirit_animal
        form.fuehrerschein.data = member.fuehrerschein
        # Handle both Enum and string values (migration compatibility)
        if hasattr(member.role, 'value'):
            form.role.data = member.role.value
        else:
            form.role.data = str(member.role)
        form.is_active.data = member.is_active
    
    if form.validate_on_submit():
        # Update all fields
        member.vorname = form.vorname.data
        member.nachname = form.nachname.data
        member.rufname = form.rufname.data or None
        member.email = form.email.data
        member.telefon = form.telefon.data or None
        
        # Personal data
        member.geburtsdatum = form.geburtsdatum.data if form.geburtsdatum.data else None
        member.nationalitaet = form.nationalitaet.data or None
        
        # Address
        member.strasse = form.strasse.data or None
        member.hausnummer = form.hausnummer.data or None
        member.plz = form.plz.data or None
        member.ort = form.ort.data or None
        
        # Association data
        member.funktion = form.funktion.data if form.funktion.data else None
        member.beitrittsjahr = int(form.beitrittsjahr.data) if form.beitrittsjahr.data and form.beitrittsjahr.data.strip() and form.beitrittsjahr.data.strip() != '' else None
        member.vorstandsmitglied = form.vorstandsmitglied.data
        
        # Physical data
        member.koerpergroesse = int(form.koerpergroesse.data) if form.koerpergroesse.data and form.koerpergroesse.data.strip() and form.koerpergroesse.data.strip() != '' else None
        member.koerpergewicht = int(form.koerpergewicht.data) if form.koerpergewicht.data and form.koerpergewicht.data.strip() and form.koerpergewicht.data.strip() != '' else None
        member.schuhgroesse = float(form.schuhgroesse.data) if form.schuhgroesse.data and form.schuhgroesse.data.strip() and form.schuhgroesse.data.strip() != '' else None
        
        # Clothing
        member.kleider_oberteil = form.kleider_oberteil.data or None
        member.kleider_hosen = form.kleider_hosen.data or None
        member.kleider_cap = form.kleider_cap.data or None
        
        # Preferences
        member.zimmerwunsch = form.zimmerwunsch.data or None
        member.spirit_animal = form.spirit_animal.data or None
        member.fuehrerschein = form.fuehrerschein.data or None
        
        # System
        member.role = Role(form.role.data)
        member.is_active = form.is_active.data
        
        db.session.commit()
        
        SecurityService.log_audit_event(
            AuditAction.ADMIN_EDIT_MEMBER, 'member', member.id
        )
        
        flash('Mitglied erfolgreich bearbeitet', 'success')
        return redirect(url_for('admin.members'))
    
    return render_template('admin/edit_member_enhanced.html', form=form, member=member)

@bp.route('/members/<int:member_id>/sensitive', methods=['GET', 'POST'])
@login_required
@admin_required
@require_step_up
def member_sensitive(member_id):
    """View/edit member sensitive data"""
    member = Member.query.get_or_404(member_id)
    
    from backend.models.member_sensitive import MemberSensitive
    sensitive_data = MemberSensitive.query.filter_by(member_id=member_id).first()
    
    if request.method == 'GET':
        if sensitive_data:
            try:
                data = SecurityService.decrypt_json(sensitive_data.payload_encrypted)
            except Exception as e:
                # If decryption fails, clear the corrupted data
                flash('Sensible Daten waren beschädigt und wurden zurückgesetzt.', 'warning')
                db.session.delete(sensitive_data)
                db.session.commit()
                data = {}
        else:
            data = {}
        
        SecurityService.log_audit_event(
            AuditAction.READ_SENSITIVE_OTHERS, 'member_sensitive', member_id
        )
        
        return render_template('admin/member_sensitive.html', member=member, data=data)
    
    elif request.method == 'POST':
        data = {
            'pass_nummer': request.form.get('pass_nummer'),
            'pass_ausgestellt': request.form.get('pass_ausgestellt'),
            'pass_ablauf': request.form.get('pass_ablauf'),
            'id_nummer': request.form.get('id_nummer'),
            'id_ausgestellt': request.form.get('id_ausgestellt'),
            'id_ablauf': request.form.get('id_ablauf'),
            'fuehrerschein': request.form.get('fuehrerschein'),
            'allergien': request.form.get('allergien')
        }
        
        encrypted_data = SecurityService.encrypt_json(data)
        
        if sensitive_data:
            sensitive_data.payload_encrypted = encrypted_data
        else:
            sensitive_data = MemberSensitive(
                member_id=member_id,
                payload_encrypted=encrypted_data
            )
            db.session.add(sensitive_data)
        
        db.session.commit()
        
        SecurityService.log_audit_event(
            AuditAction.UPDATE_SENSITIVE_OTHERS, 'member_sensitive', member_id
        )
        
        flash('Sensible Daten erfolgreich gespeichert', 'success')
        return redirect(url_for('admin.member_sensitive', member_id=member_id))

@bp.route('/events/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_event():
    """Create new event"""
    form = EventForm()
    
    # Populate organisator choices
    form.organisator_id.choices = [(m.id, m.display_name) for m in Member.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        # Set event time to 23:59:59 of the selected date
        from datetime import datetime, time
        event_datetime = datetime.combine(form.datum.data, time(23, 59, 59))
        
        event = Event(
            datum=event_datetime,
            event_typ=EventType(form.event_typ.data),
            organisator_id=form.organisator_id.data,
            season=form.datum.data.year,
            published=True
        )
        
        # Set restaurant details
        if form.restaurant.data:
            event.restaurant = form.restaurant.data
        if form.kueche.data:
            event.kueche = form.kueche.data
        if form.website.data:
            event.website = form.website.data
        if form.notizen.data:
            event.notizen = form.notizen.data
        
        # Set Google Places data if available
        if form.place_id.data or form.place_name.data or form.place_address.data:
            event.place_id = form.place_id.data
            event.place_name = form.place_name.data
            event.place_address = form.place_address.data
            event.place_lat = float(form.place_lat.data) if form.place_lat.data else None
            event.place_lng = float(form.place_lng.data) if form.place_lng.data else None
            event.place_types = json.loads(form.place_types.data) if form.place_types.data else None
            event.place_website = form.place_website.data
            event.place_maps_url = form.place_maps_url.data
            event.place_price_level = int(form.place_price_level.data) if form.place_price_level.data else None
            event.place_street_number = form.place_street_number.data
            event.place_route = form.place_route.data
            event.place_postal_code = form.place_postal_code.data
            event.place_locality = form.place_locality.data
            event.place_country = form.place_country.data
        
        db.session.add(event)
        db.session.flush()  # Get event ID
        
        # Automatically add organizer as participant
        from backend.models.participation import Participation
        from datetime import datetime
        organizer_participation = Participation(
            member_id=event.organisator_id,
            event_id=event.id,
            teilnahme=True,
            responded_at=datetime.utcnow()
        )
        db.session.add(organizer_participation)
        
        db.session.commit()
        
        SecurityService.log_audit_event(
            AuditAction.ADMIN_CREATE_EVENT, 'event', event.id
        )
        
        flash('Event erfolgreich erstellt! Organisator automatisch als Teilnehmer hinzugefügt.', 'success')
        return redirect(url_for('events.detail', event_id=event.id))
    
    return render_template('admin/create_event.html', form=form) 

@bp.route('/members/<int:member_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
@require_step_up
def reset_member_password(member_id):
    """Reset member password"""
    member = Member.query.get_or_404(member_id)
    
    if request.method == 'POST':
        # Check confirmation
        if request.form.get('confirm') != 'RESET':
            flash('Bitte geben Sie "RESET" ein, um zu bestätigen.', 'error')
            return render_template('admin/reset_member_password.html', member=member, csrf_token=generate_csrf())
        
        # Generate new password
        new_password = SecurityService.generate_secure_password()
        
        # Update member password
        member.set_password(new_password)
        db.session.commit()
        
        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.ADMIN_RESET_PASSWORD, 'member', member.id,
            extra_data={'admin_id': current_user.id, 'ip': request.remote_addr}
        )
        
        # Store password in session for display
        session['temp_password'] = {
            'member_name': member.display_name,
            'password': new_password,
            'timestamp': datetime.utcnow().isoformat()
        }
        return redirect(url_for('admin.show_temp_password'))
    
    return render_template('admin/reset_member_password.html', member=member, csrf_token=generate_csrf())

@bp.route('/members/<int:member_id>/reset-2fa', methods=['GET', 'POST'])
@login_required
@admin_required
@require_step_up
def reset_member_2fa(member_id):
    """Reset member 2FA"""
    member = Member.query.get_or_404(member_id)
    
    if request.method == 'POST':
        # Check confirmation
        if request.form.get('confirm') != 'RESET':
            flash('Bitte geben Sie "RESET" ein, um zu bestätigen.', 'error')
            return render_template('admin/reset_member_2fa.html', member=member, csrf_token=generate_csrf())
        
        # Get MFA data
        mfa_data = MemberMFA.query.filter_by(member_id=member.id).first()
        
        if mfa_data and mfa_data.is_totp_enabled:
            # Disable 2FA
            mfa_data.is_totp_enabled = False
            mfa_data.totp_secret_encrypted = None
            mfa_data.activated_at = None
            mfa_data.last_verified_at = None
            
            # Delete backup codes
            MFABackupCode.query.filter_by(member_id=member.id).delete()
            
            db.session.commit()
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.ADMIN_RESET_2FA, 'member', member.id,
                extra_data={'admin_id': current_user.id, 'ip': request.remote_addr}
            )
            
            flash(f'2FA für {member.display_name} wurde zurückgesetzt.', 'success')
        else:
            flash(f'2FA für {member.display_name} war nicht aktiviert.', 'info')
        
        return redirect(url_for('admin.members'))
    
    return render_template('admin/reset_member_2fa.html', member=member, csrf_token=generate_csrf())

@bp.route('/members/<int:member_id>/security-overview')
@login_required
@admin_required
def member_security_overview(member_id):
    """Show member security overview"""
    member = Member.query.get_or_404(member_id)
    
    # Get MFA data
    mfa_data = MemberMFA.query.filter_by(member_id=member.id).first()
    
    # Get backup codes info
    backup_codes = MFABackupCode.query.filter_by(member_id=member.id).all()
    unused_backup_codes = [code for code in backup_codes if not code.is_used and not code.is_revoked]
    
    # Get recent audit events
    recent_events = AuditEvent.query.filter_by(
        actor_id=member.id
    ).order_by(AuditEvent.at.desc()).limit(10).all()
    
    return render_template('admin/member_security_overview.html', 
                         member=member, 
                         mfa_data=mfa_data,
                         unused_backup_codes=unused_backup_codes,
                         recent_events=recent_events)

@bp.route('/temp-password')
@login_required
@admin_required
def show_temp_password():
    """Show temporary password for admin"""
    temp_password_data = session.get('temp_password')
    if not temp_password_data:
        flash('Kein temporäres Passwort verfügbar', 'error')
        return redirect(url_for('admin.members'))
    
    # Check if password is not too old (5 minutes)
    timestamp = datetime.fromisoformat(temp_password_data['timestamp'])
    if datetime.utcnow() - timestamp > timedelta(minutes=5):
        session.pop('temp_password', None)
        flash('Temporäres Passwort ist abgelaufen', 'error')
        return redirect(url_for('admin.members'))
    
    # Clear the temporary password from session after displaying
    session.pop('temp_password', None)
    
    return render_template('admin/temp_password.html', 
                         member_name=temp_password_data['member_name'],
                         password=temp_password_data['password'])

# Admin Merch Routes
@bp.route('/merch')
@login_required
@admin_required
def merch():
    """Admin merch overview"""
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_order import MerchOrder, OrderStatus
    
    # Get statistics
    total_articles = MerchArticle.query.count()
    active_articles = MerchArticle.query.filter_by(is_active=True).count()
    total_orders = MerchOrder.query.count()
    pending_orders = MerchOrder.query.filter_by(status=OrderStatus.BESTELLT).count()
    in_progress_orders = MerchOrder.query.filter_by(status=OrderStatus.WIRD_GELIEFERT).count()
    delivered_orders = MerchOrder.query.filter_by(status=OrderStatus.GELIEFERT).count()
    
    # Get recent orders
    recent_orders = MerchOrder.query.order_by(MerchOrder.created_at.desc()).limit(5).all()
    
    return render_template('admin/merch/index.html', 
                         total_articles=total_articles,
                         active_articles=active_articles,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         in_progress_orders=in_progress_orders,
                         delivered_orders=delivered_orders,
                         recent_orders=recent_orders)

@bp.route('/merch/orders')
@login_required
@admin_required
def merch_orders():
    """Admin merch orders management"""
    from backend.models.merch_order import MerchOrder, OrderStatus
    
    # Get filter parameters
    status_filter = request.args.get('status')
    search = request.args.get('search', '')
    
    # Build query
    query = MerchOrder.query
    
    if status_filter:
        query = query.filter_by(status=OrderStatus(status_filter))
    
    if search:
        query = query.join(Member).filter(
            (Member.vorname.contains(search)) |
            (Member.nachname.contains(search)) |
            (Member.email.contains(search)) |
            (MerchOrder.order_number.contains(search))
        )
    
    orders = query.order_by(MerchOrder.created_at.desc()).all()
    
    return render_template('admin/merch/orders.html', 
                         orders=orders, 
                         status_filter=status_filter,
                         search=search)

@bp.route('/merch/orders/<int:order_id>')
@login_required
@admin_required
def merch_order_detail(order_id):
    """Admin order detail"""
    from backend.models.merch_order import MerchOrder
    
    order = MerchOrder.query.get_or_404(order_id)
    
    return render_template('admin/merch/order_detail.html', order=order)

@bp.route('/merch/orders/<int:order_id>/status', methods=['GET', 'POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status"""
    from backend.models.merch_order import MerchOrder, OrderStatus
    
    print(f"DEBUG: Route reached - Order ID: {order_id}, Method: {request.method}")
    
    if request.method == 'POST':
        try:
            order = MerchOrder.query.get_or_404(order_id)
            new_status = request.form.get('status')
            
            print(f"DEBUG: Order ID: {order_id}, New Status: {new_status}")
            print(f"DEBUG: Request method: {request.method}")
            print(f"DEBUG: Request form: {dict(request.form)}")
            
            if new_status in [status.value for status in OrderStatus]:
                old_status = order.status.value
                order.status = OrderStatus(new_status)
                
                if new_status == OrderStatus.GELIEFERT.value:
                    order.delivered_at = datetime.utcnow()
                
                db.session.commit()
                
                flash(f'Bestellstatus von {old_status} zu {new_status} geändert', 'success')
            else:
                flash('Ungültiger Status', 'error')
                
        except Exception as e:
            print(f"DEBUG: Error in update_order_status: {str(e)}")
            flash(f'Fehler beim Aktualisieren des Status: {str(e)}', 'error')
        
        return redirect(url_for('admin.merch_order_detail', order_id=order_id))
    
    # GET request - just redirect back
    return redirect(url_for('admin.merch_order_detail', order_id=order_id))

@bp.route('/merch/orders/<int:order_id>/status-update', methods=['POST'])
@login_required
@admin_required
def update_order_status_alt(order_id):
    """Alternative update order status route"""
    from backend.models.merch_order import MerchOrder, OrderStatus
    
    try:
        order = MerchOrder.query.get_or_404(order_id)
        new_status = request.form.get('status')
        
        print(f"DEBUG ALT: Order ID: {order_id}, New Status: {new_status}")
        
        if new_status in [status.value for status in OrderStatus]:
            old_status = order.status.value
            order.status = OrderStatus(new_status)
            
            if new_status == OrderStatus.GELIEFERT.value:
                order.delivered_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Bestellstatus von {old_status} zu {new_status} geändert', 'success')
        else:
            flash('Ungültiger Status', 'error')
            
    except Exception as e:
        print(f"DEBUG ALT: Error in update_order_status: {str(e)}")
        flash(f'Fehler beim Aktualisieren des Status: {str(e)}', 'error')
    
    return redirect(url_for('admin.merch_order_detail', order_id=order_id))

@bp.route('/merch/articles')
@login_required
@admin_required
def merch_articles():
    """Admin merch articles management"""
    from backend.models.merch_article import MerchArticle
    
    articles = MerchArticle.query.order_by(MerchArticle.created_at.desc()).all()
    
    return render_template('admin/merch/articles.html', articles=articles)

@bp.route('/merch/articles/<int:article_id>')
@login_required
@admin_required
def merch_article_detail(article_id):
    """Admin article detail"""
    from backend.models.merch_article import MerchArticle
    from backend.models.merch_variant import MerchVariant
    
    article = MerchArticle.query.get_or_404(article_id)
    variants = MerchVariant.query.filter_by(article_id=article_id).all()
    
    return render_template('admin/merch/article_detail.html', article=article, variants=variants) 
