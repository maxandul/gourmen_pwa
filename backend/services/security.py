import json
import secrets
import string
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
from flask import current_app, session, request
from backend.extensions import db
from backend.models.audit_event import AuditEvent, AuditAction

class SecurityService:
    """Security service for password hashing, encryption, 2FA, and step-up authentication"""
    
    @staticmethod
    def hash_password(password):
        """Hash a password"""
        return generate_password_hash(password)
    
    @staticmethod
    def check_password(password_hash, password):
        """Check a password against its hash"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength (minimum 12 characters)"""
        if len(password) < 12:
            return False, "Passwort muss mindestens 12 Zeichen lang sein"
        return True, "Passwort ist stark genug"
    
    @staticmethod
    def get_fernet():
        """Get Fernet instance for encryption"""
        key = current_app.config.get('CRYPTO_KEY')
        if not key:
            raise ValueError("CRYPTO_KEY not configured")
        return Fernet(key.encode() if isinstance(key, str) else key)
    
    @staticmethod
    def encrypt_json(data):
        """Encrypt JSON data"""
        fernet = SecurityService.get_fernet()
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        encrypted = fernet.encrypt(json_str.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    @staticmethod
    def decrypt_json(encrypted_data):
        """Decrypt JSON data"""
        fernet = SecurityService.get_fernet()
        decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
        return json.loads(decrypted.decode('utf-8'))
    
    @staticmethod
    def generate_totp_secret():
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_totp_uri(email, secret, issuer=None):
        """Generate TOTP URI for authenticator apps"""
        if not issuer:
            issuer = current_app.config.get('TWOFA_ISSUER', 'Gourmen')
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    
    @staticmethod
    def verify_totp(secret, token, window=1):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code):
        """Hash a backup code"""
        return generate_password_hash(code)
    
    @staticmethod
    def check_backup_code(code_hash, code):
        """Check a backup code"""
        return check_password_hash(code_hash, code)
    
    @staticmethod
    def mask_sensitive_data(data, fields_to_mask):
        """Mask sensitive data fields"""
        masked_data = data.copy()
        for field in fields_to_mask:
            if field in masked_data and masked_data[field]:
                value = str(masked_data[field])
                if len(value) > 4:
                    masked_data[field] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_data[field] = '*' * len(value)
        return masked_data
    
    @staticmethod
    def unmask_sensitive_data(data):
        """Unmask sensitive data (returns original data)"""
        return data
    
    @staticmethod
    def check_step_up_access():
        """Check if user has step-up access"""
        if not session.get('sensitive_access_until'):
            return False
        
        access_until = datetime.fromisoformat(session['sensitive_access_until'])
        return datetime.utcnow() < access_until
    
    @staticmethod
    def grant_step_up_access():
        """Grant step-up access for configured duration"""
        ttl_seconds = current_app.config.get('SENSITIVE_ACCESS_TTL_SECONDS', 300)
        access_until = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        session['sensitive_access_until'] = access_until.isoformat()
    
    @staticmethod
    def revoke_step_up_access():
        """Revoke step-up access"""
        session.pop('sensitive_access_until', None)
    
    @staticmethod
    def log_audit_event(action, entity, entity_id=None, field=None, extra_data=None):
        """Log an audit event"""
        try:
            from flask_login import current_user
            actor_id = current_user.id if current_user.is_authenticated else None
            
            audit_event = AuditEvent(
                actor_id=actor_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                field=field,
                ip=request.remote_addr if request else None,
                extra_json=extra_data
            )
            
            db.session.add(audit_event)
            db.session.commit()
        except Exception as e:
            # Don't let audit logging break the main functionality
            current_app.logger.error(f"Failed to log audit event: {e}")
    
def require_step_up(f):
    """Decorator to require step-up authentication"""
    from functools import wraps
    from flask import abort, flash, redirect, url_for, request
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SecurityService.check_step_up_access():
            flash('Zugriff auf sensible Daten erfordert erneute Authentifizierung', 'warning')
            return redirect(url_for('auth.step_up', next=request.url))
        return f(*args, **kwargs)
    
    return decorated_function 