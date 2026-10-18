"""Durable invitation issuance before mail, with explicit manual replacement."""
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import current_app, render_template, request, url_for

from backend.extensions import db
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.audit_event import AuditEvent, AuditAction
from backend.models.member import Member
from backend.services.mail import MailService
from backend.services.security import SecurityService


class OnboardingService:
    @staticmethod
    def latest(member_id):
        return AuthToken.query.filter_by(member_id=member_id, purpose=AuthTokenPurpose.ONBOARDING).order_by(
            AuthToken.id.desc()).first()

    @staticmethod
    def eligible(member, row):
        return bool(member.is_active and row and row.issued_generation
                    and row.issued_generation == member.auth_generation)

    @staticmethod
    def matches(member, row):
        """Unbound legacy invitations require a newly issued link."""
        return bool(member and member.is_active
                    and row.issued_generation == member.auth_generation
                    and row.recipient_email
                    and SecurityService.normalized_primary_email(row.recipient_email) == SecurityService.normalized_primary_email(member.email))

    @staticmethod
    def prepare(member, *, replace=False):
        """Caller holds the member lock on replacement and commits before deliver."""
        if replace:
            SecurityService.invalidate_password_links(member.id, purpose=AuthTokenPurpose.ONBOARDING)
        raw = secrets.token_urlsafe(32)
        row = AuthToken(member=member, token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                        purpose=AuthTokenPurpose.ONBOARDING,
                        expires_at=datetime.utcnow() + timedelta(days=7),
                        request_ip=request.remote_addr, recipient_email=member.email,
                        issued_generation=member.auth_generation, delivery_status='pending')
        db.session.add(row)
        return raw, row

    @staticmethod
    def deliver(token_id, raw, actor_id, *, created=False):
        """Use the committed snapshot; never retry a transport call automatically."""
        row = db.session.get(AuthToken, token_id, populate_existing=True)
        if not row or row.purpose != AuthTokenPurpose.ONBOARDING or not row.issued_generation:
            db.session.rollback()
            return 'obsolete'
        if row.delivery_status != 'pending':
            status = row.delivery_status
            db.session.rollback()
            return status
        member = db.session.get(Member, row.member_id, populate_existing=True)
        if not member:
            db.session.rollback()
            return 'obsolete'
        member_id = member.id
        email, name = row.recipient_email, member.display_name
        valid = (row.delivery_status == 'pending' and member.is_active
                 and OnboardingService.matches(member, row) and row.used_at is None
                 and row.expires_at > datetime.utcnow()
                 and row.token_hash == hashlib.sha256(raw.encode()).hexdigest())
        # No database lock/transaction is kept open across network transport.
        db.session.rollback()
        status = 'obsolete'
        if valid:
            try:
                activation_url = url_for('auth.activate', token=raw, _external=True)
                html = render_template('emails/onboarding.html', display_name=name,
                                       activation_url=activation_url, valid_for='7 Tage')
                result = MailService.send(
                    to=email, subject='Willkommen bei Gourmen - Account aktivieren', html=html,
                    text=f'Hallo {name}\n\nAktiviere deinen Account hier: {activation_url}\n\n'
                         'Der Link ist 7 Tage gültig.',
                    tags={'type': 'onboarding', 'member_id': str(member_id)},
                )
                status = 'accepted' if result.get('success') else 'unconfirmed'
            except Exception:
                current_app.logger.warning('Onboarding mail result unconfirmed')
                status = 'unconfirmed'
        try:
            AuthToken.query.filter_by(id=token_id, delivery_status='pending').update(
                {'delivery_status': status}, synchronize_session=False)
            if created:
                db.session.add(AuditEvent(actor_id=actor_id, action=AuditAction.ADMIN_CREATE_MEMBER,
                                          entity='member', entity_id=member_id, ip=request.remote_addr))
            db.session.add(AuditEvent(actor_id=actor_id, action=AuditAction.SEND_ONBOARDING_MAIL,
                                     entity='member', entity_id=member_id, ip=request.remote_addr,
                                     extra_json={'status': status, 'token_id': token_id}))
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.warning('Onboarding result could not be persisted')
            return 'pending'
        return status
