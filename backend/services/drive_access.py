"""Transactional outbox for Shared Drive membership changes."""
from datetime import datetime

from flask import current_app

from backend.extensions import db
from backend.models.audit_event import AuditAction, AuditEvent
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.drive_access_task import DriveAccessTask
from backend.models.member import Member
from backend.services.drive_storage import DriveStorageService


OPEN_STATUSES = ('pending', 'failed')


class DriveAccessService:
    @staticmethod
    def queue_invite(member):
        """Caller holds the member lock and owns the verification transaction."""
        db.session.add(DriveAccessTask(
            member_id=member.id, email=member.google_email.lower(), action='invite',
            drive_id=current_app.config.get('GOOGLE_DRIVE_ID'),
        ))

    @staticmethod
    def queue_revocation(member):
        """Snapshot old scopes and cancel grants atomically with the local change."""
        invites = DriveAccessTask.query.filter_by(member_id=member.id, action='invite').all()
        targets = {(task.email, task.drive_id) for task in invites
                   if task.status != 'cancelled'}
        if member.google_email:
            targets.add((member.google_email.lower(), current_app.config.get('GOOGLE_DRIVE_ID')))
        for task in invites:
            if task.status in OPEN_STATUSES:
                task.status = 'cancelled'
                task.completed_at = datetime.utcnow()
        for email, drive_id in sorted(targets, key=lambda target: (target[0], target[1] or '')):
            existing = DriveAccessTask.query.filter_by(
                member_id=member.id, email=email, drive_id=drive_id, action='revoke',
            ).filter(DriveAccessTask.status.in_(OPEN_STATUSES)).first()
            if existing is None:
                db.session.add(DriveAccessTask(member_id=member.id, email=email,
                                              drive_id=drive_id, action='revoke'))

    @classmethod
    def deactivate(cls, member):
        """Called before is_active changes, under the member lock; never commits."""
        cls.queue_revocation(member)
        member.google_email_verified = False
        member.google_email_verified_at = None
        AuthToken.query.filter_by(member_id=member.id,
                                  purpose=AuthTokenPurpose.GOOGLE_EMAIL_VERIFY,
                                  used_at=None).update({'used_at': datetime.utcnow()},
                                                       synchronize_session=False)

    @staticmethod
    def process_member(member_id, *, bind_missing_drive=False, actor_id=None):
        """Process committed work, one transaction per step; stop on any failure.

        All app lifecycle writers take this same member lock. External methods
        must not commit: the lock fences a late invite from address/deactivation
        changes until its result has been stored. A crash rolls back to open work.
        """
        try:
            while True:
                member = Member.query.filter_by(id=member_id).populate_existing().with_for_update().first()
                if member is None:
                    db.session.rollback()
                    return False
                tasks = DriveAccessTask.query.filter_by(member_id=member_id).filter(
                    DriveAccessTask.status.in_(OPEN_STATUSES),
                ).order_by(DriveAccessTask.id).populate_existing().all()
                if not tasks:
                    db.session.commit()
                    return True
                task = next((item for item in tasks if item.action == 'revoke'), tasks[0])
                if task.action == 'invite' and (
                    not member.is_active or not member.google_email_verified
                    or (member.google_email or '').lower() != task.email
                ):
                    task.status = 'cancelled'
                    task.completed_at = datetime.utcnow()
                    db.session.commit()
                    continue
                if (not task.drive_id and bind_missing_drive
                        and current_app.config.get('GOOGLE_DRIVE_ID')):
                    task.drive_id = current_app.config.get('GOOGLE_DRIVE_ID')
                    # Persist the explicitly selected scope before an external effect.
                    db.session.commit()
                    continue
                task.attempts += 1
                task.last_attempt_at = datetime.utcnow()
                error = None
                if not current_app.config.get('DRIVE_FEATURE_ENABLED'):
                    error = 'feature_disabled'
                elif not task.drive_id:
                    error = 'missing_drive'
                else:
                    try:
                        DriveStorageService.apply_membership(task.drive_id, task.email, task.action)
                    except Exception:
                        # API exceptions can contain credentials, addresses and response bodies.
                        error = 'drive_error'
                task.error_code = error
                task.status = 'failed' if error else 'done'
                if not error:
                    task.completed_at = datetime.utcnow()
                action = (AuditAction.DRIVE_MEMBERSHIP_FAILED if error else
                          AuditAction.DRIVE_MEMBERSHIP_REMOVED if task.action == 'revoke' else
                          AuditAction.DRIVE_MEMBERSHIP_ADDED)
                db.session.add(AuditEvent(actor_id=actor_id or member_id, entity='member', entity_id=member_id,
                                          action=action, extra_json={'task_id': task.id,
                                                                    'error_code': error}))
                db.session.commit()
                if error:
                    return False
        except Exception:
            db.session.rollback()
            current_app.logger.warning('Drive-Aufgabe bleibt offen: Speicherung fehlgeschlagen')
            return False
