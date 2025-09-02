import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.participation import Participation, Esstyp
from backend.models.member import Member, Role
from backend.services.places import PlacesService

bp = Blueprint('events', __name__)

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
    submit = SubmitField('Speichern')

class YearPlanningForm(FlaskForm):
    year = IntegerField('Jahr', validators=[DataRequired(), NumberRange(min=2024, max=2030)])
    submit = SubmitField('Jahresplanung erstellen')

def get_second_friday_of_month(year, month):
    """Calculate second Friday of the month"""
    # Find first day of month
    first_day = date(year, month, 1)
    
    # Find first Friday (weekday() returns 0-6, where 4 is Friday)
    days_to_friday = (4 - first_day.weekday()) % 7
    first_friday = first_day + relativedelta(days=days_to_friday)
    
    # Second Friday is one week later
    second_friday = first_friday + relativedelta(days=7)
    
    return second_friday

def create_monthly_events(year):
    """Create monthly dinner events for the year"""
    # Get all active members for organizer assignment
    active_members = Member.query.filter_by(is_active=True).all()
    if not active_members:
        return []
    
    events = []
    organizer_index = 0
    
    for month in range(1, 13):
        event_date = get_second_friday_of_month(year, month)
        
        # Skip if event already exists
        existing = Event.query.filter(
            Event.datum == event_date,
            Event.event_typ == EventType.MONATSESSEN
        ).first()
        
        if not existing:
            # Assign organizer in round-robin fashion
            organizer = active_members[organizer_index % len(active_members)]
            organizer_index += 1
            
            event = Event(
                datum=event_date,
                event_typ=EventType.MONATSESSEN,
                organisator_id=organizer.id,
                season=year,
                published=True
            )
            events.append(event)
    
    return events

@bp.route('/')
@login_required
def index():
    """Events list"""
    # Get all upcoming events (no limit, show all future events)
    today = datetime.utcnow().date()
    current_events = Event.query.filter(
        Event.datum >= datetime.combine(today, datetime.min.time()),
        Event.published == True
    ).order_by(Event.datum.asc()).all()
    
    return render_template('events/index.html', events=current_events)

@bp.route('/year-planning')
@login_required
def year_planning():
    """Year planning interface"""
    if not current_user.is_admin():
        flash('Nur Admins können die Jahresplanung erstellen', 'error')
        return redirect(url_for('events.index'))
    
    form = YearPlanningForm()
    current_year = datetime.utcnow().year
    form.year.data = current_year + 1  # Default to next year
    
    return render_template('events/year_planning.html', form=form)

@bp.route('/year-planning', methods=['POST'])
@login_required
def create_year_planning():
    """Create events for the year"""
    if not current_user.is_admin():
        flash('Nur Admins können die Jahresplanung erstellen', 'error')
        return redirect(url_for('events.index'))
    
    form = YearPlanningForm()
    if form.validate_on_submit():
        year = form.year.data
        
        # Create monthly events
        monthly_events = create_monthly_events(year)
        
        if monthly_events:
            for event in monthly_events:
                db.session.add(event)
            
            db.session.commit()
            
            flash(f'Jahresplanung {year} erfolgreich erstellt: {len(monthly_events)} Monatsessen geplant', 'success')
        else:
            flash(f'Keine neuen Events erstellt - Jahresplanung {year} bereits vorhanden', 'info')
        
        return redirect(url_for('events.index'))
    
    return render_template('events/year_planning.html', form=form)

