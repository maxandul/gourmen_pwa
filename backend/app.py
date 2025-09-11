import os
from flask import Flask, render_template
from backend.extensions import db
from backend.config import config
from backend.extensions import init_extensions
from backend.models import member, member_sensitive, member_mfa, mfa_backup_code, event, participation, document, audit_event
from backend.services.notifier import PushSubscription

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
        
        # Register blueprints
        from backend.routes import public, auth, dashboard, events, billbro, stats, ggl, account, admin, docs, notifications, ratings
        
        app.register_blueprint(public.bp)
        app.register_blueprint(auth.bp, url_prefix='/auth')
        app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
        app.register_blueprint(events.bp, url_prefix='/events')
        app.register_blueprint(billbro.bp, url_prefix='/billbro')
        app.register_blueprint(stats.bp, url_prefix='/stats')
        app.register_blueprint(ggl.bp, url_prefix='/ggl')
        app.register_blueprint(account.bp, url_prefix='/account')
        app.register_blueprint(admin.bp, url_prefix='/admin')
        app.register_blueprint(docs.bp, url_prefix='/docs')
        app.register_blueprint(notifications.bp, url_prefix='/notifications')
        app.register_blueprint(ratings.bp, url_prefix='/ratings')
        
        # Register error handlers
        register_error_handlers(app)
        
        # Register context processors
        register_context_processors(app)
        
        # Add UTF-8 header to HTML responses only
        @app.after_request
        def after_request(response):
            if response.content_type and response.content_type.startswith('text/html'):
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        
        # Skip migrations since none exist and DB already has data
        app.logger.info("App created successfully - skipping migrations")
        
        # Only initialize admin user if needed (on first request)
        @app.before_first_request
        def initialize_admin_user():
            """Initialize admin user on first request"""
            try:
                init_admin_user(app)
                app.logger.info("Admin user check completed")
            except Exception as e:
                app.logger.warning(f"Admin user initialization skipped: {e}")
                pass
        
        app.logger.info("Flask app created and configured successfully")
        return app
        
    except Exception as e:
        # If app creation fails, create a minimal app for debugging
        app = Flask(__name__)
        app.logger.error(f"App creation failed: {e}")
        
        @app.route('/health')
        def health():
            return {'status': 'error', 'error': str(e)}, 500
        
        @app.route('/')
        def index():
            return f'<h1>App Error</h1><p>Error: {e}</p>'
        
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