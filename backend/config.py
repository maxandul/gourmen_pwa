import os
from datetime import timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def _normalize_database_url(raw_url: str | None) -> str:
    """Normalize DATABASE_URL to use psycopg (v3) driver.

    Converts e.g. postgres://... or postgresql://... to postgresql+psycopg://...
    Keeps sqlite URLs unchanged.
    """
    if not raw_url:
        return 'sqlite:///instance/gourmen_dev.db'

    # Keep sqlite URIs as-is
    if raw_url.startswith('sqlite:'):
        return raw_url

    # If already specifies a dialect+driver, keep if it's psycopg, else switch to psycopg
    if raw_url.startswith('postgresql+'):  # e.g. postgresql+psycopg2, postgresql+psycopg
        # Force psycopg (v3)
        return raw_url.replace('postgresql+psycopg2', 'postgresql+psycopg')

    # Handle common Heroku/Railway style URLs
    if raw_url.startswith('postgres://'):
        return 'postgresql+psycopg://' + raw_url[len('postgres://'):]
    if raw_url.startswith('postgresql://'):
        return 'postgresql+psycopg://' + raw_url[len('postgresql://'):]

    return raw_url


class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get('DATABASE_URL'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Timezone settings
    TZ = os.environ.get('TZ', 'Europe/Zurich')
    
    # 2FA settings
    TWOFA_ISSUER = os.environ.get('TWOFA_ISSUER', 'Gourmen')
    
    # Security settings
    CRYPTO_KEY = os.environ.get('CRYPTO_KEY')
    SENSITIVE_ACCESS_TTL_SECONDS = int(os.environ.get('SENSITIVE_ACCESS_TTL_SECONDS', '300'))
    
    # Rate limiting
    RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN', '5 per minute')
    RATE_LIMIT_STEPUP = os.environ.get('RATE_LIMIT_STEPUP', '5 per minute')
    
    # CSP settings
    SECURITY_CSP = os.environ.get('SECURITY_CSP', 
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
    
    # Cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # CSRF settings
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour instead of default 1 hour
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_EXEMPT_LIST = ['cron.3_week_reminders', 'cron.cleanup_subscriptions', 'cron.cron_test']
    
    # Admin initialization
    INIT_ADMIN_EMAIL = os.environ.get('INIT_ADMIN_EMAIL', 'admin@gourmen.ch')
    INIT_ADMIN_PASSWORD = os.environ.get('INIT_ADMIN_PASSWORD', 'change_me_admin')
    
    # Google Places API
    GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
    
    # Google Maps API Keys
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    GOOGLE_MAPS_API_KEY_FRONTEND = os.environ.get('GOOGLE_MAPS_API_KEY_FRONTEND')
    
    # Web Push / VAPID settings
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') or '''-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgEdtTmIlV1qFlMk2W
Uo77Fhga7xJIsxvTaa+BO+fIpdOhRANCAAS+wTXZ+vAHf40PxqrCTmKY8VVz3qjz
kmJoT3rhruZ0IqvRnzHGAjFhfujEn14yX6xmg/Gyn2NGJDNUmQLd+XLX
-----END PRIVATE KEY-----'''
    
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY') or '''-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEvsE12frwB3+ND8aqwk5imPFVc96o
85JiaE964a7mdCKr0Z8xxgIxYX7oxJ9eMl+sZoPxsp9jRiQzVJkC3fly1w==
-----END PUBLIC KEY-----'''
    
    VAPID_CLAIMS = {
        'sub': 'mailto:admin@gourmen.ch'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # HSTS
    HSTS_INCLUDE_SUBDOMAINS = True
    HSTS_PRELOAD = True
    HSTS_MAX_AGE = 31536000

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 