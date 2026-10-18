"""Summation-preserving allocations of one immutable bank movement."""
from backend.extensions import db
from backend.models.accounting import (Account,AccountKind,BankTransactionStatus,Booking,
    BookingDirection,FiscalYear,FiscalYearStatus,MemberClaim)
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.member import Member
from backend.models.event import Event
from backend.services.accounting import AccountingService,AccountingValidationError


class PaymentAllocationService:
    @staticmethod
    def rows(tx):
        return BankPaymentAllocation.query.filter_by(bank_transaction_id=tx.id).order_by(BankPaymentAllocation.id).all()

    @classmethod
    def summary(cls,tx):
        rows=cls.rows(tx)
        booked=sum(row.amount_rappen for row in rows if row.kind!='refund')
        refund=sum(row.amount_rappen for row in rows if row.kind=='refund')
        legacy=not rows and tx.status==BankTransactionStatus.BOOKED
        return dict(rows=rows,booked=tx.amount_rappen if legacy else booked,refund=refund,
                    remaining=0 if legacy else tx.amount_rappen-booked-refund,legacy=legacy)

    @staticmethod
    def record(tx,booking,kind,actor_id,*,claim_id=None,member_id=None,amount=None,position=0):
        row=BankPaymentAllocation(bank_transaction_id=tx.id,version=tx.allocation_version,
            position=position,kind=kind,amount_rappen=amount if amount is not None else booking.amount_rappen,
            booking_id=booking.id if booking else None,claim_id=claim_id,
            member_id=member_id,created_by=actor_id)
        db.session.add(row)
        return row

    @classmethod
    def allocate(cls,tx_id,*,expected_version,kind,amount_rappen,actor,account_id=None,claim_id=None,
                 member_id=None,event_id=None):
        from backend.services.bank_import import BankImportService,BankImportError,CLAIM_ACCOUNT_CODES,ROUNDING_ACCOUNT_CODES
        try:
            tx=BankImportService.get_transaction(tx_id,lock=True)
            if not tx.is_pending or tx.is_collective:
                raise BankImportError('Diese Bankbewegung ist nicht zur Teilzuordnung offen.')
            if type(expected_version) is not int or tx.allocation_version!=expected_version:
                raise BankImportError('Zuordnungsstand geändert. Bitte neu laden.')
            if kind not in ('claim','booking','rounding','refund'):
                raise BankImportError('Ungültige Zuordnungsart.')
            AccountingService.validate_booking_amount(amount_rappen)
            state=cls.summary(tx)
            if amount_rappen>state['remaining']:
                raise BankImportError('Betrag überschreitet den noch nicht zugeordneten Rest.')
            if not state['rows'] and Booking.query.filter_by(payment_ref=tx.line_key).first():
                raise BankImportError('Historische Buchung ohne Zuordnungsjournal: zuerst gezielt abgleichen.')
            if member_id is not None and db.session.get(Member,member_id) is None:
                raise BankImportError('Mitglied nicht gefunden.')
            if event_id is not None and db.session.get(Event,event_id) is None:
                raise BankImportError('Event nicht gefunden.')
            fy=AccountingService.get_or_create_fiscal_year(tx.booked_date.year,commit=False)
            fy=FiscalYear.query.filter_by(id=fy.id).populate_existing().with_for_update().one()
            if fy.status!=FiscalYearStatus.OPEN:
                raise BankImportError('Zahlungsjahr ist nicht offen.')
            claim=None
            if kind in ('claim','rounding'):
                if tx.direction!=BookingDirection.IN:
                    raise BankImportError('Forderung und Aufrundung benötigen einen Zahlungseingang.')
                claim=MemberClaim.query.filter_by(id=claim_id).populate_existing().with_for_update().first()
                if not claim or not claim.is_club_claim:
                    raise BankImportError('Vereinsforderung nicht gefunden.')
                if member_id is not None and member_id!=claim.member_id:
                    raise BankImportError('Mitglied passt nicht zur Forderung.')
                if event_id is not None and event_id!=claim.event_id:
                    raise BankImportError('Event passt nicht zur Forderung.')
                member_id,event_id=claim.member_id,claim.event_id
                if kind=='claim':
                    if not claim.is_open or amount_rappen>claim.open_rappen:
                        raise BankImportError('Betrag überschreitet die offene Forderung.')
                    code=CLAIM_ACCOUNT_CODES.get(claim.claim_type)
                else:
                    if not any(row.kind=='claim' and row.claim_id==claim.id for row in state['rows']):
                        raise BankImportError('Aufrundung benötigt eine Forderungszuordnung dieser Bankbewegung.')
                    code=ROUNDING_ACCOUNT_CODES.get(claim.claim_type)
                account=Account.query.filter_by(code=code).first() if code else None
            else:
                if claim_id is not None:
                    raise BankImportError('Diese Zuordnungsart verwendet keine Forderung.')
                account=db.session.get(Account,account_id) if account_id else None
            if kind=='refund':
                if tx.direction!=BookingDirection.IN or account_id or event_id:
                    raise BankImportError('Rückzahlungsbedarf nur für Eingang ohne Buchungskonto/Event vormerken.')
                booking=None
            else:
                expected_kind=AccountKind.INCOME if tx.is_income else AccountKind.EXPENSE
                if not account or not account.is_active or account.kind!=expected_kind:
                    raise BankImportError('Passendes aktives Konto fehlt.')
                if account_id and account_id!=account.id:
                    raise BankImportError('Konto passt nicht zur Zuordnung.')
                booking=AccountingService.create_booking(fy.id,tx.booked_date,
                    BankImportService._booking_description(tx),amount_rappen,tx.direction,account.id,
                    event_id,member_id,actor,payment_ref=tx.line_key,commit=False)
                if kind=='claim':
                    claim.register_payment(amount_rappen)
            tx.allocation_version+=1
            row=cls.record(tx,booking,kind,actor.id,claim_id=claim.id if claim else None,
                           member_id=member_id,amount=amount_rappen)
            db.session.flush()
            result=cls.summary(tx)
            if result['remaining']==0 and result['refund']==0:
                tx.status=BankTransactionStatus.BOOKED
                tx.booking_id=next(item.booking_id for item in result['rows'] if item.booking_id)
            db.session.commit()
            return row
        except AccountingValidationError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise BankImportError('Zuordnung nicht bestätigt. Aktuellen Stand vor Wiederholung prüfen.') from None
