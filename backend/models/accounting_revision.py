"""Erhaltene Einreichungen, Entscheidungen und Berichtreferenzen."""
from datetime import datetime
from backend.extensions import db


class AccountingRevision(db.Model):
    __tablename__ = 'accounting_revisions'
    __table_args__ = (db.UniqueConstraint('fiscal_year_id', 'version', name='uq_revision_year_version'),)

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year_id = db.Column(db.Integer, db.ForeignKey('fiscal_years.id', ondelete='RESTRICT'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    snapshot = db.Column(db.JSON)  # NULL only for explicitly recorded legacy withdrawal.
    submitted_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    state = db.Column(db.String(20), nullable=False, default='in_review')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'))
    reviewer_name = db.Column(db.String(255))
    approved_at = db.Column(db.DateTime)
    admin_substitute = db.Column(db.Boolean, nullable=False, default=False)
    report_drive_id = db.Column(db.String(255))
    withdrawn_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'))
    withdrawn_at = db.Column(db.DateTime)
    withdrawal_reason = db.Column(db.Text)

    fiscal_year = db.relationship('FiscalYear', backref=db.backref('revisions', order_by='AccountingRevision.version'))
    submitter = db.relationship('Member', foreign_keys=[submitted_by])
    reviewer = db.relationship('Member', foreign_keys=[reviewer_id])
    withdrawer = db.relationship('Member', foreign_keys=[withdrawn_by])
