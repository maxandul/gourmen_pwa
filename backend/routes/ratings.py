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
    """Rate an event"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user participated in this event
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not participation or not participation.teilnahme:
        flash('Sie können nur Events bewerten, an denen Sie teilgenommen haben.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Check if user has already rated this event
    existing_rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    if existing_rating:
        flash('Sie haben dieses Event bereits bewertet.', 'info')
        return redirect(url_for('events.detail', event_id=event_id))
    
    # Check if event is in the past or today
    if event.is_upcoming:
        flash('Sie können nur vergangene Events oder Events am heutigen Tag bewerten.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
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
        return redirect(url_for('events.detail', event_id=event_id))
    
    return render_template('ratings/rate_event.html', 
                         event=event, 
                         form=form)

@bp.route('/event/<int:event_id>/ratings')
@login_required
def view_ratings(event_id):
    """View all ratings for an event"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user participated in this event or is admin
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not participation and not current_user.is_admin:
        flash('Sie haben keine Berechtigung, die Bewertungen zu sehen.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    ratings = event.get_ratings()
    average_ratings = event.get_average_ratings()
    
    return render_template('ratings/view_ratings.html',
                         event=event,
                         ratings=ratings,
                         average_ratings=average_ratings)

@bp.route('/event/<int:event_id>/ratings/api')
@login_required
def get_ratings_api(event_id):
    """API endpoint to get ratings for an event"""
    event = Event.query.get_or_404(event_id)
    
    # Check if user participated in this event or is admin
    participation = Participation.query.filter_by(
        event_id=event_id, 
        member_id=current_user.id
    ).first()
    
    if not participation and not current_user.is_admin:
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
    """Edit existing rating"""
    event = Event.query.get_or_404(event_id)
    
    # Get existing rating
    rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    if not rating:
        flash('Keine Bewertung gefunden.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    form = EventRatingForm(obj=rating)
    
    if form.validate_on_submit():
        rating.food_rating = form.food_rating.data
        rating.drinks_rating = form.drinks_rating.data
        rating.service_rating = form.service_rating.data
        rating.highlights = form.highlights.data
        
        db.session.commit()
        
        flash('Ihre Bewertung wurde aktualisiert.', 'success')
        return redirect(url_for('events.detail', event_id=event_id))
    
    return render_template('ratings/edit_rating.html',
                         event=event,
                         rating=rating,
                         form=form)

@bp.route('/event/<int:event_id>/rating/delete', methods=['POST'])
@login_required
def delete_rating(event_id):
    """Delete rating"""
    rating = EventRating.query.filter_by(
        event_id=event_id, 
        participant_id=current_user.id
    ).first()
    
    if not rating:
        flash('Keine Bewertung gefunden.', 'error')
        return redirect(url_for('events.detail', event_id=event_id))
    
    db.session.delete(rating)
    db.session.commit()
    
    flash('Ihre Bewertung wurde gelöscht.', 'success')
    return redirect(url_for('events.detail', event_id=event_id))
