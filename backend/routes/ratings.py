from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.event import Event
from backend.models.rating import EventRating
from backend.models.participation import Participation
from backend.forms.rating import EventRatingForm

bp = Blueprint('ratings', __name__)

@bp.route('/event/<int:event_id>/rate', methods=['GET', 'POST'])
@login_required
def rate_event(event_id):
    """Rate an event (handled inline im Event-Tab)"""
    event = Event.query.get_or_404(event_id)
    is_organizer = event.organisator_id == current_user.id
    next_url = request.args.get('next') or request.form.get('next')

    if not event.allow_ratings:
        flash('Bewertungen sind für dieses Event deaktiviert.', 'error')
        return redirect(next_url or url_for('events.detail', event_id=event_id, tab='info'))
    
    # Check if user participated in this event
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not ((participation and participation.teilnahme) or is_organizer):
        flash('Bewertungen sind nur für Teilnehmende oder Organisatoren möglich.', 'error')
        return redirect(next_url or url_for('events.detail', event_id=event_id, tab='ratings'))
    
    # Check if user has already rated this event
    existing_rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    if existing_rating:
        flash('Sie haben dieses Event bereits bewertet.', 'info')
        return redirect(next_url or url_for('events.detail', event_id=event_id, tab='ratings'))
    
    form = EventRatingForm()
    if form.validate_on_submit():
        rating = EventRating(
            event_id=event_id,
            participant_id=current_user.id,
            food_rating=form.food_rating.data,
            drinks_rating=form.drinks_rating.data,
            service_rating=form.service_rating.data,
            highlights=form.highlights.data
        )
        db.session.add(rating)
        db.session.commit()
        flash('Vielen Dank für Ihre Bewertung!', 'success')
        return redirect(next_url or url_for('events.detail', event_id=event_id, tab='ratings'))
    
    # GET oder Validierungsfehler → zurück in den Ratings-Tab
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'error')
    return redirect(next_url or url_for('events.detail', event_id=event_id, tab='ratings'))

@bp.route('/event/<int:event_id>/ratings')
@login_required
def view_ratings(event_id):
    """View all ratings for an event"""
    event = Event.query.get_or_404(event_id)
    is_organizer = event.organisator_id == current_user.id

    if not event.allow_ratings:
        flash('Bewertungen sind für dieses Event deaktiviert.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='info'))
    
    # Check if user participated in this event or is admin
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not ((participation and participation.teilnahme) or is_organizer):
        flash('Sie haben keine Berechtigung, die Bewertungen zu sehen.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))
    
    return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))

@bp.route('/event/<int:event_id>/ratings/api')
@login_required
def get_ratings_api(event_id):
    """API endpoint to get ratings for an event"""
    event = Event.query.get_or_404(event_id)
    is_organizer = event.organisator_id == current_user.id

    if not event.allow_ratings:
        return jsonify({'error': 'Bewertungen deaktiviert'}), 403
    
    # Check if user participated in this event or is admin
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not ((participation and participation.teilnahme) or is_organizer):
        return jsonify({'error': 'Keine Berechtigung'}), 403
    
    ratings = event.get_ratings()
    average_ratings = event.get_average_ratings()
    
    return jsonify({
        'ratings': [rating.to_dict() for rating in ratings],
        'average_ratings': average_ratings
    })

@bp.route('/event/<int:event_id>/rating/edit', methods=['GET', 'POST'])
@login_required
def edit_rating(event_id):
    """Edit existing rating (inline im Event-Tab)"""
    event = Event.query.get_or_404(event_id)

    if not event.allow_ratings:
        flash('Bewertungen sind für dieses Event deaktiviert.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='info'))
    
    # Get existing rating
    rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    if not rating:
        flash('Keine Bewertung gefunden.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))
    
    form = EventRatingForm(obj=rating)
    if form.validate_on_submit():
        rating.food_rating = form.food_rating.data
        rating.drinks_rating = form.drinks_rating.data
        rating.service_rating = form.service_rating.data
        rating.highlights = form.highlights.data
        
        db.session.commit()
        
        flash('Ihre Bewertung wurde aktualisiert.', 'success')
        return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))
    
    # GET oder Validierungsfehler → zurück in den Ratings-Tab mit Edit-Mode
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'error')
    return redirect(url_for('events.detail', event_id=event_id, tab='ratings', edit_rating='1'))

@bp.route('/event/<int:event_id>/rating/delete', methods=['POST'])
@login_required
def delete_rating(event_id):
    """Delete rating"""
    rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    event = Event.query.get_or_404(event_id)
    if not event.allow_ratings:
        flash('Bewertungen sind für dieses Event deaktiviert.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='info'))
    
    if not rating:
        flash('Keine Bewertung gefunden.', 'error')
        return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))
    
    db.session.delete(rating)
    db.session.commit()
    
    flash('Ihre Bewertung wurde gelöscht.', 'success')
    return redirect(url_for('events.detail', event_id=event_id, tab='ratings'))
