"""Validate bank evidence before applying a paid correction or refund."""
from backend.models.accounting import BookingDirection
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.claim_refund_payment import ClaimRefundPayment
from backend.services.accounting import AccountingValidationError


class ClaimPaymentEvidence:
    @staticmethod
    def validate(claim):
        if not claim.is_club_claim or claim.paid_rappen < 0:
            raise AccountingValidationError('Vereinszahlungsstand muss zuerst geklaert werden.')
        receipts = BankPaymentAllocation.query.filter_by(claim_id=claim.id, kind='claim', reversal_id=None).populate_existing().all()
        if sum(r.amount_rappen for r in receipts) != claim.paid_rappen:
            raise AccountingValidationError('Gespeicherter Eingang ist nicht vollstaendig durch Bankzuordnungen belegt. Zuerst klaeren.')
        for row in receipts:
            booking = row.booking
            if not booking or booking.reversal_id or row.transaction.direction != BookingDirection.IN or (
                    booking.direction != BookingDirection.IN or booking.amount_rappen != row.amount_rappen or
                    booking.member_id != claim.member_id or row.member_id != claim.member_id or
                    booking.event_id != claim.event_id or booking.payment_ref != row.transaction.line_key or
                    booking.booking_date != row.transaction.booked_date):
                raise AccountingValidationError('Eingangsnachweis passt nicht zur Forderung. Zuerst klaeren.')
        refunds = ClaimRefundPayment.query.filter_by(claim_id=claim.id).all()
        for link in refunds:
            row = link.allocation
            if row.reversal_id:
                continue
            booking = row.booking
            if not booking or booking.reversal_id or row.kind != 'booking' or (
                    row.transaction.direction != BookingDirection.OUT or booking.direction != BookingDirection.OUT or
                    booking.account.code != '6710' or booking.amount_rappen != row.amount_rappen or
                    row.member_id != claim.member_id or booking.member_id != claim.member_id or
                    booking.event_id != claim.event_id or link.correction.event_id != claim.event_id or
                    booking.payment_ref != row.transaction.line_key or booking.booking_date != row.transaction.booked_date):
                raise AccountingValidationError('Rueckflussnachweis passt nicht zur Forderung. Zuerst klaeren.')
        if claim.net_paid_rappen < 0:
            raise AccountingValidationError('Rueckfluesse uebersteigen die belegten Eingaenge.')
        return receipts
