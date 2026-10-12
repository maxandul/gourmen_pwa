"""Durable, address-bound Shared Drive membership work."""
from datetime import datetime

from backend.extensions import db


class DriveAccessTask(db.Model):
    __tablename__ = 'drive_access_tasks'
    __table_args__ = (
        db.CheckConstraint("action IN ('revoke', 'invite')", name='ck_drive_access_action'),
        db.CheckConstraint("status IN ('pending', 'failed', 'done', 'cancelled')",
                           name='ck_drive_access_status'),
        db.Index('ix_drive_access_member_status', 'member_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'),
                          nullable=False)
    email = db.Column(db.String(254), nullable=False)
    drive_id = db.Column(db.String(100))
    action = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    error_code = db.Column(db.String(40))
    last_attempt_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    member = db.relationship('Member')
