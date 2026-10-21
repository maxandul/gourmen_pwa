"""Explicit financial approval preserves claim identities and all bank evidence."""
from datetime import datetime
from uuid import uuid4
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData
from backend.extensions import db
from backend.models.accounting import MemberClaim, ClaimType
from backend.models.billbro_correction import BillBroCorrection
from backend.models.billbro_correction_draft import BillBroCorrectionDraft
from backend.services.area_permissions import AreaPermissionService
from backend.services.billbro_correction import CorrectionError, digest, record
from backend.services.billbro_drafts import BillBroDraftService
from backend.services.claim_payment_evidence import ClaimPaymentEvidence
from backend.services.accounting import AccountingValidationError


class BillBroFinanceService(BillBroDraftService):
    @staticmethod
    def serializer():
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='billbro-finance-approval-v1')

    @staticmethod
    def require_actor(event, actor):
        if not event or not event.is_visible_to(actor) or not AreaPermissionService.has_scope(actor, 'accounting_write'):
            raise CorrectionError('Keine Berechtigung zur finanziellen Bestaetigung dieses Events.')

    @staticmethod
    def get_draft(event_id, draft_id, lock=False):
        query = BillBroCorrectionDraft.query.filter_by(id=draft_id,event_id=event_id).populate_existing()
        draft = (query.with_for_update() if lock else query).first()
        if not draft:
            raise CorrectionError('Entwurf nicht gefunden.')
        return draft

    @classmethod
    def check(cls, event, parts, claims, years, state, draft):
        if draft.status != 'pending':
            raise CorrectionError('Entwurf ist nicht mehr offen.')
        if digest(state) != digest(draft.before_json):
            raise CorrectionError('Ausgangsstand geaendert. Organisation muss einen aktuellen Entwurf vorbereiten.')
        if not any(y.year == event.datum.year for y in years):
            raise CorrectionError('Geschaeftsjahr des Events fehlt. Zuerst klaeren.')
        if any(not y.is_open for y in years):
            raise CorrectionError('Betroffenes Jahr ist nicht offen. Zuerst begruendet wieder oeffnen und Entwurf erneuern.')
        cls.validate(event,parts,claims,years,draft.proposal_json,state)
        try:
            for claim in claims:
                ClaimPaymentEvidence.validate(claim)
        except AccountingValidationError as exc:
            raise CorrectionError(str(exc)) from None

    @classmethod
    def approval_preview(cls, event_id, draft_id, actor):
        event,parts,claims,years,state = cls.load(event_id,actor)
        draft = cls.get_draft(event_id,draft_id)
        cls.check(event,parts,claims,years,state,draft)
        display = cls.display(event,parts,claims,years,draft.proposal_json,state)
        display['token'] = cls.serializer().dumps(dict(actor=actor.id,generation=actor.auth_generation,event=event_id,
            draft=draft_id,draft_hash=digest(record(draft)),before=digest(state),nonce=uuid4().hex))
        return display

    @classmethod
    def approve(cls,event_id,draft_id,actor,token):
        try:
            try:
                payload=cls.serializer().loads(token,max_age=1800)
            except (BadData,TypeError):
                raise CorrectionError('Finanzvorschau ungueltig oder abgelaufen. Erneut pruefen.') from None
            if payload.get('actor') != actor.id or payload.get('generation') != actor.auth_generation or payload.get('event') != event_id or payload.get('draft') != draft_id:
                raise CorrectionError('Finanzvorschau gehoert nicht zu diesem Zugang oder Entwurf.')
            event,parts,claims,years,before = cls.load(event_id,actor,lock=True)
            draft = cls.get_draft(event_id,draft_id,lock=True)
            request_hash=digest(token)
            existing=BillBroCorrection.query.filter_by(request_hash=request_hash).first()
            if existing:
                result=existing.id; db.session.rollback(); return result,False
            if payload['before'] != digest(before) or payload['draft_hash'] != digest(record(draft)):
                raise CorrectionError('Entwurfs- oder Zahlungsstand geaendert. Erneut pruefen.')
            cls.check(event,parts,claims,years,before,draft)
            proposed=draft.proposal_json
            shares=cls.apply_event(event,parts,proposed)
            by_member={c.member_id:c for c in claims}
            for claim in claims:
                claim.expected_rappen=shares.get(claim.member_id,0)
                claim.sync_payment_status()
            year=next(y for y in years if y.year==event.datum.year)
            for mid,share in shares.items():
                if share>0 and mid not in by_member:
                    db.session.add(MemberClaim(member_id=mid,event_id=event_id,fiscal_year_id=year.id,
                        claim_type=ClaimType.ESSENSANTEIL,expected_rappen=share,paid_rappen=0,
                        note=f'Essensanteil {event.display_date} (korrigiert)'))
            db.session.flush()
            after=cls.load(event_id,actor)[4]
            after['finance_approval']=dict(draft_id=draft.id,prepared_by=draft.actor_id,approved_by=actor.id)
            history=BillBroCorrection(event_id=event_id,actor_id=actor.id,reason=proposed['reason'],
                request_hash=request_hash,before_json=before,after_json=after)
            db.session.add(history)
            draft.status='applied'; draft.status_actor_id=actor.id; draft.status_at=datetime.utcnow()
            draft.status_reason='Finanziell bestaetigt; Bankbewegungen unveraendert.'
            db.session.flush(); result=history.id; db.session.commit()
            return result,True
        except CorrectionError:
            db.session.rollback(); raise
        except Exception:
            db.session.rollback()
            raise CorrectionError('Finanzkorrektur nicht gespeichert. Bisherige Abrechnung bleibt erhalten.') from None

    @classmethod
    def return_draft(cls,event_id,draft_id,actor,reason):
        try:
            cls.load(event_id,actor,lock=True)
            draft=cls.get_draft(event_id,draft_id,lock=True)
            reason=(reason or '').strip()
            if not 1<=len(reason)<=900:
                raise CorrectionError('Rueckgabegrund mit 1 bis 900 Zeichen erforderlich.')
            if draft.status!='pending':
                raise CorrectionError('Nur offener Entwurf kann zurueckgegeben werden.')
            draft.status='withdrawn'; draft.status_actor_id=actor.id; draft.status_at=datetime.utcnow()
            draft.status_reason='Finanzielle Rueckgabe zur Bearbeitung: '+reason
            db.session.commit()
        except CorrectionError:
            db.session.rollback(); raise
        except Exception:
            db.session.rollback()
            raise CorrectionError('Rueckgabe nicht gespeichert. Aktuellen Stand pruefen.') from None
