import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from backend.extensions import db, limiter
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.services.security import SecurityService, AuditAction
from backend.services.mail import MailService

bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    remember_me = BooleanField('Angemeldet bleiben')
    submit = SubmitField('Anmelden')

class TOTPForm(FlaskForm):
    token = StringField('6-stelliger Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verifizieren')

class BackupCodeForm(FlaskForm):
    backup_code = StringField('Backup-Code', validators=[DataRequired(), Length(min=8, max=8)])
    submit = SubmitField('Verifizieren')

class StepUpForm(FlaskForm):
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Bestätigen')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Aktuelles Passwort', validators=[DataRequired()])
    new_password = PasswordField('Neues Passwort', validators=[
        DataRequired(), 
        Length(min=12, message='Passwort muss mindestens 12 Zeichen lang sein')
    ])
    confirm_password = PasswordField('Passwort bestätigen', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwörter müssen übereinstimmen')
    ])
    submit = SubmitField('Passwort ändern')

class ForgotPasswordForm(FlaskForm):
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Zurücksetzen-Link senden')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Neues Passwort', validators=[
        DataRequired(), 
        Length(min=12, message='Passwort muss mindestens 12 Zeichen lang sein')
    ])
    confirm_password = PasswordField('Passwort bestätigen', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwörter müssen übereinstimmen')
    ])
    submit = SubmitField('Passwort zurücksetzen')


def _hash_auth_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_auth_token(member_id: int, purpose: AuthTokenPurpose, expires_in: timedelta, request_ip: str | None):
    token = secrets.token_urlsafe(32)
    token_hash = _hash_auth_token(token)
    token_row = AuthToken(
        member_id=member_id,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=datetime.utcnow() + expires_in,
        request_ip=request_ip,
    )
    db.session.add(token_row)
    return token


def _resolve_auth_token(raw_token: str, purpose: AuthTokenPurpose):
    token_hash = _hash_auth_token(raw_token)
    auth_token = AuthToken.query.filter_by(token_hash=token_hash, purpose=purpose).first()
    if not auth_token:
        return None, "missing"
    if auth_token.used_at is not None:
        return None, "used"
    if auth_token.expires_at < datetime.utcnow():
        return None, "expired"
    return auth_token, None

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = Member.query.filter_by(email=form.email.data, is_active=True).first()
        
        if user and user.check_password(form.password.data):
            # Check if 2FA is enabled
            mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
            if mfa_data and mfa_data.is_totp_enabled:
                # Check if device is remembered
                remembered_device = session.get('remembered_device')
                if remembered_device and remembered_device.get('user_id') == user.id:
                    # Check if device token is still valid
                    import time
                    current_timestamp = int(time.time())
                    expires_at_timestamp = remembered_device['expires_at']
                    
                    if current_timestamp < expires_at_timestamp:
                        # Device is remembered, skip 2FA
                        login_user(user, remember=True)  # Always remember when device is remembered
                        
                        # Log audit event
                        SecurityService.log_audit_event(
                            AuditAction.LOGIN, 'member', user.id,
                            extra_data={'ip': request.remote_addr, 'remembered_device': True}
                        )
                        
                        next_page = request.args.get('next')
                        if not next_page or not next_page.startswith('/'):
                            # Check if user needs to change password
                            if user.needs_password_change:
                                flash('Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.', 'info')
                                next_page = url_for('auth.change_password')
                            else:
                                next_page = url_for('dashboard.index')
                        return redirect(next_page)
                
                # Device not remembered, require 2FA
                session['pending_2fa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa'))
            
            # No 2FA enabled, login normally
            login_user(user, remember=form.remember_me.data)
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.LOGIN, 'member', user.id,
                extra_data={'ip': request.remote_addr}
            )
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                # Check if user needs to change password
                if user.needs_password_change:
                    flash('Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.', 'info')
                    next_page = url_for('auth.change_password')
                else:
                    next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Ungültige E-Mail oder Passwort', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet', 'success')
    return redirect(url_for('public.landing'))

@bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    """2FA verification"""
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = Member.query.get(user_id)
    if not user:
        session.pop('pending_2fa_user_id', None)
        return redirect(url_for('auth.login'))
    
    mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
    if not mfa_data or not mfa_data.is_totp_enabled:
        session.pop('pending_2fa_user_id', None)
        login_user(user)
        # Check if user needs to change password
        if user.needs_password_change:
            flash('Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.', 'info')
            return redirect(url_for('auth.change_password'))
        return redirect(url_for('dashboard.index'))
    
    totp_form = TOTPForm()
    backup_form = BackupCodeForm()
    
    if totp_form.validate_on_submit():
        # Verify TOTP
        secret = SecurityService.decrypt_json(mfa_data.totp_secret_encrypted)
        if SecurityService.verify_totp(secret, totp_form.token.data):
            session.pop('pending_2fa_user_id', None)
            
            # Check if user wants to remember this device
            remember_device = request.form.get('remember_device')
            if remember_device:
                device_token = secrets.token_urlsafe(32)
                import time
                # ~100 Jahre (effectively unlimited) - Unix Timestamp für Zeitzonenunabhängigkeit
                expires_at_timestamp = int(time.time()) + (36500 * 24 * 3600)
                session['remembered_device'] = {
                    'user_id': user.id,
                    'device_token': device_token,
                    'expires_at': expires_at_timestamp
                }
                login_user(user, remember=True)  # Always remember when device is remembered
            else:
                login_user(user, remember=False)
            
            mfa_data.last_verified_at = datetime.utcnow()
            db.session.commit()
            
            SecurityService.log_audit_event(AuditAction.LOGIN, 'member', user.id)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                # Check if user needs to change password
                if user.needs_password_change:
                    flash('Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.', 'info')
                    next_page = url_for('auth.change_password')
                else:
                    next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Ungültiger Code', 'error')
    
    elif backup_form.validate_on_submit():
        # Verify backup code
        backup_code = backup_form.backup_code.data.upper()
        valid_code = MFABackupCode.query.filter_by(
            member_id=user.id,
            code_hash=SecurityService.hash_backup_code(backup_code)
        ).filter(
            MFABackupCode.used_at.is_(None),
            MFABackupCode.revoked_at.is_(None)
        ).first()
        
        if valid_code:
            session.pop('pending_2fa_user_id', None)
            login_user(user, remember=True)  # Always remember when using backup code
            valid_code.used_at = datetime.utcnow()
            db.session.commit()
            
            SecurityService.log_audit_event(
                AuditAction.USE_BACKUP_CODE, 'member', user.id,
                extra_data={'backup_code_id': valid_code.id}
            )
            
            # Check if user needs to change password
            if user.needs_password_change:
                flash('Bitte ändern Sie Ihr Passwort bei der ersten Anmeldung.', 'info')
                return redirect(url_for('auth.change_password'))
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Ungültiger Backup-Code', 'error')
    
    return render_template('auth/verify_2fa.html', totp_form=totp_form, backup_form=backup_form)

@bp.route('/2fa/enroll', methods=['GET', 'POST'])
@login_required
def enroll_2fa():
    """Enroll 2FA - Simplified version"""
    mfa_data = MemberMFA.query.filter_by(member_id=current_user.id).first()
    if not mfa_data:
        mfa_data = MemberMFA(member_id=current_user.id)
        db.session.add(mfa_data)
        db.session.commit()
    
    if mfa_data.is_totp_enabled:
        flash('2FA ist bereits aktiviert', 'info')
        return redirect(url_for('member.profile'))
    
    # Generate new secret only if not already in session
    if '2fa_secret' not in session:
        secret = SecurityService.generate_totp_secret()
        session['2fa_secret'] = secret
        current_app.logger.info(f"2FA Debug: Generated NEW secret for {current_user.email}: {secret}")
    else:
        secret = session['2fa_secret']
        current_app.logger.info(f"2FA Debug: Using EXISTING secret for {current_user.email}: {secret}")
    
    totp_form = TOTPForm()
    
    if totp_form.validate_on_submit():
        if SecurityService.verify_totp(secret, totp_form.token.data):
            # Enable 2FA
            mfa_data.totp_secret_encrypted = SecurityService.encrypt_json(secret)
            mfa_data.is_totp_enabled = True
            mfa_data.activated_at = datetime.utcnow()
            mfa_data.last_verified_at = datetime.utcnow()
            
            # Clear the secret from session
            session.pop('2fa_secret', None)
            
            db.session.commit()
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.ENABLE_2FA, 'member', current_user.id,
                extra_data={'ip': request.remote_addr}
            )
            
            flash('2FA erfolgreich aktiviert!', 'success')
            return redirect(url_for('auth.backup_codes'))
        else:
            flash('Ungültiger Code. Bitte versuchen Sie es erneut.', 'error')
    
    return render_template('auth/enroll_2fa_simple.html', 
                         secret=secret, 
                         form=totp_form,
                         current_user=current_user)

