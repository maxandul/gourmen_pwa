"""Immutable link between a corrected claim and a real bank outflow."""
from backend.extensions import db


class ClaimRefundPayment(db.Model):
    __tablename__ = 'claim_refund_payments'
    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey('member_claims.id', ondelete='RESTRICT'), nullable=False, index=True)
    correction_id = db.Column(db.Integer, db.ForeignKey('billbro_corrections.id', ondelete='RESTRICT'), nullable=False)
    allocation_id = db.Column(db.Integer, db.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True)
    claim = db.relationship('MemberClaim')
    correction = db.relationship('BillBroCorrection')
    allocation = db.relationship('BankPaymentAllocation', backref=db.backref('claim_refund_payment', uselist=False))
