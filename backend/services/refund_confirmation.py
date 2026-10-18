"""Recognize explicitly confirmed surplus on 3620; no outgoing payment."""
from backend.extensions import db
from backend.models.accounting import Account, AccountKind, BankTransactionStatus
from backend.models.bank_refund_confirmation import BankRefundConfirmation
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.area_permissions import AreaPermissionService
from backend.services.bank_import import BankImportService, BankImportError
from backend.services.payment_allocations import PaymentAllocationService


class RefundConfirmationService:
    @staticmethod
    def confirm(tx_id, allocation_id, actor, *, expected_version):
        try:
            if not AreaPermissionService.has_scope(actor, 'accounting_write'):
                raise BankImportError('Bestätigung nicht erlaubt.')
            tx = BankImportService.get_transaction(tx_id, lock=True)
            if type(expected_version) is not int or expected_version != tx.allocation_version:
                raise BankImportError('Zuordnungsstand geändert. Bitte neu laden.')
            if not tx.is_pending or not tx.is_income or tx.is_collective:
                raise BankImportError('Diese Bankbewegung ist nicht zur Bestätigung offen.')
            state = PaymentAllocationService.summary(tx)
            row = next((r for r in state['active_rows'] if r.id == allocation_id), None)
            if not row or row.kind != 'refund' or row.refund_confirmation or not row.member_id:
                raise BankImportError('Aktive Vormerkung mit eindeutigem Mitglied erforderlich.')
            if state['remaining'] < 0:
                raise BankImportError('Zuordnungen überschreiten den Bankbetrag.')
            account = Account.query.filter_by(code='3620', is_active=True, kind=AccountKind.INCOME).first()
            if not account:
                raise BankImportError('Aktives Einnahmenkonto 3620 fehlt.')
            fy = AccountingService.get_or_create_fiscal_year(tx.booked_date.year, commit=False)
            fy = AccountingService.lock_fiscal_years(fy.id)[fy.id]
            if not fy.is_open:
                raise BankImportError('Zahlungsjahr ist nicht offen.')
            booking = AccountingService.create_booking(fy.id, tx.booked_date,
                BankImportService._booking_description(tx), row.amount_rappen, tx.direction,
                account.id, None, row.member_id, actor, payment_ref=tx.line_key, commit=False)
            confirmation = BankRefundConfirmation(allocation=row, booking=booking, created_by=actor.id)
            db.session.add(confirmation)
            tx.allocation_version += 1
            db.session.flush()
            result = PaymentAllocationService.summary(tx)
            if result['remaining'] == 0 and result['refund'] == 0:
                tx.status = BankTransactionStatus.BOOKED
                tx.booking_id = next(r.effective_booking.id for r in result['active_rows'] if r.effective_booking)
            db.session.commit()
            return confirmation
        except AccountingValidationError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise BankImportError('Bestätigung fehlgeschlagen. Aktuellen Stand vor Wiederholung prüfen.') from None
