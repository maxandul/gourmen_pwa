from flask import Blueprint, render_template, jsonify, current_app, send_from_directory
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from datetime import datetime, date

bp = Blueprint('public', __name__)

@bp.route('/')
def landing():
    """Landing page"""
    try:
        # Get next upcoming published event
        latest_event = Event.query.filter_by(published=True).filter(
            Event.datum >= datetime.utcnow()
        ).order_by(Event.datum.asc()).first()

        # Public stats
        member_count = Member.query.filter_by(is_active=True).count()
        
        # Count unique restaurants from both 'restaurant' and 'place_name' fields
        from sqlalchemy import func, case
        restaurant_names = (
            db.session.query(
                func.coalesce(Event.place_name, Event.restaurant).label('name')
            )
            .filter(
                Event.published == True,
                Event.datum < datetime.utcnow(),
                db.or_(
                    db.and_(Event.restaurant.isnot(None), Event.restaurant != ''),
                    db.and_(Event.place_name.isnot(None), Event.place_name != '')
                )
            )
            .distinct()
            .all()
        )
        restaurant_count = len(restaurant_names)
        
        days_since_foundation = (datetime.utcnow().date() - date(2021, 11, 21)).days

        return render_template(
            'public/landing.html',
            latest_event=latest_event,
            member_count=member_count,
            restaurant_count=restaurant_count,
            days_since_foundation=days_since_foundation,
        )
    except Exception as e:
        # Fallback if database is not ready
        return render_template(
            'public/landing.html',
            latest_event=None,
            member_count=0,
            restaurant_count=0,
            days_since_foundation=(datetime.utcnow().date() - date(2021, 11, 21)).days,
        )

@bp.route('/health')
def health():
    """Basic health check - no DB access"""
    try:
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/health/db')
def health_db():
    """Database health check"""
    try:
        # Simple database query
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': 'disconnected', 'error': str(e)}), 503

# Offline-Route entfernt - wird jetzt über Toast-System und Service Worker gehandhabt 

@bp.route('/sw.js')
def service_worker():
    """Serve the Service Worker from the root scope.

    This ensures the Service Worker controls the entire app (scope '/').
    """
    try:
        response = send_from_directory(current_app.static_folder, 'sw.js', mimetype='application/javascript')
        # Allow root scope for the service worker
        response.headers['Service-Worker-Allowed'] = '/'
        # Avoid aggressive caching during development
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except Exception as e:
        current_app.logger.error(f"Failed to serve service worker: {e}")
        return jsonify({'error': 'Service Worker not found'}), 404