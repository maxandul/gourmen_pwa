from backend.services.primary_email import PrimaryEmailService
from backend.services.recovery_links import RecoveryLinkService
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort, make_response
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
from backend.services.password_change import PasswordChangeService
from backend.services.authentication import AuthenticationService
from backend.services.action_confirmation import ActionConfirmationService
from backend.services.onboarding import OnboardingService

bp = Blueprint('auth', __name__)


@bp.app_context_processor
def action_confirmation_context():
    return {'action_confirmation_token': ActionConfirmationService.issue}


@bp.after_app_request
def protect_confirmation_responses(response):
    if request.endpoint in {'auth.change_password', 'auth.enroll_2fa', 'auth.disable_2fa',
                            'admin.reset_member_password', 'admin.reset_member_2fa',
                            'admin.edit_member', 'admin.create_member', 'admin.onboarding',
                            'auth.reset_password', 'auth.reset_2fa', 'auth.activate'}:
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
    return response


class LoginForm(FlaskForm):
    email = StringField('E-Mail', filters=[PrimaryEmailService.normalize], validators=[DataRequired(), Email()])
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
    email = StringField('E-Mail', filters=[PrimaryEmailService.normalize], validators=[DataRequired(), Email()])
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


class ConfirmMFAResetForm(FlaskForm):
    confirm = BooleanField(
        'Ich möchte die Zwei-Faktor-Anmeldung zurücksetzen.',
        validators=[DataRequired(message='Bitte bestätige das Zurücksetzen.')],
    )
    submit = SubmitField('2FA jetzt zurücksetzen')


def _hash_auth_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_auth_token(member_id: int, purpose: AuthTokenPurpose, expires_in: timedelta, request_ip: str | None):
    if purpose in RecoveryLinkService.PURPOSES:
        raw, _ = RecoveryLinkService.prepare(member_id,purpose,expires_in,request_ip)
        return raw
    if purpose == AuthTokenPurpose.ONBOARDING:
        SecurityService.lock_credential_member(member_id)
        SecurityService.invalidate_password_links(member_id,purpose=purpose)
    member = db.session.get(Member, member_id)
    token = secrets.token_urlsafe(32)
    token_hash = _hash_auth_token(token)
    token_row = AuthToken(
        member_id=member_id,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=datetime.utcnow() + expires_in,
        request_ip=request_ip,
        recipient_email=member.email if member else None,
        issued_generation=member.auth_generation if member and purpose == AuthTokenPurpose.ONBOARDING else None,
    )
    db.session.add(token_row)
    return token


