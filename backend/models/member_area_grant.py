"""Explicit scoped grants with durable revocation history."""
from datetime import datetime
from backend.extensions import db


class MemberAreaGrant(db.Model):
    __tablename__ = 'member_area_grants'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False, index=True)
    scope = db.Column(db.String(64), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    granted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    revoked_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'))
    revoked_at = db.Column(db.DateTime)
    grantor = db.relationship('Member', foreign_keys=[granted_by])
    revoker = db.relationship('Member', foreign_keys=[revoked_by])
    __table_args__ = (db.Index('uq_member_area_grant_active', 'member_id', 'scope', unique=True,
                              sqlite_where=revoked_at.is_(None), postgresql_where=revoked_at.is_(None)),)
