"""Prepare paid-club corrections while the effective settlement stays untouched."""
from datetime import datetime
from uuid import uuid4
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData
from sqlalchemy import or_
from backend.extensions import db
from backend.models.accounting import Booking
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.billbro_correction_draft import BillBroCorrectionDraft
from backend.services.area_permissions import AreaPermissionService
from backend.services.billbro_correction import BillBroCorrectionService, CorrectionError, digest, record
from backend.services.ggl_rules import GGLService


class BillBroDraftService(BillBroCorrectionService):
    @staticmethod
    def serializer():
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='billbro-paid-draft-v2')

    @staticmethod
    def require_actor(event, actor):
        if not event or not event.is_visible_to(actor) or not (
                AreaPermissionService.can_manage_event(actor, event) or
                AreaPermissionService.has_scope(actor, 'accounting_read')):
            raise CorrectionError('Keine Berechtigung fÃ¼r diesen Korrekturentwurf.')

    @staticmethod
    def require_preparer(event, actor):
        if not event or not AreaPermissionService.can_manage_event(actor, event):
            raise CorrectionError('Nur die zustÃ¤ndige Organisation kann diesen Entwurf vorbereiten oder zurÃ¼ckziehen.')

    @classmethod
    def load(cls, event_id, actor, lock=False):
        event, parts, claims, years, state = super().load(event_id, actor, lock=lock)
        bookings = Booking.query.filter_by(event_id=event_id).order_by(Booking.id).populate_existing().all()
        allocations = BankPaymentAllocation.query.filter(or_(
            BankPaymentAllocation.claim_id.in_([c.id for c in claims]),
            BankPaymentAllocation.booking_id.in_([b.id for b in bookings]))).order_by(BankPaymentAllocation.id).populate_existing().all()
        from backend.models.claim_refund_payment import ClaimRefundPayment
        refunds = ClaimRefundPayment.query.filter(ClaimRefundPayment.claim_id.in_([c.id for c in claims])).order_by(ClaimRefundPayment.id).all()
        state['claim_refund_payments'] = [record(r) for r in refunds]
        state['claim_refund_allocations'] = [record(r.allocation) for r in refunds]
        state['bookings'] = [record(b) for b in bookings]
        state['payment_allocations'] = [record(a) for a in allocations]
        state['payment_bookings'] = [record(a.effective_booking) for a in allocations if a.effective_booking]
        return event, parts, claims, years, state

    @staticmethod
    def pending_state(event_id):
        return [d.id for d in BillBroCorrectionDraft.query.filter_by(event_id=event_id, status='pending').order_by(BillBroCorrectionDraft.id)]

    @classmethod
    def validate(cls, event, parts, claims, years, proposed, state):
        old, new = super().validate(event, parts, claims, years, proposed, paid_club_draft=True)
        if not any(c.paid_rappen for c in claims) and not state['bookings'] and not state['payment_allocations']:
            raise CorrectionError('Keine erfassten Zahlungen oder Buchungen. Den unbezahlten Korrekturweg verwenden.')
        return old, new

    @classmethod
    def display(cls, event, parts, claims, years, proposed, state):
        old, new = cls.validate(event, parts, claims, years, proposed, state)
        ggl = GGLService.project_points(cls.projected_parts(parts, proposed), proposed['invoice']) if cls.ggl_changes(event, parts, proposed) else None
        claims_by_member = {c.member_id: c for c in claims}
        rows = []
        for part in parts:
            paid = claims_by_member[part.member_id].paid_rappen if part.member_id in claims_by_member else 0
            refunded = claims_by_member[part.member_id].refunded_rappen if part.member_id in claims_by_member else 0
            net = paid - refunded
            expected = new.get(part.member_id, 0)
            rows.append(dict(name=part.member.display_name, member_id=part.member_id,
                before=old.get(part.member_id, 0), after=expected, paid=paid, refunded=refunded, net=net,
                open=max(expected-net, 0), refund=max(net-expected, 0),
                before_attending=part.billbro_attending, after_attending=proposed['attendance'][str(part.id)],
                before_type=part.esstyp.value if part.esstyp else None, after_type=proposed['types'].get(str(part.id), part.esstyp.value if part.esstyp else None)))
        result = dict(old_invoice=event.rechnungsbetrag_rappen, old_total=event.gesamtbetrag_rappen,
            rows=rows, proposed=proposed,
            blocked_years=[y.year for y in years if not y.is_open],
            ggl_rows=[dict(name=p.member.display_name, before=dict(rank=p.rank, points=p.points), after=ggl[p.id]) for p in parts] if ggl else [])
        return result

    @classmethod
    def preview(cls, event_id, actor, form):
        event, parts, claims, years, state = cls.load(event_id, actor)
        cls.require_preparer(event, actor)
        proposed = cls.proposal(form, event.rechnungsbetrag_rappen, parts)
        result = cls.display(event, parts, claims, years, proposed, state)
        result['token'] = cls.serializer().dumps(dict(actor=actor.id, generation=actor.auth_generation,
            event=event_id, before=digest(state), proposed=proposed, pending=cls.pending_state(event_id), nonce=uuid4().hex))
        return result

    @classmethod
    def save(cls, event_id, actor, token):
        try:
            try:
                payload = cls.serializer().loads(token, max_age=1800)
            except (BadData, TypeError):
                raise CorrectionError('Entwurfsvorschau ist ungÃ¼ltig oder abgelaufen. Neu vorbereiten.') from None
            if payload.get('actor') != actor.id or payload.get('generation') != actor.auth_generation or payload.get('event') != event_id:
                raise CorrectionError('Entwurfsvorschau gehÃ¶rt nicht zu diesem Zugang oder Event.')
            event, parts, claims, years, before = cls.load(event_id, actor, lock=True)
            cls.require_preparer(event, actor)
            request_hash = digest(token)
            existing = BillBroCorrectionDraft.query.filter_by(request_hash=request_hash).first()
            if existing:
                result = existing.id
                db.session.rollback()
                return result, False
            if payload['before'] != digest(before) or payload['pending'] != cls.pending_state(event_id):
                raise CorrectionError('Ausgangs- oder Entwurfsstand wurde geÃ¤ndert. Neu vorbereiten; nichts Ã¼berschrieben.')
            proposed = payload['proposed']
            # Derive the stored preview from the exact locked business snapshot.
            display = cls.display(event, parts, claims, years, proposed, before)
            for previous in BillBroCorrectionDraft.query.filter_by(event_id=event_id, status='pending').all():
                previous.status = 'superseded'
                previous.status_reason = 'Durch neueren Entwurf ersetzt.'
                previous.status_actor_id = actor.id
                previous.status_at = datetime.utcnow()
            draft = BillBroCorrectionDraft(event_id=event_id, actor_id=actor.id, request_hash=request_hash,
                before_json=before, proposal_json=proposed, preview_json=display, status='pending')
            db.session.add(draft)
            db.session.flush()
            result = draft.id
            db.session.commit()
            return result, True
        except CorrectionError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise CorrectionError('Entwurf nicht gespeichert. Die bisherige Abrechnung bleibt unverÃ¤ndert.') from None

    @classmethod
    def withdraw(cls, event_id, draft_id, actor, reason):
        try:
            event = cls.load(event_id, actor, lock=True)[0]
            cls.require_preparer(event, actor)
            draft = BillBroCorrectionDraft.query.filter_by(id=draft_id, event_id=event_id).populate_existing().with_for_update().first()
            if not draft:
                raise CorrectionError('Entwurf nicht gefunden.')
            if draft.status == 'withdrawn':
                db.session.rollback()
                return False
            if draft.status != 'pending':
                raise CorrectionError('Nur ein offener Entwurf kann zurÃ¼ckgezogen werden.')
            reason = (reason or '').strip()
            if not 1 <= len(reason) <= 1000:
                raise CorrectionError('Grund mit 1 bis 1000 Zeichen erforderlich.')
            draft.status = 'withdrawn'
            draft.status_reason = reason
            draft.status_actor_id = actor.id
            draft.status_at = datetime.utcnow()
            db.session.commit()
            return True
        except CorrectionError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise CorrectionError('Entwurf nicht zurÃ¼ckgezogen. Aktuellen Stand prÃ¼fen.') from None
