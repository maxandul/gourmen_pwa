"""Immutable evidence of a deliberate withdrawal, never a new bank movement."""
from datetime import datetime
from backend.extensions import db


class BankAllocationReversal(db.Model):
    __tablename__ = 'bank_allocation_reversals'
    __table_args__ = (db.UniqueConstraint('bank_transaction_id', 'version', name='uq_allocation_reversal_version'),)
    id = db.Column(db.Integer, primary_key=True)
    bank_transaction_id = db.Column(db.Integer, db.ForeignKey('bank_transactions.id', ondelete='RESTRICT'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transaction = db.relationship('BankTransaction', backref='allocation_reversals')
    actor = db.relationship('Member')
