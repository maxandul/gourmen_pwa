"""Immutable application-level evidence of explicit settlement corrections."""
from datetime import datetime
from backend.extensions import db


class BillBroCorrection(db.Model):
    __tablename__ = 'billbro_corrections'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    reason = db.Column(db.String(1000), nullable=False)
    request_hash = db.Column(db.String(64), nullable=False, unique=True)
    before_json = db.Column(db.JSON, nullable=False)
    after_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actor = db.relationship('Member', foreign_keys=[actor_id])
