"""Durable intent and outcome for a single Drive trash operation."""
from datetime import datetime
from backend.extensions import db


class DocumentDeletionRequest(db.Model):
    __tablename__ = 'document_deletion_requests'
    drive_file_id = db.Column(db.String(100), primary_key=True)
    document_id = db.Column(db.Integer, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(32), nullable=False, default='pending')
