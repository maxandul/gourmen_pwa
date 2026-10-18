"""Hosting-only recovery; never exposed as a web route."""
from datetime import datetime

from backend.extensions import db
from backend.models.audit_event import AuditAction, AuditEvent
from backend.models.auth_token import AuthToken
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.services.security import SecurityService


class AdminRecoveryService:
    @staticmethod
    def recover(member_id, expected_generation, password, operator, reason, *, reset_mfa=False):
        """Stage one recovery transaction. Caller commits or rolls back including audit."""
        valid, message = SecurityService.validate_password_strength(password)
        if not valid:
            raise ValueError(message)
        if not operator.strip() or not reason.strip() or len(operator) > 200 or len(reason) > 500:
            raise ValueError('Operator und Grund sind erforderlich (maximal 200/500 Zeichen).')
        member = SecurityService.lock_credential_member(member_id)
        if not member or not member.is_active or not member.is_admin():
            raise ValueError('Ziel ist kein aktiver Systemadmin.')
        if member.auth_generation != expected_generation:
            raise ValueError('Kontozustand wurde zwischenzeitlich geändert. Neu prüfen.')
        if member.check_password(password):
            raise ValueError('Ein neues Passwort ist erforderlich.')
        member.set_password(password)
        AuthToken.query.filter_by(member_id=member_id, used_at=None).update(
            {'used_at': datetime.utcnow()}, synchronize_session='fetch')
        if reset_mfa:
            mfa = MemberMFA.query.filter_by(member_id=member_id).first()
            if mfa:
                mfa.is_totp_enabled = False
                mfa.totp_secret_encrypted = None
                mfa.activated_at = None
                mfa.last_verified_at = None
            MFABackupCode.query.filter_by(member_id=member_id, revoked_at=None).update(
                {'revoked_at': datetime.utcnow()}, synchronize_session='fetch')
        actions = [AuditAction.ADMIN_RESET_PASSWORD]
        if reset_mfa:
            actions.append(AuditAction.ADMIN_RESET_2FA)
        for action in actions:
            db.session.add(AuditEvent(actor_id=member_id, action=action, entity='member',
                entity_id=member_id, extra_json={'source': 'hosting_cli',
                    'operator_reference': operator.strip(), 'reason': reason.strip(),
                    'reset_mfa': reset_mfa, 'actor_basis': 'hosting_identity_external'}))
