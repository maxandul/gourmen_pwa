import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.participation import Participation, Esstyp
from backend.routes.billbro import BillBroForm
from backend.models.member import Member, Role
from backend.services.places import PlacesService
from backend.services.notifier import NotifierService
from backend.services.push_notifications import PushNotificationService
from backend.services.retro_cleanup import RetroCleanupService
from backend.services.monatsessen_stats import get_monatsessen_statistics
from backend.forms.rating import EventRatingForm

bp = Blueprint('events', __name__)

CLEANUP_RSVP_UNDO_SESSION_KEY = 'cleanup_rsvp_undo'


def _cleanup_rsvp_undo_available() -> bool:
    payload = session.get(CLEANUP_RSVP_UNDO_SESSION_KEY)
    return bool(
        payload
        and payload.get('member_id') == current_user.id
    )


# Push Notification API Routes
@bp.route('/api/events/<int:event_id>/participation-stats', methods=['GET'])
@login_required
def get_participation_stats(event_id):
    """Get participation statistics for an event"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Nur Organisator oder Admin kann Statistiken sehen
        if current_user.id != event.organisator_id and not current_user.is_admin():
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        stats = PushNotificationService.get_event_participation_stats(event_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/events/<int:event_id>/send-reminders', methods=['POST'])
@login_required
def send_participation_reminders(event_id):
    """Send participation reminders to members who haven't responded"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Nur Organisator oder Admin kann Erinnerungen senden
        if current_user.id != event.organisator_id and not current_user.is_admin():
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        result = PushNotificationService.send_participation_reminder_to_members(event_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/events/<int:event_id>/send-organizer-reminder', methods=['POST'])
@login_required
def send_organizer_reminder(event_id):
    """Send reminder to event organizer"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Nur Admin kann Organisator-Erinnerungen senden
        if not current_user.is_admin():
            return jsonify({'error': 'Keine Berechtigung'}), 403
        
        success = PushNotificationService.send_event_reminder_to_organizer(event_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Erinnerung an Organisator gesendet'}), 200
        else:
            return jsonify({'success': False, 'message': 'Erinnerung konnte nicht gesendet werden'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    """Events main page with tabs"""
    tab = request.args.get('tab', 'kommend')
    if tab == 'overview':
        # Alter Tab entfernt — gleiche Infos wie Dashboard; Bookmarks weiterleiten
        params = request.args.to_dict(flat=True)
        params['tab'] = 'kommend'
        return redirect(url_for('events.index', **params))

    now = datetime.utcnow()

    context = {
        'active_tab': tab,
    }

    # Globale Filter (Jahr / Organisator) — alle Tabs, URL-Parameter identisch wie bisher
    filter_year = request.args.get('year', type=int)
    filter_organizer_id = request.args.get('organisator_id', type=int)

    years_query = (
        db.session.query(Event.season)
        .filter(Event.published == True)
        .distinct()
        .order_by(Event.season.desc())
        .all()
    )
    filter_years = [row[0] for row in years_query] if years_query else []
    filter_organizers = (
        Member.query.filter_by(is_active=True)
        .order_by(Member.nachname, Member.vorname)
        .all()
    )
    events_filter_args = {}
    if filter_year:
        events_filter_args['year'] = filter_year
    if filter_organizer_id:
        events_filter_args['organisator_id'] = filter_organizer_id
    events_filters_active = bool(filter_year or filter_organizer_id)
    selected_organizer_label = None
    if filter_organizer_id:
        org_member = db.session.get(Member, filter_organizer_id)
        if org_member:
            selected_organizer_label = org_member.display_name_with_spirit

    context.update(
        {
            'years': filter_years,
            'organizers': filter_organizers,
            'selected_year': filter_year,
            'selected_organizer_id': filter_organizer_id,
            'events_filter_args': events_filter_args,
            'events_filters_active': events_filters_active,
            'selected_organizer_label': selected_organizer_label,
            'events_tab_urls': {
                'kommend': url_for(
                    'events.index', tab='kommend', **events_filter_args, _anchor='gourmen-tabs'
                ),
                'archiv': url_for(
                    'events.index', tab='archiv', **events_filter_args, _anchor='gourmen-tabs'
                ),
                'stats': url_for(
                    'events.index', tab='stats', **events_filter_args, _anchor='gourmen-tabs'
                ),
            },
            'events_filter_reset_url': url_for('events.index', tab=tab, _anchor='gourmen-tabs'),
        }
    )

    def _apply_event_filters(query):
        if filter_year:
            query = query.filter(Event.season == filter_year)
        if filter_organizer_id:
            query = query.filter(Event.organisator_id == filter_organizer_id)
        return query

    # Tab-specific data
    if tab == 'kommend':
        upcoming_query = Event.query.filter(
            Event.published == True,
            Event.datum > now,
        )
        upcoming_query = _apply_event_filters(upcoming_query)
        context['events'] = upcoming_query.order_by(Event.datum.asc()).all()

    elif tab == 'archiv':
        # Past events with pagination
        page = request.args.get('page', 1, type=int)

        query = Event.query.filter(
            Event.published == True,
            Event.datum < now,
        )
        query = _apply_event_filters(query)

        events = query.order_by(Event.datum.desc()).paginate(
            page=page, per_page=10, error_out=False
        )

        context['events'] = events

    elif tab == 'stats':
        monatsessen_stats = get_monatsessen_statistics(
            now=now,
            season_year=filter_year,
            organizer_id=filter_organizer_id,
            current_member_id=current_user.id,
        )
        context['monatsessen_stats'] = monatsessen_stats
    
    return render_template('events/index.html', **context)

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
    """Redirect to archive tab"""
    return redirect(url_for('events.index', tab='archiv', **request.args))

@bp.route('/cleanup')
@login_required
def cleanup():
    """Nur vergangene Events: fehlende Zu-/Absage und/oder Bewertung; Reihenfolge jüngstes zuerst; Navigation per ?i=."""
    progress = RetroCleanupService.get_progress(current_user.id)
    open_events = RetroCleanupService.list_open_cleanup_events(current_user.id)
    focus = request.args.get('focus')

    if not open_events:
        return render_template(
            'events/cleanup.html',
            no_events=True,
            progress=progress,
            cleanup_rsvp_undo_available=_cleanup_rsvp_undo_available()
        )

    raw_i = request.args.get('i', default=0, type=int)
    if raw_i is None:
        raw_i = 0
    idx = max(0, min(raw_i, len(open_events) - 1))
    event = open_events[idx]
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event.id,
    ).first()
    has_rating = RetroCleanupService._has_rating(event.id, current_user.id)

    can_rate = (
        event.allow_ratings
        and ((participation and participation.teilnahme) or event.organisator_id == current_user.id)
        and not has_rating
    )
    rating_form = EventRatingForm()

    return render_template(
        'events/cleanup.html',
        event=event,
        participation=participation,
        has_rating=has_rating,
        can_rate=can_rate,
        form=rating_form,
        progress=progress,
        focus=focus,
        cleanup_idx=idx,
        cleanup_open_count=len(open_events),
        cleanup_rsvp_undo_available=_cleanup_rsvp_undo_available()
    )


@bp.route('/cleanup/undo-rsvp', methods=['POST'])
@login_required
def cleanup_undo_rsvp():
    """Stellt die Teilnahme-Zeile vor der letzten Zu-/Absage in der Bereinigung wieder her."""
    payload = session.pop(CLEANUP_RSVP_UNDO_SESSION_KEY, None)
    if not payload or payload.get('member_id') != current_user.id:
        flash('Nichts zum Rückgängigmachen.', 'info')
        return redirect(url_for('events.cleanup'))

    event_id = payload['event_id']
    prev = payload['prev']
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id,
    ).first()

    if not prev['had_row']:
        if participation:
            db.session.delete(participation)
        db.session.commit()
    else:
        if not participation:
            flash('Eintrag nicht gefunden — Rückgängig nicht möglich.', 'error')
            return redirect(url_for('events.cleanup'))
        participation.teilnahme = prev['teilnahme']
        if prev.get('responded_at'):
            participation.responded_at = datetime.fromisoformat(prev['responded_at'])
        else:
            participation.responded_at = None
        db.session.commit()

    flash('Die letzte Zu-/Absage wurde rückgängig gemacht.', 'success')
    open_events = RetroCleanupService.list_open_cleanup_events(current_user.id)
    ids = [e.id for e in open_events]
    i = ids.index(event_id) if event_id in ids else 0
    return redirect(url_for('events.cleanup', i=i))


@bp.route('/<int:event_id>/cleanup/rsvp', methods=['POST'])
@login_required
def cleanup_rsvp(event_id):
    """Setzt Teilnahme explizit im Datenbereinigungs-Flow."""
    status = request.form.get('status')
    if status not in ('yes', 'no'):
        flash('Ungültige Auswahl.', 'error')
        return redirect(url_for('events.cleanup'))

    event = Event.query.get_or_404(event_id)

    if not RetroCleanupService.allows_cleanup_rsvp(event):
        flash('Dieses Event gehört nicht zur Datenbereinigung.', 'error')
        return redirect(url_for('events.cleanup'))

    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()

    if participation:
        prev = {
            'had_row': True,
            'teilnahme': participation.teilnahme,
            'responded_at': participation.responded_at.isoformat() if participation.responded_at else None,
        }
    else:
        prev = {'had_row': False}

    if not participation:
        participation = Participation(
            member_id=current_user.id,
            event_id=event_id,
            teilnahme=(status == 'yes')
        )
        db.session.add(participation)

    participation.teilnahme = (status == 'yes')
    participation.responded_at = datetime.utcnow()

    db.session.commit()

    session[CLEANUP_RSVP_UNDO_SESSION_KEY] = {
        'member_id': current_user.id,
        'event_id': event_id,
        'prev': prev,
    }
    session.modified = True

    focus = (
        'rating'
        if (status == 'yes' and event.allow_ratings)
        else None
    )
    return redirect(url_for('events.cleanup', focus=focus))

@bp.route('/<int:event_id>/ratings/enable', methods=['POST'])
@login_required
def enable_event_ratings(event_id):
    """Erlaubt Bewertungen für ein Event."""
    event = Event.query.get_or_404(event_id)

    if not (current_user.is_admin() or event.organisator_id == current_user.id):
        flash('Keine Berechtigung.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))

    event.allow_ratings = True
    db.session.commit()
    flash('Bewertungen für dieses Event wurden zugelassen.', 'success')
    return redirect(url_for('events.detail', event_id=event_id))

@bp.route('/<int:event_id>/ratings/disable', methods=['POST'])
@login_required
def disable_event_ratings(event_id):
    """Verhindert Bewertungen für ein Event."""
    event = Event.query.get_or_404(event_id)

    if not (current_user.is_admin() or event.organisator_id == current_user.id):
        flash('Keine Berechtigung.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))

    event.allow_ratings = False
    db.session.commit()
    flash('Bewertungen für dieses Event wurden deaktiviert.', 'success')
    return redirect(url_for('events.detail', event_id=event_id))

@bp.route('/<int:event_id>')
@login_required
def detail(event_id):
    """Event detail"""
    event = Event.query.get_or_404(event_id)
    active_tab = request.args.get('tab', 'info')
    if not event.allow_ratings and active_tab == 'ratings':
        active_tab = 'info'
    
    # Get user's participation
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id
    ).first()
    
    # Get all participations for this event
    participations = Participation.query.filter_by(event_id=event_id).all()
    
    # Get all active members for complete overview
    all_members = Member.query.filter_by(is_active=True).order_by(Member.nachname, Member.vorname).all()

    is_organizer = (current_user.is_admin() or event.organisator_id == current_user.id)
    billbro_form = None
    if (participation and participation.teilnahme) or is_organizer:
        billbro_form = BillBroForm()

    ratings = event.get_ratings()
    ratings_sorted = sorted(ratings, key=lambda r: r.created_at or datetime.min, reverse=True)
    user_rating = next((r for r in ratings_sorted if r.participant_id == current_user.id), None)
    average_ratings = event.get_average_ratings()
    # Bewertungen nur wenn erlaubt und für bestätigte Teilnehmende oder den tatsächlichen Organisator
    can_rate = (event.allow_ratings and ((participation and participation.teilnahme) or event.organisator_id == current_user.id))
    rating_edit_mode = request.args.get('edit_rating') == '1' if (user_rating and can_rate) else False

    # Navigation: vorheriges/nächstes Event (stabile Sortierung: datum, id)
    prev_event = (
        Event.query.filter(
            Event.published == True,
            db.or_(
                Event.datum < event.datum,
                db.and_(Event.datum == event.datum, Event.id < event.id),
            ),
        )
        .order_by(Event.datum.desc(), Event.id.desc())
        .first()
    )
    next_event = (
        Event.query.filter(
            Event.published == True,
            db.or_(
                Event.datum > event.datum,
                db.and_(Event.datum == event.datum, Event.id > event.id),
            ),
        )
        .order_by(Event.datum.asc(), Event.id.asc())
        .first()
    )
    
    return render_template('events/detail.html', 
                         event=event, 
                         participation=participation,
                         participations=participations,
                         all_members=all_members,
                         active_tab=active_tab,
                         form=billbro_form,
                         average_ratings=average_ratings,
                         user_rating=user_rating,
                         event_ratings=ratings_sorted,
                         can_rate=can_rate,
                         rating_edit_mode=rating_edit_mode,
                         prev_event=prev_event,
                         next_event=next_event)


@bp.route('/<int:event_id>/billbro-sync', methods=['GET'])
@login_required
def billbro_sync(event_id):
    """Kompakter BillBro-Zustand für Polling im Event-Detail (Tab BillBro)."""
    event = Event.query.get_or_404(event_id)
    participation = Participation.query.filter_by(
        member_id=current_user.id,
        event_id=event_id,
    ).first()
    is_organizer = event.organisator_id == current_user.id
    can_access = (participation and participation.teilnahme) or is_organizer
    if not can_access:
        return jsonify({'error': 'forbidden'}), 403

    attending = sum(1 for p in event.participations if p.teilnahme)
    guesses = sum(
        1
        for p in event.participations
        if p.teilnahme and p.guess_bill_amount_rappen is not None
    )
    resp = jsonify(
        billbro_closed=event.billbro_closed,
        rechnungsbetrag_rappen=event.rechnungsbetrag_rappen,
        gesamtbetrag_rappen=event.gesamtbetrag_rappen,
        trinkgeld_rappen=event.trinkgeld_rappen,
        attending=attending,
        guesses=guesses,
        betrag_sparsam_rappen=event.betrag_sparsam_rappen,
        betrag_normal_rappen=event.betrag_normal_rappen,
        betrag_allin_rappen=event.betrag_allin_rappen,
    )
    resp.headers['Cache-Control'] = 'no-store'
    return resp


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
        try:
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
            if form.place_id.data or form.place_name.data or form.place_address.data:
                event.place_id = form.place_id.data
                event.place_name = form.place_name.data
                event.place_address = form.place_address.data
                
                # Safe conversion for latitude
                try:
                    event.place_lat = float(form.place_lat.data) if form.place_lat.data else None
                except (ValueError, TypeError):
                    event.place_lat = None
                
                # Safe conversion for longitude
                try:
                    event.place_lng = float(form.place_lng.data) if form.place_lng.data else None
                except (ValueError, TypeError):
                    event.place_lng = None
                
                # Safe JSON parsing for place types
                try:
                    event.place_types = json.loads(form.place_types.data) if form.place_types.data else None
                except (json.JSONDecodeError, TypeError):
                    event.place_types = None
                
                event.place_website = form.place_website.data
                event.place_maps_url = form.place_maps_url.data
                
                # Safe conversion for price level
                try:
                    event.place_price_level = int(form.place_price_level.data) if form.place_price_level.data else None
                except (ValueError, TypeError):
                    event.place_price_level = None
                
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
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating event {event_id}: {str(e)}')
            flash(f'Fehler beim Speichern des Events: {str(e)}', 'error')
            return render_template('events/edit.html', form=form, event=event)
    
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
            'event_title': event.restaurant or f"{event.event_typ.value if hasattr(event.event_typ, 'value') else str(event.event_typ)} am {event.display_date}",
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
    
    # Prüfe, ob der Request vom Dashboard kommt (Referer-Header)
    referer = request.headers.get('Referer', '')
    if 'dashboard' in referer:
        return redirect(url_for('dashboard.index'))
    else:
        return redirect(url_for('events.detail', event_id=event_id))

@bp.route('/<int:event_id>/send_rsvp_reminder', methods=['POST'])
@login_required
def send_rsvp_reminder(event_id):
    """Send RSVP reminder via Push Notifications to members who haven't responded yet"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user is organizer or admin
    if not (current_user.is_admin or event.organisator_id == current_user.id):
        flash('Nur der Organisator kann Erinnerungen senden', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Use PushNotificationService to send reminders
    from backend.services.push_notifications import PushNotificationService
    result = PushNotificationService.send_participation_reminder_to_members(event_id)
    
    # Log audit event
    from backend.services.security import SecurityService, AuditAction
    SecurityService.log_audit_event(
        AuditAction.EVENT_SEND_REMINDER, 'event', event.id,
        extra_data={
            'event_id': event_id,
            'result': result
        }
    )
    
    if result.get('success'):
        sent_count = result.get('sent_count', 0)
        members_count = result.get('members_count', 0)
        if sent_count > 0:
            flash(f'✅ Push-Benachrichtigung an {sent_count} Geräte von {members_count} Mitgliedern gesendet!', 'success')
        else:
            flash(f'ℹ️ {members_count} Mitglied(er) haben noch nicht geantwortet, aber keine Push-Subscriptions.', 'info')
    else:
        flash(f'⚠️ Fehler: {result.get("message", "Unbekannter Fehler")}', 'warning')
    
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
    """Redirect to stats tab"""
    return redirect(url_for('events.index', tab='stats'))

# Import here to avoid circular imports
from datetime import datetime 