@bp.route('/2fa/disable', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    """Disable 2FA"""
    mfa_data = MemberMFA.query.filter_by(member_id=current_user.id).first()
    if not mfa_data or not mfa_data.is_totp_enabled:
        flash('2FA ist nicht aktiviert', 'info')
        return redirect(url_for('member.profile'))
    
    step_up_form = StepUpForm()
    if step_up_form.validate_on_submit():
        if current_user.check_password(step_up_form.password.data):
            # Disable 2FA
            mfa_data.is_totp_enabled = False
            mfa_data.activated_at = None
            mfa_data.last_verified_at = None
            
            # Revoke all backup codes
            backup_codes = MFABackupCode.query.filter_by(member_id=current_user.id).all()
            for code in backup_codes:
                code.revoked_at = datetime.utcnow()
            
            db.session.commit()
            
            SecurityService.log_audit_event(AuditAction.DISABLE_MFA, 'member_mfa', current_user.id)
            
            flash('2FA erfolgreich deaktiviert', 'success')
            return redirect(url_for('member.profile'))
        else:
            flash('Ungültiges Passwort', 'error')
    
    return render_template('auth/disable_2fa.html', form=step_up_form)

@bp.route('/step-up', methods=['GET', 'POST'])
@login_required
def step_up():
    """Step-up authentication"""
    # Get next page from multiple sources for robustness
    # Use a list comprehension to filter out empty strings
    next_candidates = [
        request.args.get('next'),
        request.form.get('next'),
        request.form.get('next_url'),
        session.get('step_up_next')
    ]
    next_page = next((page for page in next_candidates if page and page.strip()), None)
    
    # Debug logging
    current_app.logger.info(f"Step-up called with next_page: {next_page}")
    current_app.logger.info(f"Request args: {dict(request.args)}")
    current_app.logger.info(f"Request form: {dict(request.form)}")
    current_app.logger.info(f"Session step_up_next: {session.get('step_up_next')}")
    
    # Store next page in session for reliability (only on GET or if not already set)
    if next_page and next_page.startswith('/'):
        session['step_up_next'] = next_page
        current_app.logger.info(f"Stored next_page in session: {next_page}")
    elif not session.get('step_up_next'):
        current_app.logger.info(f"Invalid or missing next_page: {next_page}")
    
    # If user already has step-up access, redirect to the requested page
    if SecurityService.check_step_up_access():
        # Use session-stored next page if available
        stored_next = session.get('step_up_next')
        if stored_next:
            session.pop('step_up_next', None)  # Clear after use
            current_app.logger.info(f"Already authenticated, redirecting to stored next: {stored_next}")
            return redirect(stored_next)
        elif next_page and next_page.startswith('/'):
            current_app.logger.info(f"Already authenticated, redirecting to next: {next_page}")
            return redirect(next_page)
        else:
            current_app.logger.info("Already authenticated, no next page, redirecting to dashboard")
            return redirect(url_for('dashboard.index'))
    
    form = StepUpForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            # Grant step-up access BEFORE redirect
            SecurityService.grant_step_up_access()
            SecurityService.log_audit_event(AuditAction.LOGIN, 'member', current_user.id)
            
            # Get the final next page to redirect to
            final_next = session.get('step_up_next') or next_page
            
            # Debug logging
            current_app.logger.info(f"Step-up successful for user {current_user.id}")
            current_app.logger.info(f"Next page from form: {next_page}")
            current_app.logger.info(f"Next page from session: {session.get('step_up_next')}")
            current_app.logger.info(f"Final next page: {final_next}")
            
            # Clear session after reading
            session.pop('step_up_next', None)
            
            # Redirect to the final next page
            if final_next and final_next.startswith('/'):
                current_app.logger.info(f"Redirecting to: {final_next}")
                return redirect(final_next)
            else:
                current_app.logger.info("No valid next page, redirecting to dashboard")
                return redirect(url_for('dashboard.index'))
        else:
            flash('Ungültiges Passwort', 'error')
    
    # Always pass the next page to the template (prefer session value)
    template_next = session.get('step_up_next') or next_page
    return render_template('auth/step_up.html', form=form, next=template_next)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged in user"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Aktuelles Passwort ist falsch', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Validate new password strength
        is_valid, message = SecurityService.validate_password_strength(form.new_password.data)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Check if new password is different from current
        if current_user.check_password(form.new_password.data):
            flash('Neues Passwort muss sich vom aktuellen unterscheiden', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Check if this was the first login (password_changed_at was None before)
        was_first_login = current_user.password_changed_at is None
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.CHANGE_PASSWORD, 'member', current_user.id,
            extra_data={'ip': request.remote_addr}
        )
        
        flash('Passwort erfolgreich geändert', 'success')
        
        # Redirect based on whether this was first login or normal password change
        if was_first_login:
            return redirect(url_for('dashboard.index'))
        else:
            return redirect(url_for('member.profile'))
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=['POST'])
def forgot_password():
    """Request password reset by mail without user enumeration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = Member.query.filter_by(email=form.email.data, is_active=True).first()

        if user:
            token = _issue_auth_token(
                member_id=user.id,
                purpose=AuthTokenPurpose.PASSWORD_RESET,
                expires_in=timedelta(hours=1),
                request_ip=request.remote_addr,
            )
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            html = render_template(
                'emails/password_reset.html',
                display_name=user.display_name,
                reset_url=reset_url,
                valid_for='1 Stunde',
            )
            text = (
                f"Hallo {user.display_name}\n\n"
                "Du hast eine Anfrage zum Zuruecksetzen deines Passworts gestellt.\n"
                f"Setze dein Passwort ueber diesen Link zurueck: {reset_url}\n\n"
                "Der Link ist 1 Stunde gueltig.\n"
                "Falls du das nicht warst, kannst du diese Mail ignorieren."
            )
            MailService.send_async(
                to=user.email,
                subject='Gourmen Passwort zuruecksetzen',
                html=html,
                text=text,
                tags={'type': 'password_reset', 'member_id': str(user.id)},
            )
            SecurityService.log_audit_event(
                AuditAction.REQUEST_PASSWORD_RESET,
                'member',
                user.id,
                extra_data={'ip': request.remote_addr},
                actor_id=user.id,
            )
            db.session.commit()

        flash('Wenn die Adresse existiert, wurde eine Mail versendet.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.PASSWORD_RESET)
    if token_error == "missing":
        flash('Ungültiger oder abgelaufener Reset-Link', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "used":
        flash('Dieser Reset-Link wurde bereits verwendet.', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "expired":
        flash('Reset-Link ist abgelaufen', 'error')
        return redirect(url_for('auth.login'))

    user = Member.query.get(auth_token.member_id)
    if not user or not user.is_active:
        flash('Ungültiger Reset-Link', 'error')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Validate password strength
        is_valid, message = SecurityService.validate_password_strength(form.new_password.data)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/reset_password.html', form=form, token=token)
        
        # Update password
        user.set_password(form.new_password.data)
        auth_token.used_at = datetime.utcnow()
        db.session.commit()

        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.RESET_PASSWORD, 'member', user.id,
            extra_data={'ip': request.remote_addr},
            actor_id=user.id,
        )
        
        flash('Passwort erfolgreich zurücksetzt. Sie können sich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

# 2FA Reset via Email
@bp.route('/2fa/reset-request', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def request_2fa_reset():
    """Request 2FA reset via email"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = ForgotPasswordForm()  # Reuse existing form
    
    if form.validate_on_submit():
        user = Member.query.filter_by(email=form.email.data, is_active=True).first()
        
        if user:
            # Check if user has 2FA enabled
            mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
            if mfa_data and mfa_data.is_totp_enabled:
                token = _issue_auth_token(
                    member_id=user.id,
                    purpose=AuthTokenPurpose.MFA_RESET,
                    expires_in=timedelta(hours=1),
                    request_ip=request.remote_addr,
                )
                reset_url = url_for('auth.reset_2fa', token=token, _external=True)
                html = render_template(
                    'emails/2fa_reset.html',
                    display_name=user.display_name,
                    reset_url=reset_url,
                    valid_for='1 Stunde',
                )
                text = (
                    f"Hallo {user.display_name}\n\n"
                    "Du hast einen 2FA-Reset angefordert.\n"
                    f"Setze 2FA ueber diesen Link zurueck: {reset_url}\n\n"
                    "Der Link ist 1 Stunde gueltig."
                )
                MailService.send_async(
                    to=user.email,
                    subject='Gourmen 2FA zuruecksetzen',
                    html=html,
                    text=text,
                    tags={'type': '2fa_reset', 'member_id': str(user.id)},
                )
                
                # Log audit event
                SecurityService.log_audit_event(
                    AuditAction.REQUEST_2FA_RESET, 'member', user.id,
                    extra_data={'ip': request.remote_addr},
                    actor_id=user.id,
                )
                db.session.commit()
            else:
                # Don't reveal if 2FA is enabled or not
                pass
        
        flash('Wenn die Adresse existiert, wurde eine Mail versendet.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_2fa_reset.html', form=form)

