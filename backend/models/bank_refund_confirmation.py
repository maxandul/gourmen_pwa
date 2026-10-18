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

    @property
    def paid_rappen(self):
        from backend.models.bank_refund_payment import BankRefundPayment
        from backend.models.bank_payment_allocation import BankPaymentAllocation
        return sum(row.amount_rappen for row in BankPaymentAllocation.query.join(
            BankRefundPayment, BankRefundPayment.allocation_id == BankPaymentAllocation.id).filter(
                BankRefundPayment.confirmation_id == self.id,
                BankPaymentAllocation.reversal_id.is_(None)).all())

    @property
    def open_rappen(self):
        return 0 if self.allocation.reversal_id else self.allocation.amount_rappen - self.paid_rappen
