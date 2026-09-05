import os
import re
from flask import Flask, render_template, redirect, request
from flask import send_from_directory, make_response
from backend.extensions import db
from backend.config import config
from backend.extensions import init_extensions
from sqlalchemy import text
from backend.models import member, member_sensitive, member_mfa, mfa_backup_code, event, participation, document, audit_event, auth_token
# PushSubscription Model wird über backend.models importiert wenn benötigt

# Content-Hash im Dateinamen, z. B. main-v2.fa47ba3e.css -> unveraenderlich cachebar.
_FINGERPRINTED_ASSET = re.compile(r"\.[0-9a-f]{8}\.[a-z0-9]+$", re.IGNORECASE)


def create_app(config_name=None):
    """Application factory"""
    try:
        if config_name is None:
            config_name = os.environ.get('FLASK_ENV', 'development')
        
        
        
        app = Flask(__name__, template_folder='../templates', static_folder='../static')
        app.config.from_object(config[config_name])
        
        # Ensure UTF-8 encoding
        app.config['JSON_AS_ASCII'] = False
        
        # Initialize extensions
        init_extensions(app)

        @app.before_request
        def redirect_apex_to_www():
            """Apex gourmen.ch -> www.gourmen.ch, unter Beibehaltung von Pfad und Query.

            Wichtig fuer SEO und Deeplinks: Eine Umleitung, die den Pfad verwirft,
            wirft jeden Besucher (und jeden Crawler) von gourmen.ch/restaurants auf
            die Startseite und laesst die Linkkraft der Unterseiten verpuffen.

            Achtung: Dieser Handler greift nur, wenn Apex-Requests die App auch
            wirklich erreichen. Derzeit leitet bereits eine Ebene davor (DNS-/
            Edge-Redirect beim Domain-Provider) pauschal auf https://www.gourmen.ch
            um - ohne Pfad. Solange das so konfiguriert ist, laeuft dieser Code
            nicht an; siehe docs/SEO.md.
            """
            if request.method not in ("GET", "HEAD"):
                return None
            host = (request.host or "").split(":")[0].lower()
            if host != "gourmen.ch":
                return None
            target = f"https://www.gourmen.ch{request.path or '/'}"
            qs = request.query_string.decode("utf-8")
            if qs:
                target = f"{target}?{qs}"
            return redirect(target, code=301)
        
        # Test database connection
        try:
            with app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(text('SELECT 1'))
        except Exception as db_error:
            app.logger.warning(f"Database connection test failed: {db_error}")
            # Continue anyway - database might be available later
        
        # Register blueprints
        from backend.routes import public, auth, dashboard, events, billbro, ggl, member, admin, notifications, ratings
        from backend.routes import push_notifications, cron, docs, calendar_feed, accounting

        app.register_blueprint(public.bp)
        app.register_blueprint(auth.bp, url_prefix='/auth')
        app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
        app.register_blueprint(events.bp, url_prefix='/events')
        app.register_blueprint(billbro.bp, url_prefix='/billbro')
        app.register_blueprint(ggl.bp, url_prefix='/ggl')
        app.register_blueprint(member.bp, url_prefix='/member')
        app.register_blueprint(admin.bp, url_prefix='/admin')
        app.register_blueprint(notifications.bp, url_prefix='/notifications')
        app.register_blueprint(ratings.bp, url_prefix='/ratings')
        app.register_blueprint(push_notifications.bp)
        app.register_blueprint(cron.bp)
        app.register_blueprint(docs.bp, url_prefix='/docs')
        app.register_blueprint(calendar_feed.bp)
        app.register_blueprint(accounting.bp, url_prefix='/accounting')
        app.logger.info("Push notifications and cron jobs registered")
        
        # Register error handlers
        register_error_handlers(app)
        
        # Register context processors
        register_context_processors(app)

        # Serve Service Worker from origin root with proper headers
        @app.route('/sw.js')
        def service_worker():
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
            response = make_response(send_from_directory(static_dir, 'sw.js'))
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
            # Ensure the service worker can control the entire origin
            response.headers['Service-Worker-Allowed'] = '/'
            # Avoid caching to allow timely updates
            response.headers['Cache-Control'] = 'no-cache'
            return response
        
        # Add UTF-8 header to HTML responses only
        @app.after_request
        def after_request(response):
            if response.content_type and response.content_type.startswith('text/html'):
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response

        @app.after_request
        def add_static_cache_headers(response):
            """Cache-Header fuer /static/.

            Flask liefert statische Dateien per Default mit `Cache-Control: no-cache`
            aus. Bei rund 50 Assets pro Seitenaufruf heisst das: 50 Revalidierungen
            gegen den Server - hinter einem scannenden Firmenproxy ein spuerbarer
            Klotz, der render-blockierendes CSS ausbremst oder abreissen laesst.

            Gehashte Dateien (main-v2.<hash>.css) sind unveraenderlich und werden
            ein Jahr gecacht. Alles andere unter /static/ bekommt eine kurze
            Lebensdauer, damit ein vergessener Cache-Buster nicht zur Dauerlast wird.
            """
            if response.status_code != 200 or not request.path.startswith('/static/'):
                return response

            if _FINGERPRINTED_ASSET.search(request.path):
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            else:
                response.headers['Cache-Control'] = 'public, max-age=3600'

            # Werkzeug setzt `Content-Disposition: inline; filename=...`. Fuer
            # Subresourcen bringt der Header nichts, triggert aber die
            # Download-Inspektion mancher Security-Gateways.
            response.headers.pop('Content-Disposition', None)
            return response
        
        # Test endpoint
        @app.route('/test')
        def test():
            return {'status': 'ok', 'message': 'App is running successfully'}
        
        # Healthcheck endpoint für Railway
        @app.route('/health')
        def health():
            return {'status': 'healthy', 'message': 'App is healthy'}, 200
        
        # Skip migrations since none exist and DB already has data
        app.logger.info("App created successfully - skipping migrations")
        
        # Admin user initialization will be done manually when needed
        # No automatic initialization to avoid startup issues
        
        app.logger.info("Flask app created and configured successfully")
        return app
        
    except Exception as e:
        # If app creation fails, create a minimal app for debugging
        app = Flask(__name__)
        app.logger.error(f"App creation failed: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        @app.route('/health')
        def health_error():
            return {'status': 'error', 'error': 'App creation failed'}, 500
        
        @app.route('/')
        def index():
            return f'<h1>App Error</h1><p>Error: {e}</p>'
        
        @app.route('/test')
        def test():
            return {'status': 'ok', 'message': 'App is running'}
        
        return app

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

def register_context_processors(app):
    """Register context processors"""
    
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_config():
        return dict(config=app.config)

    @app.context_processor
    def inject_seo():
        """Canonical-URL und Indexierungs-Flag fuer die Meta-Tags in base.html.

        Ohne Canonical konkurrieren fuer Google mehrere URL-Varianten derselben
        Seite (mit/ohne Query, apex/www) miteinander und verwaessern das Ranking.
        `is_public_page` steuert index/noindex: der eingeloggte Vereinsbereich
        gehoert nicht in den Suchindex.
        """
        from flask import has_request_context

        base = app.config.get('PUBLIC_APP_BASE_URL', 'https://www.gourmen.ch').rstrip('/')

        if not has_request_context():
            return dict(canonical_url=base + '/', is_public_page=False)

        canonical = f"{base}{request.path or '/'}"

        # Paginierte Listen kanonisieren auf sich selbst - sonst wertet Google
        # Seite 2+ als Duplikat von Seite 1 und indexiert sie gar nicht erst.
        page_raw = request.args.get('page', '')
        if page_raw.isdigit() and int(page_raw) > 1:
            canonical = f"{canonical}?page={int(page_raw)}"

        endpoint = request.endpoint or ''
        return dict(canonical_url=canonical, is_public_page=endpoint.startswith('public.'))

    @app.context_processor
    def inject_retro_cleanup():
        """Stellt Fortschritt für Datenbereinigung bereit (z. B. Dashboard-Card)."""
        from flask_login import current_user
        from backend.services.retro_cleanup import RetroCleanupService

        if current_user.is_authenticated:
            progress = RetroCleanupService.get_progress(current_user.id)
            return dict(retro_cleanup_progress=progress)

        # Default: kein Login, kein Bedarf
        return dict(retro_cleanup_progress={'total': 0, 'completed': 0, 'pending': 0})
    
    # Register custom Jinja2 filters
    @app.template_filter('cuisine_type_mapper')
    def cuisine_type_mapper(place_type):
        """Map Google Places types to readable cuisine descriptions"""
        cuisine_map = {
            'restaurant': 'Restaurant',
            'italian_restaurant': 'Italienisch',
            'chinese_restaurant': 'Chinesisch',
            'japanese_restaurant': 'Japanisch',
            'thai_restaurant': 'Thai',
            'indian_restaurant': 'Indisch',
            'mexican_restaurant': 'Mexikanisch',
            'greek_restaurant': 'Griechisch',
            'turkish_restaurant': 'Türkisch',
            'spanish_restaurant': 'Spanisch',
            'french_restaurant': 'Französisch',
            'german_restaurant': 'Deutsch',
            'swiss_restaurant': 'Schweizer',
            'pizza_restaurant': 'Pizza',
            'burger_restaurant': 'Burger',
            'steakhouse': 'Steakhouse',
            'seafood_restaurant': 'Meeresfrüchte',
            'vegetarian_restaurant': 'Vegetarisch',
            'vegan_restaurant': 'Vegan',
            'fast_food_restaurant': 'Fast Food',
            'cafe': 'Café',
            'bar': 'Bar',
            'pub': 'Pub',
            'bistro': 'Bistro'
        }
        return cuisine_map.get(place_type, place_type.replace('_', ' ').title())
    
    @app.template_filter('event_type_emoji')
    def event_type_emoji(event_type_value):
        """Add emoji prefix to event type"""
        emoji_map = {
            'MONATSESSEN': '🍽️',
            'GENERALVERSAMMLUNG': '🏛️',
            'AUSFLUG': '🧳',
            'VORSTANDSSITZUNG': '📋',
            'ESSEN_BUCHHALTUNG': '💳',
        }
        emoji = emoji_map.get(event_type_value, '')
        return f"{emoji} {event_type_value}" if emoji else event_type_value

def init_admin_user(app):
    """Initialize admin user if it doesn't exist"""
    from backend.models.member import Member, Role
    from backend.services.security import SecurityService
    
    admin_email = app.config.get('INIT_ADMIN_EMAIL')
    admin_password = app.config.get('INIT_ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        app.logger.warning("Admin credentials not configured, skipping admin user creation")
        return
    
    # Check if admin user already exists
    admin_user = Member.query.filter_by(email=admin_email).first()
    if admin_user:
        app.logger.info(f"Admin user {admin_email} already exists")
        return
    
    # Create admin user
    admin_user = Member(
        email=admin_email,
        vorname='Admin',
        nachname='Gourmen',
        role=Role.ADMIN,
        is_active=True
    )
    admin_user.set_password(admin_password)
    
    try:
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info(f"Created admin user: {admin_email}")
    except Exception as e:
        app.logger.error(f"Failed to create admin user: {e}")
        db.session.rollback()

# Import here to avoid circular imports
from flask import render_template
from backend.extensions import db 