"""Version-bound unpaid amount/payer corrections with complete claim evidence."""
import hashlib
import json
from datetime import date, datetime
from enum import Enum
from uuid import uuid4
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData
from sqlalchemy import or_

from backend.extensions import db
from backend.models.event import Event, BillPaidBy
from backend.models.participation import Participation
from backend.models.accounting import MemberClaim, ClaimType, ClaimStatus, Booking, FiscalYear, FiscalYearStatus
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.billbro_correction import BillBroCorrection
from backend.services.area_permissions import AreaPermissionService
from backend.services.billbro_shares import BillBroShareService, ShareError
from backend.services.money import MoneyService


class CorrectionError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def record(obj):
    def value(raw):
        if isinstance(raw, Enum): return raw.value
        if isinstance(raw, (date, datetime)): return raw.isoformat()
        return raw
    return {col.name: value(getattr(obj, col.name)) for col in obj.__table__.columns}


class BillBroCorrectionService:
    @staticmethod
    def serializer():
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='billbro-correction-v1')

    @staticmethod
    def require_actor(event, actor):
        if not event or not AreaPermissionService.can_manage_event(actor, event) or not event.is_visible_to(actor):
            raise CorrectionError('Keine Berechtigung für diese Abrechnungskorrektur.')

    @classmethod
    def load(cls, event_id, actor, lock=False):
        query = Event.query.filter_by(id=event_id).populate_existing()
        event = (query.with_for_update() if lock else query).first()
        cls.require_actor(event, actor)
        pq = Participation.query.filter_by(event_id=event.id).order_by(Participation.id).populate_existing()
        parts = (pq.with_for_update() if lock else pq).all()
        # Year before claims matches accounting's year -> claim lock order.
        claim_years = db.session.query(MemberClaim.fiscal_year_id).filter_by(event_id=event.id)
        yq = FiscalYear.query.filter(or_(FiscalYear.year == event.datum.year, FiscalYear.id.in_(claim_years))).order_by(FiscalYear.id).populate_existing()
        years = (yq.with_for_update() if lock else yq).all()
        cq = MemberClaim.query.filter_by(event_id=event.id).order_by(MemberClaim.id).populate_existing()
        claims = (cq.with_for_update() if lock else cq).all()
        db.session.expire(event, ['participations'])
        state = dict(event=record(event), participations=[record(p) for p in parts], claims=[record(c) for c in claims],
                     years=[record(y) for y in years],
                     members=[dict(id=p.member_id, name=p.member.display_name, active=p.member.is_active) for p in parts],
                     history=[r.id for r in BillBroCorrection.query.filter_by(event_id=event.id).order_by(BillBroCorrection.id)])
        return event, parts, claims, years, state

    @staticmethod
    def proposal(form):
        reason = (form.get('reason') or '').strip()
        if not 1 <= len(reason) <= 1000:
            raise CorrectionError('Einen Grund mit 1 bis 1000 Zeichen angeben.')
        try:
            total = MoneyService.parse_positive_rappen(form.get('total'))
            mode = BillPaidBy(form.get('paid_by'))
            payer = int(form.get('payer_member_id') or 0) if mode == BillPaidBy.MITGLIED else None
        except (ValueError, TypeError):
            raise CorrectionError('Gesamtbetrag und Zahlweg gültig und rappengenau angeben.') from None
        return dict(reason=reason, total=total, paid_by=mode.value, payer=payer)

    @staticmethod
    def validate(event, parts, claims, years, proposed):
        if event.gesamtbetrag_rappen is None or not event.rechnungsbetrag_rappen:
            raise CorrectionError('Dieser Weg benötigt einen vollständigen bestehenden Abschluss.')
        if proposed['total'] < event.rechnungsbetrag_rappen:
            raise CorrectionError('Gesamtbetrag darf die Restaurantrechnung nicht unterschreiten.')
        attending = {p.member_id for p in parts if p.teilnahme}
        if proposed['paid_by'] == BillPaidBy.MITGLIED.value and proposed['payer'] not in attending:
            raise CorrectionError('Auslegende Person muss am Essen teilnehmen.')
        if any(c.paid_rappen != 0 or c.status != ClaimStatus.OFFEN or c.settled_at is not None for c in claims):
            raise CorrectionError('Zahlungen oder abgeschlossene Posten benötigen den Finanzkorrekturweg.')
        if BankPaymentAllocation.query.filter(BankPaymentAllocation.claim_id.in_([c.id for c in claims])).first() or Booking.query.filter_by(event_id=event.id).first():
            raise CorrectionError('Verbuchte Vorgänge benötigen den Finanzkorrekturweg; ihre Historie bleibt erhalten.')
        if (event.is_paid_by_club or proposed['paid_by'] == BillPaidBy.VEREINSKONTO.value or any(c.fiscal_year_id for c in claims)) and any(y.status != FiscalYearStatus.OPEN for y in years):
            raise CorrectionError('Betroffenes Geschäftsjahr ist in Revision oder abgeschlossen. Zuerst mit Grund wieder öffnen.')
        old_shares = {p.member_id: BillBroShareService.stored_share(event, p) for p in parts if p.teilnahme}
        if any(type(v) is not int or v < 0 for v in old_shares.values()):
            raise CorrectionError('Alte Einzelanteile sind unvollständig. Zuerst klären.')
        old_creditor = event.bill_payer_member_id if event.bill_paid_by == BillPaidBy.MITGLIED else None
        if event.bill_paid_by == BillPaidBy.MITGLIED and old_creditor not in attending:
            raise CorrectionError('Bisherige auslegende Person ist nicht eindeutig. Zuerst klären.')
        expected = {mid: share for mid, share in old_shares.items() if share > 0 and mid != old_creditor} if event.bill_paid_by else {}
        if len(claims) != len(expected) or len({c.member_id for c in claims}) != len(claims) or any(
                c.claim_type != ClaimType.ESSENSANTEIL or c.expected_rappen != expected.get(c.member_id) or
                c.creditor_member_id != old_creditor or c.merch_order_id is not None for c in claims):
            raise CorrectionError('Bestehende Forderungen und Anteile stimmen nicht überein. Zuerst klären.')
        if (event.gesamtbetrag_rappen, event.bill_paid_by.value if event.bill_paid_by else None, old_creditor) == (proposed['total'], proposed['paid_by'], proposed['payer']):
            raise CorrectionError('Keine Änderung gewählt.')
        try:
            shares = BillBroShareService.calculate(event, proposed['total'])
        except ShareError as exc:
            raise CorrectionError(str(exc)) from None
        return old_shares, shares

    @classmethod
    def preview(cls, event_id, actor, form):
        proposed = cls.proposal(form)
        event, parts, claims, years, state = cls.load(event_id, actor)
        old_shares, shares = cls.validate(event, parts, claims, years, proposed)
        token = cls.serializer().dumps(dict(actor=actor.id, generation=actor.auth_generation,
            event=event.id, before=digest(state), proposed=proposed, nonce=uuid4().hex))
        return dict(token=token, proposed=proposed, old_total=event.gesamtbetrag_rappen,
                    old_paid_by=event.bill_paid_by.value if event.bill_paid_by else None,
                    old_payer=event.bill_payer_member_id,
                    rows=[dict(id=p.member_id, name=p.member.display_name, before=old_shares.get(p.member_id, 0), after=shares.get(p.member_id, 0),
                               before_claim=next((c.expected_rappen for c in claims if c.member_id == p.member_id), 0),
                               after_claim=shares.get(p.member_id, 0) if p.member_id != proposed['payer'] else 0) for p in parts])

    @classmethod
    def confirm(cls, event_id, actor, token):
        try:
            try:
                payload = cls.serializer().loads(token, max_age=1800)
            except (BadData, TypeError):
                raise CorrectionError('Vorschau ist ungültig oder abgelaufen. Neu vorbereiten.') from None
            if payload.get('actor') != actor.id or payload.get('generation') != actor.auth_generation or payload.get('event') != event_id:
                raise CorrectionError('Vorschau gehört nicht zu diesem Zugang oder Event.')
            event, parts, claims, years, before = cls.load(event_id, actor, lock=True)
            request_hash = digest(token)
            existing = BillBroCorrection.query.filter_by(request_hash=request_hash).first()
            if existing:
                existing_id = existing.id
                db.session.rollback()
                return existing_id, False
            if digest(before) != payload['before']:
                raise CorrectionError('Stand wurde seit der Vorschau geändert. Neu vorbereiten; nichts wurde überschrieben.')
            proposed = payload['proposed']
            cls.validate(event, parts, claims, years, proposed)
            event.gesamtbetrag_rappen = proposed['total']
            event.trinkgeld_rappen = proposed['total'] - event.rechnungsbetrag_rappen
            event.bill_paid_by = BillPaidBy(proposed['paid_by'])
            event.bill_payer_member_id = proposed['payer']
            shares = BillBroShareService.apply(event, proposed['total'])
            creditor = proposed['payer']
            # Insert before deleting, so even SQLite cannot reuse an old claim identity.
            for mid, share in shares.items():
                if share > 0 and mid != creditor:
                    db.session.add(MemberClaim(member_id=mid, creditor_member_id=creditor, event_id=event.id,
                        claim_type=ClaimType.ESSENSANTEIL, expected_rappen=share,
                        fiscal_year_id=next((c.fiscal_year_id for c in claims if c.member_id == mid), None),
                        note=f'Essensanteil {event.display_date} (korrigiert)'))
            db.session.flush()
            for claim in claims:
                db.session.delete(claim)
            db.session.flush()
            after = cls.load(event_id, actor)[4]
            history = BillBroCorrection(event_id=event.id, actor_id=actor.id, reason=proposed['reason'],
                                       request_hash=request_hash, before_json=before, after_json=after)
            db.session.add(history)
            db.session.flush()
            history_id = history.id
            db.session.commit()
            return history_id, True
        except CorrectionError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise CorrectionError('Korrektur konnte nicht gespeichert werden. Bisherige Abrechnung bleibt erhalten; Vorschau kann erneut bestätigt werden.') from None