@bp.route('/2fa/reset/<token>', methods=['GET', 'POST'])
def reset_2fa(token):
    """Reset 2FA with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.MFA_RESET)
    if token_error == "missing":
        flash('Ungültiger oder abgelaufener 2FA Reset-Link', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "used":
        flash('Dieser 2FA Reset-Link wurde bereits verwendet.', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "expired":
        flash('2FA Reset-Link ist abgelaufen', 'error')
        return redirect(url_for('auth.login'))

    user = Member.query.get(auth_token.member_id)
    if not user or not user.is_active:
        flash('Ungültiger 2FA Reset-Link', 'error')
        return redirect(url_for('auth.login'))
    
    # Disable 2FA
    mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
    if mfa_data:
        mfa_data.is_totp_enabled = False
        mfa_data.totp_secret_encrypted = None
        mfa_data.activated_at = None
        mfa_data.last_verified_at = None
        
        # Delete backup codes
        MFABackupCode.query.filter_by(member_id=user.id).delete()
        
    auth_token.used_at = datetime.utcnow()
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.RESET_2FA, 'member', user.id,
        extra_data={'ip': request.remote_addr},
        actor_id=user.id,
    )
    
    flash('2FA erfolgreich zurückgesetzt. Sie können sich jetzt anmelden und 2FA neu einrichten.', 'success')
    return redirect(url_for('auth.login'))


@bp.route('/activate/<token>', methods=['GET', 'POST'])
def activate(token):
    """Activate account via onboarding token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.ONBOARDING)
    if token_error == "missing":
        flash('Ungültiger oder abgelaufener Aktivierungs-Link', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "used":
        flash('Dieser Aktivierungs-Link wurde bereits verwendet.', 'error')
        return redirect(url_for('auth.login'))
    if token_error == "expired":
        flash('Aktivierungs-Link ist abgelaufen.', 'error')
        return redirect(url_for('auth.login'))

    user = Member.query.get(auth_token.member_id)
    if not user or not user.is_active:
        flash('Ungültiger Aktivierungs-Link', 'error')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        is_valid, message = SecurityService.validate_password_strength(form.new_password.data)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/reset_password.html', form=form, token=token)

        user.set_password(form.new_password.data)
        auth_token.used_at = datetime.utcnow()
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.USE_ONBOARDING_TOKEN,
            'member',
            user.id,
            extra_data={'ip': request.remote_addr},
            actor_id=user.id,
        )
        login_user(user, remember=False)
        flash('Account aktiviert. Willkommen bei Gourmen!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/reset_password.html', form=form, token=token)

