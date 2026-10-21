"""Version-bound unpaid amount/payer corrections with complete claim evidence."""
import hashlib
import json
from datetime import date, datetime
from enum import Enum
from uuid import uuid4
from types import SimpleNamespace
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadData
from sqlalchemy import or_

from backend.extensions import db
from backend.models.event import Event, BillPaidBy
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim, ClaimType, ClaimStatus, Booking, FiscalYear, FiscalYearStatus
from backend.models.bank_payment_allocation import BankPaymentAllocation
from backend.models.billbro_correction import BillBroCorrection
from backend.services.area_permissions import AreaPermissionService
from backend.services.billbro_shares import BillBroShareService, ShareError
from backend.services.money import MoneyService
from backend.services.ggl_rules import GGLService


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
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='billbro-correction-v5')

    @staticmethod
    def require_actor(event, actor):
        if not event or not AreaPermissionService.can_manage_event(actor, event) or not event.is_visible_to(actor):
            raise CorrectionError('Keine Berechtigung für diese Abrechnungskorrektur.')

    @staticmethod
    def candidates(event, parts):
        existing = {p.member_id for p in parts}
        return parts + [SimpleNamespace(id=-m.id, member_id=m.id, member=m,
            teilnahme=None, responded_at=None, billbro_attendance=None,
            billbro_attending=False, esstyp=None, guess_bill_amount_rappen=None,
            diff_amount_rappen=None, rank=None, points=None, calculated_share_rappen=None)
            for m in event.eligible_members_query().order_by('id').all() if m.id not in existing]

    @staticmethod
    def projected_parts(parts, proposed):
        return [SimpleNamespace(id=p.id, member_id=p.member_id,
            teilnahme=proposed['attendance'][str(p.id)],
            guess_bill_amount_rappen=p.guess_bill_amount_rappen,
            esstyp=Esstyp(proposed['types'][str(p.id)]) if proposed['attendance'][str(p.id)] else p.esstyp)
            for p in parts]

    @staticmethod
    def ggl_changes(event, parts, proposed):
        return event.supports_ggl and (proposed['invoice'] != event.rechnungsbetrag_rappen or
            any(proposed['attendance'][str(p.id)] != p.billbro_attending for p in parts))

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
        eligible = event.eligible_members_query().order_by('id').all()
        state['eligible_members'] = [dict(id=m.id, name=m.display_name) for m in eligible]
        return event, cls.candidates(event, parts), claims, years, state

    @staticmethod
    def proposal(form, previous_invoice, parts):
        reason = (form.get('reason') or '').strip()
        if not 1 <= len(reason) <= 1000:
            raise CorrectionError('Einen Grund mit 1 bis 1000 Zeichen angeben.')
        try:
            total = MoneyService.parse_positive_rappen(form.get('total'))
            invoice = MoneyService.parse_positive_rappen(form.get('invoice', f'{(previous_invoice or 0) / 100:.2f}'))
            mode = BillPaidBy(form.get('paid_by'))
            payer = int(form.get('payer_member_id') or 0) if mode == BillPaidBy.MITGLIED else None
        except (ValueError, TypeError):
            raise CorrectionError('Restaurantrechnung, Gesamtbetrag und Zahlweg gültig und rappengenau angeben.') from None
        allowed = {f'{prefix}_{p.id}' for p in parts for prefix in ('esstyp', 'attendance')}
        if any(key.startswith(('esstyp_', 'attendance_')) and key not in allowed for key in form):
            raise CorrectionError('Auswahl enthält keine Person dieser Abrechnung.')
        types, attendance = {}, {}
        for part in parts:
            raw = form.get(f'attendance_{part.id}', 'present' if part.billbro_attending else 'absent')
            if raw not in ('present', 'absent'):
                raise CorrectionError('Anwesenheit gültig wählen.')
            attendance[str(part.id)] = raw == 'present'
            if raw == 'present':
                try:
                    types[str(part.id)] = Esstyp(form.get(f'esstyp_{part.id}', part.esstyp.value if part.esstyp else '')).value
                except ValueError:
                    raise CorrectionError('Für jede anwesende Person einen gültigen Ess-Typ wählen.') from None
        return dict(reason=reason, total=total, invoice=invoice, paid_by=mode.value, payer=payer, types=types, attendance=attendance,
                    private_unpaid_confirmed=form.get('private_unpaid_confirmed') == 'yes',
                    private_unpaid_note=(form.get('private_unpaid_note') or '').strip())

    @classmethod
    def validate(cls, event, parts, claims, years, proposed, *, paid_club_draft=False):
        if event.gesamtbetrag_rappen is None or not event.rechnungsbetrag_rappen:
            raise CorrectionError('Dieser Weg benötigt einen vollständigen bestehenden Abschluss.')
        if not paid_club_draft and event.bill_paid_by == BillPaidBy.MITGLIED and (
                proposed.get('private_unpaid_confirmed') is not True or
                not 1 <= len(proposed.get('private_unpaid_note', '')) <= 1000):
            raise CorrectionError('Private Zahlungen sind der App unbekannt. Zuerst klären und mit Vermerk bestätigen, dass noch keine privaten Zahlungen erfolgt sind. Bei Zahlung oder unklarem Stand ist der Finanzklärungsweg erforderlich.')
        if proposed['total'] < proposed['invoice']:
            raise CorrectionError('Gesamtbetrag darf die Restaurantrechnung nicht unterschreiten.')
        attending = {p.member_id for p in parts if p.billbro_attending}
        new_attending = {p.member_id for p in parts if proposed['attendance'][str(p.id)]}
        eligible = {m.id for m in event.eligible_members_query().all()}
        if any(p.member_id not in eligible and not p.billbro_attending and proposed['attendance'][str(p.id)] for p in parts):
            raise CorrectionError('Neue anwesende Person ist für dieses Event nicht auswählbar.')
        if proposed['paid_by'] == BillPaidBy.MITGLIED.value and proposed['payer'] not in new_attending:
            raise CorrectionError('Auslegende Person muss am Essen teilnehmen.')
        if paid_club_draft:
            if not event.is_paid_by_club or proposed['paid_by'] != BillPaidBy.VEREINSKONTO.value:
                raise CorrectionError('Dieser Entwurf erhält den Vereinszahlweg. Private Ausgleichsfälle bleiben separat.')
            for claim in claims:
                if type(claim.paid_rappen) is not int or claim.paid_rappen < 0:
                    raise CorrectionError('Gespeicherter Zahlungsstand ist ungültig. Zuerst klären.')
                net = claim.net_paid_rappen
                if net < 0:
                    raise CorrectionError('Rueckzahlungen uebersteigen gespeicherte Eingaenge. Zuerst klaeren.')
                expected_status = (ClaimStatus.BEGLICHEN if net >= claim.expected_rappen else
                                   ClaimStatus.TEILWEISE if net else ClaimStatus.OFFEN)
                if claim.status != expected_status:
                    raise CorrectionError('Erlass oder Zahlungsstatus benötigt eine gesonderte Klärung.')
        if not paid_club_draft and any(c.paid_rappen != 0 or c.status != ClaimStatus.OFFEN or c.settled_at is not None for c in claims):
            raise CorrectionError('Zahlungen oder abgeschlossene Posten benötigen den Finanzkorrekturweg.')
        if not paid_club_draft and (BankPaymentAllocation.query.filter(BankPaymentAllocation.claim_id.in_([c.id for c in claims])).first() or Booking.query.filter_by(event_id=event.id).first()):
            raise CorrectionError('Verbuchte Vorgänge benötigen den Finanzkorrekturweg; ihre Historie bleibt erhalten.')
        if not paid_club_draft and (event.is_paid_by_club or proposed['paid_by'] == BillPaidBy.VEREINSKONTO.value or any(c.fiscal_year_id for c in claims)) and any(y.status != FiscalYearStatus.OPEN for y in years):
            raise CorrectionError('Betroffenes Geschäftsjahr ist in Revision oder abgeschlossen. Zuerst mit Grund wieder öffnen.')
        old_shares = {p.member_id: BillBroShareService.stored_share(event, p) for p in parts if p.billbro_attending}
        if any(type(v) is not int or v < 0 for v in old_shares.values()):
            raise CorrectionError('Alte Einzelanteile sind unvollständig. Zuerst klären.')
        old_creditor = event.bill_payer_member_id if event.bill_paid_by == BillPaidBy.MITGLIED else None
        if event.bill_paid_by == BillPaidBy.MITGLIED and old_creditor not in attending:
            raise CorrectionError('Bisherige auslegende Person ist nicht eindeutig. Zuerst klären.')
        expected = {mid: share for mid, share in old_shares.items() if share > 0 and mid != old_creditor} if event.bill_paid_by else {}
        if paid_club_draft:
            # Paid corrections retain zero-valued claims and their payment identities.
            expected.update({c.member_id: 0 for c in claims if c.expected_rappen == 0 and
                             c.member_id in {p.member_id for p in parts} and old_shares.get(c.member_id, 0) == 0})
        if len(claims) != len(expected) or len({c.member_id for c in claims}) != len(claims) or any(
                c.claim_type != ClaimType.ESSENSANTEIL or c.expected_rappen != expected.get(c.member_id) or
                c.creditor_member_id != old_creditor or c.merch_order_id is not None for c in claims):
            raise CorrectionError('Bestehende Forderungen und Anteile stimmen nicht überein. Zuerst klären.')
        if (event.rechnungsbetrag_rappen, event.gesamtbetrag_rappen, event.bill_paid_by.value if event.bill_paid_by else None, old_creditor) == (proposed['invoice'], proposed['total'], proposed['paid_by'], proposed['payer']) and proposed['types'] == {str(p.id): p.esstyp.value if p.esstyp else '' for p in parts if p.billbro_attending} and proposed['attendance'] == {str(p.id): p.billbro_attending for p in parts}:
            raise CorrectionError('Keine Änderung gewählt.')
        try:
            hypothetical = SimpleNamespace(weights_used_json=event.weights_used_json, participations=cls.projected_parts(parts, proposed))
            shares = BillBroShareService.calculate(hypothetical, proposed['total'])
        except ShareError as exc:
            raise CorrectionError(str(exc)) from None
        if cls.ggl_changes(event, parts, proposed):
            try:
                GGLService.project_points(cls.projected_parts(parts, proposed), proposed['invoice'])
            except ValueError as exc:
                raise CorrectionError(str(exc)) from None
        return old_shares, shares

    @classmethod
    def preview(cls, event_id, actor, form):
        event, parts, claims, years, state = cls.load(event_id, actor)
        proposed = cls.proposal(form, event.rechnungsbetrag_rappen, parts)
        old_shares, shares = cls.validate(event, parts, claims, years, proposed)
        token = cls.serializer().dumps(dict(actor=actor.id, generation=actor.auth_generation,
            event=event.id, before=digest(state), proposed=proposed, nonce=uuid4().hex))
        ggl = GGLService.project_points(cls.projected_parts(parts, proposed), proposed['invoice']) if cls.ggl_changes(event, parts, proposed) else None
        return dict(token=token, proposed=proposed, old_invoice=event.rechnungsbetrag_rappen, old_total=event.gesamtbetrag_rappen,
                    ggl_rows=[dict(name=p.member.display_name, before=dict(rank=p.rank, points=p.points, diff_amount_rappen=p.diff_amount_rappen), after=ggl[p.id]) for p in parts] if ggl is not None else [],
                    old_paid_by=event.bill_paid_by.value if event.bill_paid_by else None,
                    old_payer=event.bill_payer_member_id,
                    rows=[dict(id=p.member_id, name=p.member.display_name, before_attending=p.billbro_attending, after_attending=proposed['attendance'][str(p.id)], rsvp=p.teilnahme, before_type=p.esstyp.value if p.esstyp else '–', after_type=proposed['types'].get(str(p.id), p.esstyp.value if p.esstyp else '–'), before=old_shares.get(p.member_id, 0), after=shares.get(p.member_id, 0),
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
            ggl = GGLService.project_points(cls.projected_parts(parts, proposed), proposed['invoice']) if cls.ggl_changes(event, parts, proposed) else None
            for part in parts:
                key = str(part.id)
                old_id = part.id
                if part.id < 0:
                    if not proposed['attendance'][key]:
                        continue
                    part = Participation(event_id=event.id, member_id=part.member_id, teilnahme=None)
                    db.session.add(part)
                part.billbro_attendance = proposed['attendance'][key]
                if part.billbro_attendance:
                    part.esstyp = Esstyp(proposed['types'][key])
                if ggl is not None:
                    for field, value in ggl[old_id].items():
                        setattr(part, field, value)
            db.session.flush()
            db.session.expire(event, ['participations'])
            event.rechnungsbetrag_rappen = proposed['invoice']
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
            if before['event']['bill_paid_by'] == BillPaidBy.MITGLIED.value:
                after['private_unpaid_clarification'] = dict(
                    statement='Organisation erklärt nach Klärung: keine privaten Zahlungen erfolgt.',
                    note=proposed['private_unpaid_note'])
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
