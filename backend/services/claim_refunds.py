"""Match real outflows to financially approved claim reductions, without transfers."""
from backend.extensions import db
from backend.models.accounting import Account, AccountKind, MemberClaim, ClaimType, ClaimStatus
from backend.models.billbro_correction import BillBroCorrection
from backend.models.claim_refund_payment import ClaimRefundPayment
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.area_permissions import AreaPermissionService
from backend.services.bank_import import BankImportService, BankImportError
from backend.services.payment_allocations import PaymentAllocationService
from backend.services.claim_payment_evidence import ClaimPaymentEvidence


class ClaimRefundService:
    @staticmethod
    def current_correction(claim):
        history = BillBroCorrection.query.filter_by(event_id=claim.event_id).order_by(BillBroCorrection.id.desc()).first()
        if not history or not history.after_json.get('finance_approval') or not any(
                c['id']==claim.id and c['expected_rappen']==claim.expected_rappen for c in history.after_json['claims']):
            raise BankImportError('Aktuelle finanzielle Korrektur fuer diese Forderung fehlt.')
        return history

    @classmethod
    def available(cls,actor):
        if not AreaPermissionService.has_scope(actor,'accounting_read'):
            return []
        candidates=MemberClaim.query.filter(MemberClaim.creditor_member_id.is_(None),
            MemberClaim.claim_type==ClaimType.ESSENSANTEIL,
            MemberClaim.paid_rappen>MemberClaim.expected_rappen).order_by(MemberClaim.id).all()
        result=[]
        for claim in candidates:
            if not claim.event or not claim.event.is_visible_to(actor) or claim.status==ClaimStatus.ERLASSEN or claim.refund_due_rappen<=0:
                continue
            try:
                history=cls.current_correction(claim)
            except AccountingValidationError:
                continue
            result.append(dict(claim=claim,correction=history))
        return result

    @classmethod
    def allocate(cls,tx_id,claim_id,correction_id,actor,*,expected_version,amount_rappen):
        try:
            if not AreaPermissionService.has_scope(actor,'accounting_write'):
                raise BankImportError('Keine Berechtigung zum Rueckzahlungsabgleich.')
            tx=BankImportService.get_transaction(tx_id,lock=True)
            if tx.is_income or not tx.is_pending or tx.is_collective:
                raise BankImportError('Offene Ausgangsbewegung erforderlich.')
            if type(expected_version) is not int or tx.allocation_version!=expected_version:
                raise BankImportError('Bankzuordnungsstand geaendert. Neu laden.')
            AccountingService.validate_booking_amount(amount_rappen)
            year=AccountingService.get_or_create_fiscal_year(tx.booked_date.year,commit=False)
            year=AccountingService.lock_fiscal_years(year.id)[year.id]
            if not year.is_open:
                raise BankImportError('Ausgangsjahr ist nicht offen.')
            claim=MemberClaim.query.filter_by(id=claim_id).populate_existing().with_for_update().first()
            if not claim or not claim.is_club_claim or claim.claim_type!=ClaimType.ESSENSANTEIL or not claim.event or not claim.event.is_visible_to(actor):
                raise BankImportError('Berechtigte Vereinsforderung nicht gefunden.')
            if claim.status==ClaimStatus.ERLASSEN:
                raise BankImportError('Erlass zuerst gesondert klaeren.')
            correction=cls.current_correction(claim)
            if correction.id!=correction_id:
                raise BankImportError('Finanzkorrektur geaendert. Neu laden.')
            receipts=ClaimPaymentEvidence.validate(claim)
            if amount_rappen>claim.refund_due_rappen:
                raise BankImportError('Betrag ueberschreitet den offenen Rueckzahlungsbedarf.')
            if not receipts or tx.booked_date<max(r.transaction.booked_date for r in receipts):
                raise BankImportError('Ausgang liegt vor den zugehoerigen Eingaengen.')
            account=Account.query.filter_by(code='6710',is_active=True,kind=AccountKind.EXPENSE).first()
            if not account:
                raise BankImportError('Aktives Ausgabenkonto 6710 fehlt.')
            row=PaymentAllocationService.allocate(tx.id,expected_version=expected_version,kind='booking',
                amount_rappen=amount_rappen,actor=actor,account_id=account.id,member_id=claim.member_id,
                event_id=claim.event_id,commit=False)
            payment=ClaimRefundPayment(claim=claim,correction=correction,allocation=row)
            db.session.add(payment); db.session.flush()
            claim.sync_payment_status()
            db.session.commit()
            return payment
        except AccountingValidationError:
            db.session.rollback(); raise
        except Exception:
            db.session.rollback()
            raise BankImportError('Rueckzahlungsabgleich nicht gespeichert. Aktuellen Stand pruefen.') from None