@bp.route('/archive')
@login_required
def archive():
    """Events archive - only past events"""
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', type=int)
    
    # Only show past events in archive
    today = datetime.utcnow().date()
    query = Event.query.filter(
        Event.published == True,
        Event.datum < datetime.combine(today, datetime.min.time())
    )
    
    if year:
        query = query.filter(Event.season == year)
    
    events = query.order_by(Event.datum.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get available years for filter (only years with past events)
    years = db.session.query(Event.season).filter(
        Event.datum < datetime.combine(today, datetime.min.time())
    ).distinct().order_by(Event.season.desc()).all()
    years = [year[0] for year in years]
    
    return render_template('events/archive.html', events=events, years=years, selected_year=year)

@bp.route('/<int:event_id>')
@login_required
def detail(event_id):
    """Event detail"""
    event = Event.query.get_or_404(event_id)
    
    # Get user's participation
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    # Get all participations for this event
    participations = Participation.query.filter_by(event_id=event_id).all()
    
    return render_template('events/detail.html', 
                         event=event, 
                         participation=participation,
                         participations=participations)

@bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(event_id):
    """Edit event"""
    event = Event.query.get_or_404(event_id)
    
    # Check permissions
    if not (current_user.is_admin() or event.organisator_id == current_user.id):
        flash('Keine Berechtigung zum Bearbeiten dieses Events', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    form = EventForm(obj=event)
    
    # Load organizer choices
    active_members = Member.query.filter_by(is_active=True).order_by(Member.nachname, Member.vorname).all()
    form.organisator_id.choices = [(m.id, m.display_name) for m in active_members]
    
    if form.validate_on_submit():
        old_organizer_id = event.organisator_id
        new_organizer_id = form.organisator_id.data
        
        event.datum = form.datum.data
        event.event_typ = EventType(form.event_typ.data)
        event.organisator_id = new_organizer_id
        event.season = event.datum.year
        
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
        if form.place_id.data:
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
        
        # Handle organizer change and participation updates
        if old_organizer_id != new_organizer_id:
            # Remove old organizer from participants (they are usually unavailable)
            old_organizer_participation = Participation.query.filter_by(
                member_id=old_organizer_id,
                event_id=event.id
            ).first()
            
            if old_organizer_participation:
                db.session.delete(old_organizer_participation)
            
            # Add new organizer as participant (if not already participating)
            new_organizer_participation = Participation.query.filter_by(
                member_id=new_organizer_id,
                event_id=event.id
            ).first()
            
            if not new_organizer_participation:
                new_organizer_participation = Participation(
                    member_id=new_organizer_id,
                    event_id=event.id,
                    teilnahme=True,
                    responded_at=datetime.utcnow()
                )
                db.session.add(new_organizer_participation)
        
        db.session.commit()
        
        # Log organizer change if it happened
        if old_organizer_id != new_organizer_id:
            from backend.services.security import SecurityService, AuditAction
            old_organizer = Member.query.get(old_organizer_id)
            new_organizer = Member.query.get(new_organizer_id)
            SecurityService.log_audit_event(
                AuditAction.EVENT_ORGANIZER_CHANGED, 'event', event.id,
                extra_data={
                    'old_organizer_id': old_organizer_id,
                    'new_organizer_id': new_organizer_id,
                    'old_organizer_name': old_organizer.display_name if old_organizer else 'Unbekannt',
                    'new_organizer_name': new_organizer.display_name if new_organizer else 'Unbekannt'
                }
            )
            flash(f'Event erfolgreich bearbeitet. Organisator geändert: {old_organizer.display_name if old_organizer else "Unbekannt"} → {new_organizer.display_name if new_organizer else "Unbekannt"}. Alter Organisator als Teilnehmer entfernt, neuer Organisator automatisch als Teilnehmer hinzugefügt.', 'success')
        else:
            flash('Event erfolgreich bearbeitet', 'success')
        
        return redirect(url_for('events.detail', event_id=event_id))
    
    return render_template('events/edit.html', form=form, event=event)

@bp.route('/<int:event_id>/delete', methods=['POST'])
@login_required
def delete(event_id):
    """Delete event"""
    event = Event.query.get_or_404(event_id)
    
    # Check permissions - only admins can delete events
    if not current_user.is_admin():
        flash('Nur Administratoren können Events löschen', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Check if event is in the past
    if event.datum.date() < datetime.utcnow().date():
        flash('Vergangene Events können nicht gelöscht werden', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Delete all participations for this event
    participations = Participation.query.filter_by(event_id=event_id).all()
    for participation in participations:
        db.session.delete(participation)
    
    # Log audit event before deletion
    from backend.services.security import SecurityService, AuditAction
    SecurityService.log_audit_event(
        AuditAction.EVENT_DELETE, 'event', event_id,
        extra_data={
            'event_title': event.restaurant or f"{event.event_typ.value} am {event.display_date}",
            'event_date': event.datum.isoformat(),
            'deleted_by': current_user.display_name
        }
    )
    
    # Delete the event
    db.session.delete(event)
    db.session.commit()
    
    flash('Event erfolgreich gelöscht', 'success')
    return redirect(url_for('events.index'))

@bp.route('/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp(event_id):
    """RSVP for event - simple toggle"""
    event = Event.query.get_or_404(event_id)
    
    # Get or create participation
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    if not participation:
        participation = Participation(
            member_id=current_user.id,
            event_id=event_id,
            teilnahme=False
        )
        db.session.add(participation)
    
    # Simple toggle
    participation.teilnahme = not participation.teilnahme
    participation.responded_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log audit event
    from backend.services.security import SecurityService, AuditAction
    SecurityService.log_audit_event(
        AuditAction.RSVP_UPDATE, 'participation', participation.id,
        extra_data={
            'event_id': event_id,
            'action': 'toggle'
        }
    )
    
    message = 'Teilnahme bestätigt' if participation.teilnahme else 'Teilnahme abgesagt'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'teilnahme': participation.teilnahme,
            'message': message
        })
    
    flash(message, 'success')
    return redirect(url_for('events.detail', event_id=event_id))

@bp.route('/places/autocomplete')
@login_required
def places_autocomplete():
    """Google Places autocomplete API endpoint"""
    query = request.args.get('query', '').strip()
    session_token = request.args.get('session_token')
    
    current_app.logger.info(f"Places autocomplete endpoint called with query: '{query}'")
    current_app.logger.info(f"Session token: {session_token}")
    
    if not query:
        current_app.logger.info("Empty query, returning empty results")
        return jsonify([])
    
    predictions = PlacesService.autocomplete(query, session_token)
    current_app.logger.info(f"Returning {len(predictions)} predictions")
    return jsonify(predictions)

@bp.route('/places/details')
@login_required
def places_details():
    """Google Places details API endpoint"""
    place_id = request.args.get('place_id')
    session_token = request.args.get('session_token')
    
    if not place_id:
        return jsonify({'error': 'Place ID is required'}), 400
    
    details = PlacesService.get_place_details(place_id, session_token)
    if not details:
        return jsonify({'error': 'Place not found'}), 404
    
    return jsonify(details)

@bp.route('/places/config')
@login_required
def places_config():
    """Return Google Maps API configuration for frontend"""
    api_key = current_app.config.get('GOOGLE_MAPS_API_KEY_FRONTEND')
    enabled = bool(api_key)
    
    current_app.logger.info(f"Places config endpoint called")
    current_app.logger.info(f"Frontend API key present: {bool(api_key)}")
    current_app.logger.info(f"Places enabled: {enabled}")
    
    return jsonify({
        'api_key': api_key,
        'enabled': enabled
    })

@bp.route('/stats')
@login_required
def stats():
    """General event statistics page"""
    # Get all past events (published and in the past)
    past_events = Event.query.filter(
        Event.published == True,
        Event.datum < datetime.utcnow().date()
    ).order_by(Event.datum.desc()).all()
    
    # Get all future events
    future_events = Event.query.filter(
        Event.published == True,
        Event.datum >= datetime.utcnow().date()
    ).order_by(Event.datum.asc()).all()
    
    # Calculate general stats
    total_events = len(past_events) + len(future_events)
    total_past_events = len(past_events)
    total_future_events = len(future_events)
    
    # Event type distribution
    event_types = {}
    for event in past_events + future_events:
        event_type = event.event_typ.value
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Restaurant stats
    restaurants = {}
    for event in past_events:
        if event.restaurant:
            restaurants[event.restaurant] = restaurants.get(event.restaurant, 0) + 1
    
    # BillBro stats (only for past events)
    billbro_events = [e for e in past_events if e.rechnungsbetrag_rappen]
    total_billbro_events = len(billbro_events)
    
    avg_bill_amount = 0
    avg_tip_amount = 0
    total_bill_amount = 0
    total_tip_amount = 0
    
    if billbro_events:
        for event in billbro_events:
            total_bill_amount += event.rechnungsbetrag_rappen
            if event.trinkgeld_rappen:
                total_tip_amount += event.trinkgeld_rappen
        
        avg_bill_amount = total_bill_amount / len(billbro_events) / 100
        avg_tip_amount = total_tip_amount / len(billbro_events) / 100
    
    # Participation stats
    total_participations = 0
    confirmed_participations = 0
    
    for event in past_events + future_events:
        participations = Participation.query.filter_by(event_id=event.id).all()
        total_participations += len(participations)
        confirmed_participations += len([p for p in participations if p.teilnahme])
    
    avg_participation_rate = 0
    if total_participations > 0:
        avg_participation_rate = (confirmed_participations / total_participations) * 100
    
    return render_template('events/stats.html', 
                         past_events=past_events,
                         future_events=future_events,
                         total_events=total_events,
                         total_past_events=total_past_events,
                         total_future_events=total_future_events,
                         event_types=event_types,
                         restaurants=restaurants,
                         total_billbro_events=total_billbro_events,
                         avg_bill_amount=avg_bill_amount,
                         avg_tip_amount=avg_tip_amount,
                         total_participations=total_participations,
                         confirmed_participations=confirmed_participations,
                         avg_participation_rate=avg_participation_rate)

# Import here to avoid circular imports
from datetime import datetime 