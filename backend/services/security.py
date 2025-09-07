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
    def generate_secure_password(length=16):
        """Generate a secure random password"""
        # Use a mix of characters for better security
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*"
        
        # Ensure at least one character from each category
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + symbols
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
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
    def verify_totp(secret, token, window=3):
        """Verify TOTP token with extended window for time synchronization"""
        totp = pyotp.TOTP(secret)
        result = totp.verify(token, valid_window=window)
        
        # Debug-Logging für 2FA-Problem
        try:
            from flask import current_app
            current_app.logger.info(f"TOTP Debug: token={token}, secret_length={len(secret)}, window={window}, result={result}")
            
            # Zeige aktuellen TOTP-Code für Debugging
            current_code = totp.now()
            current_app.logger.info(f"TOTP Debug: current_code={current_code}, input_token={token}")
            
        except Exception as e:
            # Ignoriere Logging-Fehler
            pass
            
        return result
    
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
        
        try:
            import time
            current_timestamp = int(time.time())
            access_until_timestamp = session['sensitive_access_until']
            has_access = current_timestamp < access_until_timestamp
            
            # Debug logging
            try:
                from flask import current_app
                current_datetime = datetime.fromtimestamp(current_timestamp)
                access_until_datetime = datetime.fromtimestamp(access_until_timestamp)
                current_app.logger.info(f"Step-up access check: {has_access}")
                current_app.logger.info(f"Current time: {current_datetime} (timestamp: {current_timestamp})")
                current_app.logger.info(f"Access until: {access_until_datetime} (timestamp: {access_until_timestamp})")
                current_app.logger.info(f"Time difference: {access_until_timestamp - current_timestamp}s")
            except:
                pass
            
            return has_access
        except Exception as e:
            # If parsing fails, clear the corrupted session data
            session.pop('sensitive_access_until', None)
            return False
    
    @staticmethod
    def grant_step_up_access():
        """Grant step-up access for configured duration"""
        try:
            from flask import current_app
            ttl_seconds = current_app.config.get('SENSITIVE_ACCESS_TTL_SECONDS', 1800)  # 30 Minuten statt 5
        except:
            # Fallback if current_app not available
            ttl_seconds = 1800  # 30 Minuten
        
        # Verwende Unix Timestamp (zeitzonenunabhängig)
        import time
        access_until_timestamp = int(time.time()) + ttl_seconds
        session['sensitive_access_until'] = access_until_timestamp
        
        # Debug logging
        try:
            from flask import current_app
            access_until_datetime = datetime.fromtimestamp(access_until_timestamp)
            current_app.logger.info(f"Step-up access granted until {access_until_datetime} (TTL: {ttl_seconds}s)")
            current_app.logger.info(f"Session timestamp: {access_until_timestamp}")
        except:
            pass
    
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
        has_access = SecurityService.check_step_up_access()
        
        # Debug logging
        try:
            from flask import current_app
            current_app.logger.info(f"require_step_up check for {request.url}: {has_access}")
        except:
            pass
        
        if not has_access:
            flash('Zugriff auf sensible Daten erfordert erneute Authentifizierung', 'warning')
            return redirect(url_for('auth.step_up', next=request.url))
        return f(*args, **kwargs)
    
    return decorated_function 