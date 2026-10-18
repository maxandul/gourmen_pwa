"""Append-only allocation evidence; source bank rows remain unchanged."""
from datetime import datetime
from backend.extensions import db


class BankPaymentAllocation(db.Model):
    __tablename__ = 'bank_payment_allocations'
    id = db.Column(db.Integer, primary_key=True)
    bank_transaction_id = db.Column(db.Integer, db.ForeignKey('bank_transactions.id',ondelete='RESTRICT'),nullable=False)
    reversal_id = db.Column(db.Integer,db.ForeignKey('bank_allocation_reversals.id',ondelete='RESTRICT'))
    reversal = db.relationship('BankAllocationReversal')
    version = db.Column(db.Integer,nullable=False)
    position = db.Column(db.Integer,nullable=False,default=0,server_default='0')
    kind = db.Column(db.String(16),nullable=False)
    amount_rappen = db.Column(db.Integer,nullable=False)
    claim_id = db.Column(db.Integer,db.ForeignKey('member_claims.id',ondelete='RESTRICT'))
    booking_id = db.Column(db.Integer,db.ForeignKey('bookings.id',ondelete='RESTRICT'),unique=True)
    member_id = db.Column(db.Integer,db.ForeignKey('members.id',ondelete='RESTRICT'))
    created_by = db.Column(db.Integer,db.ForeignKey('members.id',ondelete='RESTRICT'),nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    transaction = db.relationship('BankTransaction',backref=db.backref('payment_allocations',order_by='BankPaymentAllocation.id',passive_deletes=True))
    booking = db.relationship('Booking',backref=db.backref('payment_allocation',uselist=False))
    claim = db.relationship('MemberClaim')
    member = db.relationship('Member',foreign_keys=[member_id])
    actor = db.relationship('Member',foreign_keys=[created_by])
    __table_args__ = (
        db.CheckConstraint('amount_rappen > 0',name='ck_payment_allocation_positive'),
        db.CheckConstraint("kind IN ('claim','booking','rounding','refund')",name='ck_payment_allocation_kind'),
        db.CheckConstraint("(kind = 'refund' AND booking_id IS NULL) OR (kind != 'refund' AND booking_id IS NOT NULL)",name='ck_payment_allocation_booking'),
        db.UniqueConstraint('bank_transaction_id','version','position',name='uq_payment_allocation_step'),
        db.Index('ix_payment_allocations_transaction','bank_transaction_id'))

    @property
    def kind_display(self):
        if self.kind == "refund" and self.refund_confirmation:
            return "Bestätigter Überschuss (3620)"
        return {'claim':'Forderung','booking':'Buchung','rounding':'Freiwillige Aufrundung',
                'refund':'Rückzahlungsbedarf (vorgemerkt)'}[self.kind]

    @property
    def effective_booking(self):
        return self.booking or (self.refund_confirmation.booking if self.refund_confirmation else None)
