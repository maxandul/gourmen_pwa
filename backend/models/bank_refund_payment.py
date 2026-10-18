"""Link actual outgoing allocations to confirmed incoming surplus."""
from backend.extensions import db


class BankRefundPayment(db.Model):
    __tablename__ = 'bank_refund_payments'
    id = db.Column(db.Integer, primary_key=True)
    confirmation_id = db.Column(db.Integer, db.ForeignKey('bank_refund_confirmations.id', ondelete='RESTRICT'), nullable=False, index=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True)
    confirmation = db.relationship('BankRefundConfirmation', backref='payments')
    allocation = db.relationship('BankPaymentAllocation', backref=db.backref('refund_payment', uselist=False))
