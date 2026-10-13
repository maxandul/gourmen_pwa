import json
import secrets
import string
from datetime import datetime, timedelta
from urllib.parse import unquote, urlsplit
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
from flask import current_app, session, request
from flask_login import current_user
from backend.extensions import db
from backend.models.audit_event import AuditEvent, AuditAction


class SensitiveDataReadError(Exception):
    """Safe public error; unreadable stored data must never become empty form values."""

    def __init__(self):
        super().__init__(
            'Sensible Daten konnten nicht gelesen werden. Die gespeicherten Daten bleiben '
            'unverändert erhalten; es wurde nichts gespeichert. Bitte öffne die Seite erneut. '
            'Falls der Fehler bleibt, kontaktiere den Administrator.'
        )


class SecurityService:
    """Security service for password hashing, encryption, 2FA, and step-up authentication"""

    @staticmethod
    def local_return_target(value):
        """Accept only root-relative URLs, rejecting browser-ambiguous paths."""
        if not isinstance(value, str) or not value.startswith('/'):
            return None
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            return None
        try:
            parsed = urlsplit(value)
        except ValueError:
            return None
        path = unquote(parsed.path)
        if (parsed.scheme or parsed.netloc or value.startswith('//')
                or path.startswith('//') or '\\' in path
                or any(ord(char) < 32 or ord(char) == 127 for char in path)):
            return None
        return value
    
    @staticmethod
    def lock_credential_member(member_id):
        """Serialize credential issuance/change and refresh the member state."""
        from backend.models.member import Member
        return Member.query.filter_by(id=member_id).populate_existing().with_for_update().first()

    @staticmethod
    def invalidate_password_links(member_id, *, purpose=None):
        """Revoke password links in the caller's transaction, never commit here."""
        from backend.models.auth_token import AuthToken, AuthTokenPurpose
        purposes = (AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.ONBOARDING)
        if purpose is not None:
            if purpose not in purposes:
                raise ValueError('Not a password token purpose')
            purposes = (purpose,)
        return AuthToken.query.filter(
            AuthToken.member_id == member_id, AuthToken.purpose.in_(purposes),
            AuthToken.used_at.is_(None),
        ).update({'used_at': datetime.utcnow()}, synchronize_session='fetch')

    @staticmethod
    def invalidate_mfa_reset_links(member_id):
        """Revoke only this member's MFA reset links in the caller's transaction."""
        from backend.models.auth_token import AuthToken, AuthTokenPurpose
        return AuthToken.query.filter_by(
            member_id=member_id, purpose=AuthTokenPurpose.MFA_RESET, used_at=None,
        ).update({'used_at': datetime.utcnow()}, synchronize_session='fetch')

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
    def read_member_sensitive(encrypted_data):
        """Read a member payload without mutation, including before an attempted update."""
        try:
            data = SecurityService.decrypt_json(encrypted_data)
            if not isinstance(data, dict):
                raise ValueError('Expected a member data object')
            return data
        except Exception:
            # Exceptions can contain decrypted content or key material. Never log them.
            current_app.logger.warning('Member sensitive data could not be read; data preserved')
            raise SensitiveDataReadError() from None
    
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
        
        # Only the outcome is safe to log, never entered or generated codes.
        try:
            current_app.logger.info('TOTP verification completed: accepted=%s', result)
        except Exception:
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
    def replace_backup_codes(member_id):
        """Replace codes within the caller's locked credential transaction."""
        from backend.models.mfa_backup_code import MFABackupCode

        codes = SecurityService.generate_backup_codes()
        MFABackupCode.query.filter_by(member_id=member_id).filter(
            MFABackupCode.revoked_at.is_(None)
        ).update({'revoked_at': datetime.utcnow()}, synchronize_session='fetch')
        for code in codes:
            db.session.add(MFABackupCode(
                member_id=member_id, code_hash=SecurityService.hash_backup_code(code)))
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
    def consume_backup_code(member_id, code):
        """Verify a salted hash and persist single use before granting a login."""
        from backend.models.mfa_backup_code import MFABackupCode

        candidates = MFABackupCode.query.filter_by(member_id=member_id).filter(
            MFABackupCode.used_at.is_(None), MFABackupCode.revoked_at.is_(None)
        ).all()
        for candidate in candidates:
            if not SecurityService.check_backup_code(candidate.code_hash, code.upper()):
                continue
            code_id = candidate.id
            try:
                # Recheck eligibility in the write itself: only one request can win.
                changed = MFABackupCode.query.filter_by(id=code_id, member_id=member_id).filter(
                    MFABackupCode.used_at.is_(None), MFABackupCode.revoked_at.is_(None)
                ).update({MFABackupCode.used_at: datetime.utcnow()}, synchronize_session=False)
                if changed != 1:
                    db.session.rollback()
                    return None
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
            return code_id
        return None
    
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
        if (not current_user.is_authenticated
                or session.get('sensitive_access_member_id') != current_user.get_id()):
            SecurityService.revoke_step_up_access()
            return False
        if not session.get('sensitive_access_until'):
            SecurityService.revoke_step_up_access()
            return False
        
        try:
            import time
            current_timestamp = int(time.time())
            access_until_timestamp = session['sensitive_access_until']
            has_access = current_timestamp < access_until_timestamp
            if not has_access:
                SecurityService.revoke_step_up_access()
            
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
            SecurityService.revoke_step_up_access()
            return False
    
    @staticmethod
    def grant_step_up_access():
        """Grant step-up access for configured duration"""
        if not current_user.is_authenticated:
            SecurityService.revoke_step_up_access()
            return False
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
        session['sensitive_access_member_id'] = current_user.get_id()
        
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
        session.pop('sensitive_access_member_id', None)

    @staticmethod
    def clear_auth_transients(sender, user=None, **kwargs):
        """Clear account-bound intermediate state at authentication boundaries."""
        SecurityService.revoke_step_up_access()
        for key in ('2fa_secret', 'pending_2fa_user_id', 'pending_2fa_next', 'step_up_next',
                    'password_change_return'):
            session.pop(key, None)
    
    @staticmethod
    def log_audit_event(action, entity, entity_id=None, field=None, extra_data=None, actor_id=None):
        """Log an audit event"""
        try:
            from flask_login import current_user
            resolved_actor_id = actor_id
            if resolved_actor_id is None:
                resolved_actor_id = current_user.id if current_user.is_authenticated else None
            if resolved_actor_id is None and entity == 'member' and entity_id is not None:
                # Public auth flows have no logged-in user; in that case the member itself is actor.
                resolved_actor_id = entity_id
            
            audit_event = AuditEvent(
                actor_id=resolved_actor_id,
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
            current_app.logger.info('Step-up access check: allowed=%s', has_access)
        except:
            pass
        
        if not has_access:
            flash('Zugriff auf sensible Daten erfordert erneute Authentifizierung', 'warning')
            return redirect(url_for('auth.step_up', next=request.url))
        return f(*args, **kwargs)
    
    return decorated_function
