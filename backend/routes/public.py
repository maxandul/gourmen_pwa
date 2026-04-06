from flask import Blueprint, render_template, jsonify, current_app, send_from_directory, redirect, url_for, request
from flask_login import current_user
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member
from datetime import datetime
from sqlalchemy import func

from backend.services.monatsessen_stats import (
    get_landing_extras,
    get_landing_restaurant_table,
)

bp = Blueprint('public', __name__)

@bp.route('/')
def landing():
    """Landing page - redirects to dashboard if user is logged in (unless explicitly requested)"""
    # Only redirect to dashboard if user is authenticated AND didn't explicitly request landing page
    show_landing = request.args.get('show', '0') == '1'
    
    if current_user.is_authenticated and not show_landing:
        return redirect(url_for('dashboard.index'))

    try:
        page_raw = request.args.get('page', '1')
        try:
            page = int(page_raw)
        except (TypeError, ValueError):
            page = 1
        if page < 1:
            page = 1

        now = datetime.utcnow()
        landing_extra = get_landing_extras(now)
        table_rows, table_total, table_total_pages, table_page = get_landing_restaurant_table(
            now, page=page, per_page=10
        )

        # Public stats
        member_count = Member.query.filter_by(is_active=True).count()
        
        # Count unique restaurants from both 'restaurant' and 'place_name' fields
        restaurant_names = (
            db.session.query(
                func.coalesce(Event.place_name, Event.restaurant).label('name')
            )
            .filter(
                Event.published == True,
                Event.datum < now,
                db.or_(
                    db.and_(Event.restaurant.isnot(None), Event.restaurant != ''),
                    db.and_(Event.place_name.isnot(None), Event.place_name != '')
                )
            )
            .distinct()
            .all()
        )
        restaurant_count = len(restaurant_names)

        return render_template(
            'public/landing.html',
            member_count=member_count,
            restaurant_count=restaurant_count,
            last_restaurant=landing_extra['last_restaurant'],
            next_essen_date=landing_extra['next_essen_date'],
            table_rows=table_rows,
            table_total=table_total,
            table_page=table_page,
            table_total_pages=table_total_pages,
            use_v2_design=True,
        )
    except Exception:
        # Fallback if database is not ready
        return render_template(
            'public/landing.html',
            member_count=0,
            restaurant_count=0,
            last_restaurant=None,
            next_essen_date=None,
            table_rows=[],
            table_total=0,
            table_page=1,
            table_total_pages=1,
            use_v2_design=True,
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
