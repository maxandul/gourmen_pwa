from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from backend.extensions import db, limiter
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService, AuditAction
from backend.extensions import csrf
import secrets
from datetime import datetime, timedelta

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
            login_user(user, remember=form.remember_me.data)
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.LOGIN, 'member', user.id,
                extra_data={'ip': request.remote_addr}
            )
            
            # Check if 2FA is enabled
            mfa_data = MemberMFA.query.filter_by(member_id=user.id).first()
            if mfa_data and mfa_data.is_totp_enabled:
                session['pending_2fa_user_id'] = user.id
                return redirect(url_for('auth.verify_2fa'))
            
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
            login_user(user)
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
            login_user(user)
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
    """Enroll 2FA"""
    mfa_data = MemberMFA.query.filter_by(member_id=current_user.id).first()
    if not mfa_data:
        mfa_data = MemberMFA(member_id=current_user.id)
        db.session.add(mfa_data)
        db.session.commit()
    
    if mfa_data.is_totp_enabled:
        flash('2FA ist bereits aktiviert', 'info')
        return redirect(url_for('account.profile'))
    
    # Generate new secret
    secret = SecurityService.generate_totp_secret()
    totp_uri = SecurityService.generate_totp_uri(current_user.email, secret)
    
    totp_form = TOTPForm()
    if totp_form.validate_on_submit():
        if SecurityService.verify_totp(secret, totp_form.token.data):
            # Enable 2FA
            mfa_data.totp_secret_encrypted = SecurityService.encrypt_json(secret)
            mfa_data.is_totp_enabled = True
            mfa_data.activated_at = datetime.utcnow()
            mfa_data.last_verified_at = datetime.utcnow()
            
            # Generate backup codes
            backup_codes = SecurityService.generate_backup_codes()
            for code in backup_codes:
                backup_code = MFABackupCode(
                    member_id=current_user.id,
                    code_hash=SecurityService.hash_backup_code(code)
                )
                db.session.add(backup_code)
            
            db.session.commit()
            
            SecurityService.log_audit_event(AuditAction.ENABLE_MFA, 'member_mfa', current_user.id)
            
            flash('2FA erfolgreich aktiviert', 'success')
            return render_template('auth/backup_codes.html', backup_codes=backup_codes)
        else:
            flash('Ungültiger Code', 'error')
    
    return render_template('auth/enroll_2fa.html', secret=secret, totp_uri=totp_uri, form=totp_form)

@bp.route('/2fa/disable', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    """Disable 2FA"""
    mfa_data = MemberMFA.query.filter_by(member_id=current_user.id).first()
    if not mfa_data or not mfa_data.is_totp_enabled:
        flash('2FA ist nicht aktiviert', 'info')
        return redirect(url_for('account.profile'))
    
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
            return redirect(url_for('account.profile'))
        else:
            flash('Ungültiges Passwort', 'error')
    
    return render_template('auth/disable_2fa.html', form=step_up_form)

@bp.route('/step-up', methods=['GET', 'POST'])
@login_required
def step_up():
    """Step-up authentication"""
    # Get next page from URL parameters or form data
    next_page = request.args.get('next') or request.form.get('next')
    
    if SecurityService.check_step_up_access():
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard.index')
        return redirect(next_page)
    
    form = StepUpForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            SecurityService.grant_step_up_access()
            SecurityService.log_audit_event(AuditAction.LOGIN, 'member', current_user.id)
            
            # Ensure we redirect to the original requested page
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            else:
                return redirect(url_for('dashboard.index'))
        else:
            flash('Ungültiges Passwort', 'error')
    
    return render_template('auth/step_up.html', form=form, next=next_page)

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
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.CHANGE_PASSWORD, 'member', current_user.id,
            extra_data={'ip': request.remote_addr}
        )
        
        flash('Passwort erfolgreich geändert', 'success')
        return redirect(url_for('account.profile'))
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Forgot password - send reset link"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = Member.query.filter_by(email=form.email.data, is_active=True).first()
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Store token in session (in production, use database or Redis)
            session[f'reset_token_{token}'] = {
                'user_id': user.id,
                'expires_at': expires_at.isoformat()
            }
            
            # Generate reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # In production, send email here
            # For now, we'll just show the URL (remove this in production!)
            flash(f'Reset-Link generiert: {reset_url}', 'info')
            
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.REQUEST_PASSWORD_RESET, 'member', user.id,
                extra_data={'ip': request.remote_addr}
            )
        else:
            # Don't reveal if email exists or not
            pass
        
        # Always show success message to prevent email enumeration
        flash('Falls die E-Mail-Adresse existiert, wurde ein Reset-Link gesendet', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Verify token
    token_data = session.get(f'reset_token_{token}')
    if not token_data:
        flash('Ungültiger oder abgelaufener Reset-Link', 'error')
        return redirect(url_for('auth.login'))
    
    # Check expiration
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.utcnow() > expires_at:
        session.pop(f'reset_token_{token}', None)
        flash('Reset-Link ist abgelaufen', 'error')
        return redirect(url_for('auth.login'))
    
    user = Member.query.get(token_data['user_id'])
    if not user or not user.is_active:
        session.pop(f'reset_token_{token}', None)
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
        db.session.commit()
        
        # Remove token
        session.pop(f'reset_token_{token}', None)
        
        # Log audit event
        SecurityService.log_audit_event(
            AuditAction.RESET_PASSWORD, 'member', user.id,
            extra_data={'ip': request.remote_addr}
        )
        
        flash('Passwort erfolgreich zurückgesetzt. Sie können sich jetzt anmelden.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

# Import here to avoid circular imports
from datetime import datetime 