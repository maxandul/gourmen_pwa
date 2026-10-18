"""Reconcile existing bank outflows; never initiate a transfer."""
from backend.extensions import db
from backend.models.accounting import Account, AccountKind
from backend.models.bank_refund_confirmation import BankRefundConfirmation
from backend.models.bank_refund_payment import BankRefundPayment
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.area_permissions import AreaPermissionService
from backend.services.bank_import import BankImportService, BankImportError
from backend.services.payment_allocations import PaymentAllocationService


class RefundPaymentService:
    @staticmethod
    def available():
        return [row for row in BankRefundConfirmation.query.order_by(BankRefundConfirmation.id).all()
                if row.open_rappen > 0]

    @staticmethod
    def allocate(tx_id, confirmation_id, actor, *, expected_version, amount_rappen):
        try:
            if not AreaPermissionService.has_scope(actor, 'accounting_write'):
                raise BankImportError('Rückzahlungsabgleich nicht erlaubt.')
            tx = BankImportService.get_transaction(tx_id, lock=True)
            if tx.is_income or not tx.is_pending or tx.is_collective:
                raise BankImportError('Offene Ausgangsbewegung erforderlich.')
            if type(expected_version) is not int or tx.allocation_version != expected_version:
                raise BankImportError('Zuordnungsstand geändert. Bitte neu laden.')
            AccountingService.validate_booking_amount(amount_rappen)
            fy = AccountingService.get_or_create_fiscal_year(tx.booked_date.year, commit=False)
            fy = AccountingService.lock_fiscal_years(fy.id)[fy.id]
            if not fy.is_open:
                raise BankImportError('Ausgangsjahr ist nicht offen.')
            confirmation = BankRefundConfirmation.query.filter_by(id=confirmation_id).populate_existing().with_for_update().first()
            if not confirmation:
                raise BankImportError('Bestätigter Überschuss fehlt.')
            db.session.refresh(confirmation.allocation)
            db.session.refresh(confirmation.booking)
            if confirmation.allocation.reversal_id or confirmation.booking.reversal_id:
                raise BankImportError('Eingangszuordnung wurde zurückgenommen.')
            if amount_rappen > confirmation.open_rappen:
                raise BankImportError('Betrag überschreitet den offenen Rückzahlungsbedarf.')
            if tx.booked_date < confirmation.booking.booking_date:
                raise BankImportError('Ausgang liegt vor dem zugehörigen Eingang.')
            account = Account.query.filter_by(code='6710', is_active=True, kind=AccountKind.EXPENSE).first()
            if not account:
                raise BankImportError('Aktives Ausgabenkonto 6710 fehlt.')
            row = PaymentAllocationService.allocate(tx.id, expected_version=expected_version,
                kind='booking', amount_rappen=amount_rappen, actor=actor, account_id=account.id,
                member_id=confirmation.allocation.member_id, commit=False)
            payment = BankRefundPayment(confirmation=confirmation, allocation=row)
            db.session.add(payment)
            db.session.commit()
            return payment
        except AccountingValidationError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise BankImportError('Rückzahlungsabgleich fehlgeschlagen. Aktuellen Stand vor Wiederholung prüfen.') from None