def _resolve_auth_token(raw_token: str, purpose: AuthTokenPurpose, *, lock=False):
    token_hash = _hash_auth_token(raw_token)
    auth_token = AuthToken.query.filter_by(token_hash=token_hash, purpose=purpose).first()
    if auth_token and lock:
        user = SecurityService.lock_credential_member(auth_token.member_id)
        if not user or not user.is_active:
            return None, "missing"
        auth_token = AuthToken.query.filter_by(token_hash=token_hash, purpose=purpose).populate_existing().first()
    if not auth_token:
        return None, "missing"
    if auth_token.used_at is not None:
        return None, "used"
    if auth_token.expires_at < datetime.utcnow():
        return None, "expired"
    member = db.session.get(Member, auth_token.member_id)
    if not member or not member.is_active:
        return None, "missing"
    if purpose in (AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.MFA_RESET, AuthTokenPurpose.ONBOARDING):
        if not auth_token.recipient_email or SecurityService.normalized_primary_email(auth_token.recipient_email) != SecurityService.normalized_primary_email(member.email):
            return None, "missing"
    if purpose == AuthTokenPurpose.ONBOARDING and not OnboardingService.matches(member, auth_token):
        return None, "missing"
    return auth_token, None

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    """Login page"""
    # Visiting/retrying login abandons any previous password/MFA attempt.
    session.pop('pending_2fa_user_id', None)
    session.pop('pending_2fa_next', None)
    session.pop('pending_2fa_generation', None)
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = PrimaryEmailService.find_active(form.email.data)
        if user:
            user = SecurityService.lock_credential_member(user.id)
        
        if user and user.is_active and user.check_password(form.password.data):
            # Check if 2FA is enabled
            mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
            if mfa_data and mfa_data.is_totp_enabled:
                # Check if device is remembered
                if AuthenticationService.trusted_device(user):
                    login_user(user, remember=True)
                    SecurityService.log_audit_event(
                        AuditAction.LOGIN, 'member', user.id,
                        extra_data={'ip': request.remote_addr, 'remembered_device': True}
                    )
                    next_page = SecurityService.local_return_target(request.args.get('next'))
                    return redirect(PasswordChangeService.after_login_target(user, next_page))
                
                # Device not remembered, require 2FA
                session['pending_2fa_user_id'] = user.id
                session['pending_2fa_generation'] = user.auth_generation
                session['pending_2fa_next'] = SecurityService.local_return_target(request.args.get('next'))
                return redirect(url_for('auth.verify_2fa'))
            
            # No 2FA enabled, login normally
            login_user(user, remember=form.remember_me.data)
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.LOGIN, 'member', user.id,
                extra_data={'ip': request.remote_addr}
            )
            
            next_page = SecurityService.local_return_target(request.args.get('next'))
            return redirect(PasswordChangeService.after_login_target(user, next_page))
        else:
            flash('Ungültige E-Mail oder Passwort', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Du wurdest erfolgreich abgemeldet', 'success')
    return redirect(url_for('public.landing'))

@bp.route('/2fa/verify', methods=['GET', 'POST'])
def verify_2fa():
    """2FA verification"""
    # Capture before login_user clears authentication intermediates.
    return_target = SecurityService.local_return_target(session.get('pending_2fa_next'))
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        session.pop('pending_2fa_next', None)
        return redirect(url_for('auth.login'))
    
    user = SecurityService.lock_credential_member(user_id)
    generation = session.get('pending_2fa_generation')
    if not user or not user.is_active or generation != user.auth_generation:
        SecurityService.clear_auth_transients(current_app)
        return redirect(url_for('auth.login'))
    
    mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
    if not mfa_data or not mfa_data.is_totp_enabled:
        SecurityService.clear_auth_transients(current_app)
        return redirect(url_for('auth.login'))
    
    totp_form = TOTPForm()
    backup_form = BackupCodeForm()
    
    if totp_form.validate_on_submit():
        # Verify TOTP
        secret = SecurityService.decrypt_json(mfa_data.totp_secret_encrypted)
        if SecurityService.verify_totp(secret, totp_form.token.data):
            remember_device = bool(request.form.get('remember_device'))
            mfa_data.last_verified_at = datetime.utcnow()
            db.session.commit()
            if not AuthenticationService.complete_login(user, generation, remember=remember_device):
                return redirect(url_for('auth.login'))
            if remember_device:
                AuthenticationService.issue_device_trust(user)
            
            SecurityService.log_audit_event(AuditAction.LOGIN, 'member', user.id)
            
            return redirect(PasswordChangeService.after_login_target(user, return_target))
        else:
            flash('Ungültiger Code', 'error')
    
    elif backup_form.validate_on_submit():
        # Verify backup code
        backup_code = backup_form.backup_code.data.upper()
        backup_code_id = SecurityService.consume_backup_code(user.id, backup_code)
        
        if backup_code_id is not None:
            session.pop('pending_2fa_user_id', None)
            if not AuthenticationService.complete_login(user, generation, remember=True):
                return redirect(url_for('auth.login'))
            
            SecurityService.log_audit_event(
                AuditAction.USE_BACKUP_CODE, 'member', user.id,
                extra_data={'backup_code_id': backup_code_id}
            )
            
            return redirect(PasswordChangeService.after_login_target(user, return_target))
        else:
            flash('Ungültiger Backup-Code', 'error')
    
    return render_template('auth/verify_2fa.html', totp_form=totp_form, backup_form=backup_form)

@bp.route('/2fa/enroll', methods=['GET', 'POST'])
@login_required
def enroll_2fa():
    """Enroll 2FA - Simplified version"""
    mfa_data = MemberMFA.query.filter_by(member_id=current_user.id).first()
    if mfa_data and mfa_data.is_totp_enabled:
        flash('2FA ist bereits aktiviert', 'info')
        return redirect(url_for('member.profile'))
    
    # Generate new secret only if not already in session
    if '2fa_secret' not in session:
        secret = SecurityService.generate_totp_secret()
        session['2fa_secret'] = secret
        current_app.logger.info('MFA enrollment started')
    else:
        secret = session['2fa_secret']
        current_app.logger.info('MFA enrollment resumed')
    
    totp_form = TOTPForm()
    
    if (totp_form.validate_on_submit()
            and ActionConfirmationService.check('mfa_enroll', current_user, request.form.get('action_password'))):
        if SecurityService.verify_totp(secret, totp_form.token.data):
            user = SecurityService.lock_credential_member(current_user.id)
            if not user or not user.is_active:
                abort(403)
            mfa_data = MemberMFA.query.filter_by(member_id=user.id).populate_existing().first()
            if mfa_data and mfa_data.is_totp_enabled:
                flash('2FA ist bereits aktiviert', 'info')
                return redirect(url_for('member.profile'))
            if not mfa_data:
                mfa_data = MemberMFA(member_id=user.id)
                db.session.add(mfa_data)
            # Enable 2FA
            mfa_data.totp_secret_encrypted = SecurityService.encrypt_json(secret)
            mfa_data.is_totp_enabled = True
            mfa_data.activated_at = datetime.utcnow()
            mfa_data.last_verified_at = datetime.utcnow()
            user.rotate_auth_generation()
            generation = user.auth_generation
            
            try:
                codes = SecurityService.replace_backup_codes(user.id)
                SecurityService.invalidate_mfa_reset_links(user.id)
                # Render before commit so rendering failures cannot strand activation.
                response = make_response(render_template('auth/backup_codes.html', backup_codes=codes))
                response.headers['Cache-Control'] = 'no-store'
                response.headers['Referrer-Policy'] = 'no-referrer'
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            session.pop('2fa_secret', None)
            if not AuthenticationService.retain_current(user, generation):
                return redirect(url_for('auth.login'))
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.ENABLE_2FA, 'member', current_user.id,
                extra_data={'ip': request.remote_addr}
            )
            
            flash('2FA erfolgreich aktiviert!', 'success')
            return response
        else:
            flash('Ungültiger Code. Bitte versuche es erneut.', 'error')
    
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
    if (step_up_form.validate_on_submit()
            and ActionConfirmationService.check('mfa_disable', current_user, step_up_form.password.data)):
        user = SecurityService.lock_credential_member(current_user.id)
        if not user or not user.is_active:
            abort(403)
        mfa_data = MemberMFA.query.filter_by(member_id=user.id).populate_existing().first()
        if not mfa_data or not mfa_data.is_totp_enabled:
            return redirect(url_for('member.profile'))
        if current_user.check_password(step_up_form.password.data):
            # Disable 2FA
            mfa_data.is_totp_enabled = False
            mfa_data.activated_at = None
            mfa_data.last_verified_at = None
            
            # Revoke all backup codes
            backup_codes = MFABackupCode.query.filter_by(member_id=current_user.id).all()
            for code in backup_codes:
                code.revoked_at = datetime.utcnow()
            
            SecurityService.invalidate_mfa_reset_links(current_user.id)
            user.rotate_auth_generation()
            generation = user.auth_generation
            db.session.commit()
            if not AuthenticationService.retain_current(user, generation):
                return redirect(url_for('auth.login'))
            
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
    # Validate every source, including values saved by older app versions.
    next_candidates = (
        request.args.get('next'),
        request.form.get('next'),
        request.form.get('next_url'),
        session.pop('step_up_next', None),
    )
    next_page = next((target for candidate in next_candidates
                      if (target := SecurityService.local_return_target(candidate))), None)
    if next_page:
        session['step_up_next'] = next_page

    # Form data and return URLs can contain passwords or tokens.
    current_app.logger.info('Step-up authentication requested')

    if SecurityService.check_step_up_access():
        session.pop('step_up_next', None)
        return redirect(next_page or url_for('dashboard.index'))

    form = StepUpForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            SecurityService.grant_step_up_access()
            SecurityService.log_audit_event(AuditAction.LOGIN, 'member', current_user.id)
            current_app.logger.info('Step-up authentication succeeded')
            session.pop('step_up_next', None)
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Ungültiges Passwort', 'error')

    return render_template('auth/step_up.html', form=form, next=next_page)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged in user"""
    form = ChangePasswordForm()
    
    if (form.validate_on_submit()
            and ActionConfirmationService.check('password_change', current_user, form.current_password.data)):
        user = SecurityService.lock_credential_member(current_user.id)
        if not user or not user.is_active:
            abort(403)
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
        trust = AuthenticationService.trusted_device(user)
        current_user.set_password(form.new_password.data)
        generation = user.auth_generation
        SecurityService.invalidate_password_links(current_user.id)
        db.session.commit()
        if not AuthenticationService.retain_current(user, generation, trust=trust):
            return redirect(url_for('auth.login'))
        
        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.CHANGE_PASSWORD, 'member', current_user.id,
            extra_data={'ip': request.remote_addr}
        )
        
        flash('Passwort erfolgreich geändert', 'success')
        
        # Redirect based on whether this was first login or normal password change
        if was_first_login:
            return redirect(PasswordChangeService.consume_target(current_user.id)
                            or url_for('dashboard.index'))
        else:
            session.pop('password_change_return', None)
            return redirect(url_for('member.profile'))
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=['POST'])
def forgot_password():
    """Request a durable, address-bound reset without account enumeration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = PrimaryEmailService.find_active(form.email.data)
        if user:
            RecoveryLinkService.request(user.id, AuthTokenPurpose.PASSWORD_RESET, request.remote_addr)
        flash('Wenn die Adresse fuer eine Wiederherstellung verwendet werden kann, erhaeltst du einen Link. Bitte pruefe auch den Spamordner.', 'success')
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
        auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.PASSWORD_RESET, lock=True)
        if token_error:
            flash('Dieser Link ist nicht mehr gültig. Bitte fordere einen neuen an.', 'error')
            return redirect(url_for('auth.login'))
        user.set_password(form.new_password.data)
        SecurityService.invalidate_password_links(user.id)
        db.session.commit()

        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.RESET_PASSWORD, 'member', user.id,
            extra_data={'ip': request.remote_addr},
            actor_id=user.id,
        )
        
        flash('Passwort erfolgreich zurückgesetzt. Du kannst dich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

# 2FA Reset via Email
@bp.route('/2fa/reset-request', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def request_2fa_reset():
    """Request a durable reset with the same neutral public response."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = PrimaryEmailService.find_active(form.email.data)
        if user:
            RecoveryLinkService.request(user.id, AuthTokenPurpose.MFA_RESET, request.remote_addr)
        flash('Wenn die Adresse fuer eine Wiederherstellung verwendet werden kann, erhaeltst du einen Link. Bitte pruefe auch den Spamordner.', 'success')
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
    
    form = ConfirmMFAResetForm()
    if not form.validate_on_submit():
        response = current_app.make_response(render_template('auth/reset_2fa.html', form=form))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.MFA_RESET, lock=True)
    if token_error:
        flash('Dieser Link ist nicht mehr gültig. Bitte fordere einen neuen an.', 'error')
        return redirect(url_for('auth.login'))

    # Disable 2FA only after explicit, CSRF-protected confirmation.
    mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
    if mfa_data:
        mfa_data.is_totp_enabled = False
        mfa_data.totp_secret_encrypted = None
        mfa_data.activated_at = None
        mfa_data.last_verified_at = None
        
        # Delete backup codes
        MFABackupCode.query.filter_by(member_id=user.id).delete()
        
    SecurityService.invalidate_mfa_reset_links(user.id)
    user.rotate_auth_generation()
    db.session.commit()
    
    # Log audit event
    SecurityService.log_audit_event(
        AuditAction.RESET_2FA, 'member', user.id,
        extra_data={'ip': request.remote_addr},
        actor_id=user.id,
    )
    
    flash('2FA erfolgreich zurückgesetzt. Du kannst dich jetzt anmelden und 2FA neu einrichten.', 'success')
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

        auth_token, token_error = _resolve_auth_token(token, AuthTokenPurpose.ONBOARDING, lock=True)
        if token_error:
            flash('Dieser Link ist nicht mehr gültig. Bitte fordere einen neuen an.', 'error')
            return redirect(url_for('auth.login'))
        user.set_password(form.new_password.data)
        generation = user.auth_generation
        SecurityService.invalidate_password_links(user.id)
        db.session.commit()

        SecurityService.log_audit_event(
            AuditAction.USE_ONBOARDING_TOKEN,
            'member',
            user.id,
            extra_data={'ip': request.remote_addr},
            actor_id=user.id,
        )
        # Activation must not bypass an existing second factor.
        mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
        if mfa_data and mfa_data.is_totp_enabled:
            return redirect(url_for('auth.login'))
        if not AuthenticationService.complete_login(user, generation, remember=False):
            return redirect(url_for('auth.login'))
        flash('Account aktiviert. Willkommen bei Gourmen!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/reset_password.html', form=form, token=token)

# Remember this device for 2FA
@bp.route('/2fa/remember-device', methods=['POST'])
@login_required
def remember_device():
    """Legacy entry cannot mint trust from a login session alone."""
    abort(403)

@bp.route('/2fa/backup-codes')
@login_required
def backup_codes():
    """Legacy entry: codes are only issued in the confirmed enrollment POST."""
    flash('Backup-Codes werden nur nach der 2FA-Einrichtung angezeigt. Falls du sie verloren hast, kannst du 2FA deaktivieren und neu einrichten.', 'info')
    return redirect(url_for('member.profile'))
