"""Explicit income recognition of a refund-designated bank surplus."""
from datetime import datetime
from backend.extensions import db


class BankRefundConfirmation(db.Model):
    __tablename__ = 'bank_refund_confirmations'
    id = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='RESTRICT'), nullable=False, unique=True)
    created_by = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    allocation = db.relationship('BankPaymentAllocation', backref=db.backref('refund_confirmation', uselist=False))
    booking = db.relationship('Booking', backref=db.backref('refund_confirmation', uselist=False))
    actor = db.relationship('Member')
