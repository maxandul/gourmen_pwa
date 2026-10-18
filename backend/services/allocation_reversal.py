"""Withdraw a whole allocation version without erasing its payment evidence."""
from collections import defaultdict

from backend.extensions import db
from backend.models.accounting import Booking, BankTransactionStatus, ClaimStatus, MemberClaim, FiscalYear
from backend.models.bank_allocation_reversal import BankAllocationReversal
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.area_permissions import AreaPermissionService
from backend.services.bank_import import BankImportService, BankImportError
from backend.services.payment_allocations import PaymentAllocationService


class AllocationReversalService:
    @classmethod
    def reverse(cls, tx_id, actor, *, expected_version, reason):
        try:
            if not AreaPermissionService.has_scope(actor, 'accounting_write'):
                raise BankImportError('Zuordnungsrücknahme nicht erlaubt.')
            reason = (reason or '').strip()
            if not reason or len(reason) > 2000:
                raise BankImportError('Grund mit 1 bis 2000 Zeichen erforderlich.')
            tx = BankImportService.get_transaction(tx_id, lock=True)
            if type(expected_version) is not int or tx.allocation_version != expected_version:
                raise BankImportError('Zuordnungsstand geändert. Bitte neu laden.')
            if tx.is_collective or tx.status == BankTransactionStatus.IGNORED:
                raise BankImportError('Diese Bankbewegung kann nicht zurückgenommen werden.')
            state = PaymentAllocationService.summary(tx)
            rows = state['active_rows']
            if not rows or state['remaining'] < 0:
                raise BankImportError('Keine eindeutigen aktiven Zuordnungen. Historischen Stand gezielt abgleichen.')
            if tx.status == BankTransactionStatus.BOOKED and (state['remaining'] or state['refund']):
                raise BankImportError('Bankstatus passt nicht zur Zuordnung. Zuerst gezielt abgleichen.')
            bookings = [row.effective_booking for row in rows if row.effective_booking]
            # Refund-only reservations still belong to their payment year.
            fy = FiscalYear.query.filter_by(year=tx.booked_date.year).first()
            if fy is None:
                raise BankImportError('Zahlungsjahr fehlt. Historischen Stand gezielt abgleichen.')
            years = AccountingService.lock_fiscal_years(fy.id, *[b.fiscal_year_id for b in bookings])
            if any(not year.is_open for year in years.values()):
                raise BankImportError('Zahlungsjahr ist nicht offen. Zuerst begründet wiederöffnen.')
            if bookings:
                Booking.query.filter(Booking.id.in_([b.id for b in bookings])).order_by(Booking.id).populate_existing().with_for_update().all()
            totals = defaultdict(int)
            for row in rows:
                booking = row.effective_booking
                if booking and (booking.reversal_id or booking.amount_rappen != row.amount_rappen
                        or booking.direction != tx.direction or booking.payment_ref != tx.line_key
                        or booking.booking_date != tx.booked_date or booking.member_id != row.member_id
                        or booking.fiscal_year.year != tx.booked_date.year):
                    raise BankImportError('Buchungsstand weicht von Zuordnung ab. Zuerst gezielt abgleichen.')
                if row.kind == 'claim':
                    totals[row.claim_id] += row.amount_rappen
            claims = {c.id: c for c in MemberClaim.query.filter(MemberClaim.id.in_(totals)).order_by(MemberClaim.id).populate_existing().with_for_update().all()}
            for claim_id, amount in totals.items():
                claim = claims.get(claim_id)
                if not claim or not claim.is_club_claim or claim.paid_rappen < amount:
                    raise BankImportError('Forderungsstand passt nicht zur Zuordnung. Zuerst gezielt abgleichen.')
                if any(row.member_id != claim.member_id for row in rows if row.kind == 'claim' and row.claim_id == claim_id):
                    raise BankImportError('Forderungsmitglied wurde geändert. Zuerst gezielt abgleichen.')
            reversal = BankAllocationReversal(bank_transaction_id=tx.id, version=tx.allocation_version+1,
                                               reason=reason, created_by=actor.id)
            db.session.add(reversal)
            db.session.flush()
            for row in rows:
                row.reversal_id = reversal.id
                if row.effective_booking:
                    row.effective_booking.reversal_id = reversal.id
            for claim_id, amount in totals.items():
                claim = claims[claim_id]
                claim.paid_rappen -= amount
                if claim.status != ClaimStatus.ERLASSEN:
                    claim.status = (ClaimStatus.BEGLICHEN if claim.paid_rappen >= claim.expected_rappen else
                                    ClaimStatus.TEILWEISE if claim.paid_rappen else ClaimStatus.OFFEN)
                if claim.paid_rappen < claim.expected_rappen:
                    claim.settled_at = None
            tx.allocation_version += 1
            tx.status = BankTransactionStatus.PENDING
            tx.booking_id = None
            db.session.commit()
            return reversal
        except AccountingValidationError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise BankImportError('Rücknahme nicht bestätigt. Aktuellen Stand vor Wiederholung prüfen.') from None
