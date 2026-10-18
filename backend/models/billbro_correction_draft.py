"""Retained proposals; saving a draft does not change any settlement."""
from datetime import datetime
from backend.extensions import db


class BillBroCorrectionDraft(db.Model):
    __tablename__ = 'billbro_correction_drafts'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    request_hash = db.Column(db.String(64), nullable=False, unique=True)
    before_json = db.Column(db.JSON, nullable=False)
    proposal_json = db.Column(db.JSON, nullable=False)
    preview_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(16), default='pending', nullable=False)
    status_reason = db.Column(db.String(1000))
    status_actor_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'))
    status_at = db.Column(db.DateTime)
    actor = db.relationship('Member', foreign_keys=[actor_id])
    status_actor = db.relationship('Member', foreign_keys=[status_actor_id])
    __table_args__ = (
        db.CheckConstraint("status IN ('pending','superseded','withdrawn','applied')", name='ck_billbro_draft_status'),
        db.Index('ix_billbro_drafts_event', 'event_id'))

    @property
    def status_label(self):
        return {'pending': 'Entwurf, noch nicht wirksam', 'superseded': 'Durch neueren Entwurf ersetzt',
                'withdrawn': 'Zurückgezogen', 'applied': 'Finanziell bestätigt'}[self.status]