# Remember this device for 2FA
@bp.route('/2fa/remember-device', methods=['POST'])
@login_required
def remember_device():
    """Remember this device for 2FA"""
    # Generate device token
    device_token = secrets.token_urlsafe(32)
    import time
    expires_at_timestamp = int(time.time()) + (36500 * 24 * 3600)  # ~100 years (effectively unlimited)
    
    # Store in session
    session['remembered_device'] = {
        'user_id': current_user.id,
        'device_token': device_token,
        'expires_at': expires_at_timestamp
    }
    
    flash('Dieses Gerät wird dauerhaft gemerkt. 2FA wird nur bei neuen Geräten erforderlich.', 'success')
    return redirect(url_for('dashboard.index')) 

@bp.route('/2fa/backup-codes')
@login_required
def backup_codes():
    """Show backup codes after 2FA enrollment"""
    # Generate new backup codes if they don't exist
    backup_codes = MFABackupCode.query.filter_by(member_id=current_user.id).all()
    if not backup_codes:
        # Generate new backup codes
        codes = SecurityService.generate_backup_codes()
        for code in codes:
            backup_code = MFABackupCode(
                member_id=current_user.id,
                code_hash=SecurityService.hash_backup_code(code)
            )
            db.session.add(backup_code)
        db.session.commit()
        
        # Return the plain codes for display
        return render_template('auth/backup_codes.html', backup_codes=codes)
    
    # If backup codes already exist, show a message
    flash('Backup-Codes wurden bereits generiert. Falls Sie sie verloren haben, können Sie 2FA deaktivieren und neu einrichten.', 'info')
    return redirect(url_for('member.profile')) 