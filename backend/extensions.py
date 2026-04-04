from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Database
db = SQLAlchemy()
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
login_manager.login_message_category = 'info'

# Security
csrf = CSRFProtect()

# Rate limiting - will be initialized in init_extensions()
limiter = None

def init_extensions(app):
    """Initialize all Flask extensions"""
    global limiter
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Flask-Limiter: optional deaktivierbar (development/testing → RATELIMIT_ENABLED=False)
    limit_enabled = app.config.get('RATELIMIT_ENABLED', True)
    redis_url = app.config.get('REDIS_URL')
    default_limits = ["200 per day", "50 per hour"] if limit_enabled else []

    if not limit_enabled:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[],
            enabled=False,
        )
        app.logger.info("Flask-Limiter deaktiviert (RATELIMIT_ENABLED=False)")
    elif redis_url:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=default_limits,
            storage_uri=redis_url,
        )
        app.logger.info("Flask-Limiter initialized with Redis storage")
    else:
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=default_limits,
        )
        app.logger.warning(
            "Flask-Limiter initialized with in-memory storage (not recommended for production)"
        )
    
    # Configure login manager
    @login_manager.user_loader
    def load_user(user_id):
        from backend.models.member import Member
        return Member.query.get(int(user_id)) 