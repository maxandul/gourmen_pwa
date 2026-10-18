"""Durable reset issuance and one transport attempt per token, without raw-token storage."""
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import current_app, request, render_template, url_for
from backend.extensions import db
from backend.models.auth_token import AuthToken, AuthTokenPurpose as Purpose
from backend.models.audit_event import AuditEvent, AuditAction
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.services.security import SecurityService
from backend.services.primary_email import PrimaryEmailService
from backend.services.mail import MailService


class RecoveryLinkService:
    PURPOSES = (Purpose.PASSWORD_RESET, Purpose.MFA_RESET)

    @classmethod
    def prepare(cls, member_id, purpose, expires_in, request_ip, *, require_factor=False):
        if purpose not in cls.PURPOSES:
            raise ValueError('Unsupported recovery purpose')
        member = SecurityService.lock_credential_member(member_id)
        if not member or not member.is_active:
            return None, None
        if require_factor and purpose == Purpose.MFA_RESET:
            factor = MemberMFA.query.filter_by(member_id=member_id).populate_existing().first()
            if not factor or not factor.is_totp_enabled:
                return None, None
        if purpose == Purpose.PASSWORD_RESET:
            SecurityService.invalidate_password_links(member_id, purpose=purpose)
        else:
            SecurityService.invalidate_mfa_reset_links(member_id)
        raw = secrets.token_urlsafe(32)
        row = AuthToken(member_id=member_id, purpose=purpose,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(), expires_at=datetime.utcnow()+expires_in,
            request_ip=request_ip, recipient_email=PrimaryEmailService.normalize(member.email), delivery_status='pending')
        db.session.add(row)
        return raw, row

    @classmethod
    def request(cls, member_id, purpose, request_ip):
        try:
            raw, row = cls.prepare(member_id,purpose,timedelta(hours=1),request_ip,require_factor=True)
            if not row:
                db.session.rollback()
                return 'obsolete'
            db.session.flush()
            db.session.add(AuditEvent(actor_id=member_id,
                action=AuditAction.REQUEST_PASSWORD_RESET if purpose==Purpose.PASSWORD_RESET else AuditAction.REQUEST_2FA_RESET,
                entity='member',entity_id=member_id,ip=request_ip,extra_json={'token_id':row.id}))
            token_id=row.id
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.warning('Recovery link could not be persisted; no mail attempted')
            return 'unconfirmed'
        return cls.deliver(token_id,raw)

    @classmethod
    def deliver(cls, token_id, raw):
        row=db.session.get(AuthToken,token_id)
        if not row or row.purpose not in cls.PURPOSES:
            return 'obsolete'
        member=SecurityService.lock_credential_member(row.member_id)
        db.session.refresh(row)
        if row.delivery_status != 'pending':
            status=row.delivery_status or 'obsolete'
            db.session.rollback()
            return status
        valid=bool(member and member.is_active and row.used_at is None and row.expires_at>datetime.utcnow()
            and row.recipient_email and PrimaryEmailService.normalize(row.recipient_email)==PrimaryEmailService.normalize(member.email)
            and row.token_hash==hashlib.sha256(raw.encode()).hexdigest())
        email,name,purpose,member_id=row.recipient_email,member.display_name if member else '',row.purpose,row.member_id
        row.delivery_status='sending' if valid else 'obsolete'
        try:
            db.session.commit()  # Commit the send claim before releasing to transport.
        except Exception:
            db.session.rollback()
            current_app.logger.warning('Recovery send claim could not be persisted; no mail attempted')
            return 'pending'
        if not valid:
            return 'obsolete'
        status='unconfirmed'
        try:
            password=purpose==Purpose.PASSWORD_RESET
            link=url_for('auth.reset_password' if password else 'auth.reset_2fa',token=raw,_external=True)
            html=render_template('emails/password_reset.html' if password else 'emails/2fa_reset.html',
                display_name=name,reset_url=link,valid_for='1 Stunde')
            result=MailService.send(to=email,subject='Gourmen Passwort zuruecksetzen' if password else 'Gourmen 2FA zuruecksetzen',
                html=html,text=f'Hallo {name}\n\nDein angeforderter Wiederherstellungslink: {link}\n\nDer Link ist 1 Stunde gueltig.',
                tags={'type':'password_reset' if password else '2fa_reset','member_id':str(member_id)})
            status='accepted' if result.get('success') is True and result.get('message_id') and not result.get('error') else 'unconfirmed'
        except Exception:
            current_app.logger.warning('Recovery mail result unconfirmed')
        try:
            AuthToken.query.filter_by(id=token_id,delivery_status='sending').update({'delivery_status':status},synchronize_session=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.warning('Recovery result could not be persisted')
            return 'sending'
        return status
