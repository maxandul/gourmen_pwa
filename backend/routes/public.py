from flask import Blueprint, render_template, jsonify
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from datetime import datetime, date

bp = Blueprint('public', __name__)

@bp.route('/')
def landing():
    """Landing page"""
    # Get latest published event
    latest_event = Event.query.filter_by(published=True).order_by(Event.datum.desc()).first()

    # Public stats
    member_count = Member.query.filter_by(is_active=True).count()
    restaurant_count = (
        db.session.query(Event.restaurant)
        .filter(
            Event.published == True,
            Event.datum < datetime.utcnow(),
            Event.restaurant.isnot(None),
            Event.restaurant != ''
        )
        .distinct()
        .count()
    )
    days_since_foundation = (datetime.utcnow().date() - date(2021, 11, 21)).days

    return render_template(
        'public/landing.html',
        latest_event=latest_event,
        member_count=member_count,
        restaurant_count=restaurant_count,
        days_since_foundation=days_since_foundation,
    )

@bp.route('/health')
def health():
    """Basic health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

@bp.route('/health/db')
def health_db():
    """Database health check"""
    try:
        # Simple database query
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': 'disconnected', 'error': str(e)}), 503

@bp.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html') 