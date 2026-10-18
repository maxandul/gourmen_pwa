"""Undo only the unchanged result of a simple cleanup RSVP."""
import hashlib
import json
from datetime import datetime
from enum import Enum
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.accounting import MemberClaim, Booking
from backend.services.retro_cleanup import RetroCleanupService


class CleanupConflict(ValueError):
    pass


class CleanupFailure(RuntimeError):
    pass


class CleanupParticipationService:
    @staticmethod
    def lock(event_id, member):
        event = Event.query.filter_by(id=event_id).populate_existing().with_for_update().first()
        if not member or not member.is_active or not event or not event.is_visible_to(member) or not RetroCleanupService.allows_cleanup_rsvp(event):
            raise CleanupConflict('Event ist nicht mehr zur Bereinigung verfügbar.')
        row = Participation.query.filter_by(event_id=event.id, member_id=member.id).populate_existing().with_for_update().first()
        return event, row

    @staticmethod
    def fingerprint(event, row):
        def value(raw):
            if isinstance(raw, Enum):return raw.value
            if isinstance(raw, datetime):return raw.isoformat()
            return raw
        state = {name: {column.name: value(getattr(obj, column.name)) for column in obj.__table__.columns}
                 for name, obj in [('event', event), ('participation', row)]}
        return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()

    @staticmethod
    def protected(event, row, member_id):
        event_fields = ('rechnungsbetrag_rappen', 'gesamtbetrag_rappen', 'trinkgeld_rappen', 'bill_paid_by')
        row_fields = ('billbro_attendance', 'esstyp', 'guess_bill_amount_rappen', 'diff_amount_rappen', 'rank', 'points', 'calculated_share_rappen')
        return (event.billbro_closed or any(getattr(event, field) is not None for field in event_fields)
            or (row and any(getattr(row, field) is not None for field in row_fields))
            or EventRating.query.filter_by(event_id=event.id, participant_id=member_id).first()
            or MemberClaim.query.filter_by(event_id=event.id).first()
            or Booking.query.filter_by(event_id=event.id).first())

    @classmethod
    def apply(cls, event_id, member, status):
        try:
            if status not in ('yes', 'no'):raise CleanupConflict('Ungültige Auswahl.')
            event, row = cls.lock(event_id, member)
            if cls.protected(event, row, member.id):
                raise CleanupConflict('Fachwerte vorhanden. Teilnahme über den zuständigen Korrekturablauf klären.')
            previous = {'had_row': bool(row)}
            if row:
                previous.update(teilnahme=row.teilnahme, responded_at=row.responded_at.isoformat() if row.responded_at else None)
            else:
                row = Participation(member_id=member.id, event_id=event.id, teilnahme=status == 'yes')
                db.session.add(row)
            row.teilnahme = status == 'yes'
            row.responded_at = datetime.utcnow()
            db.session.flush()
            payload = dict(member_id=member.id, event_id=event.id, prev=previous, after=cls.fingerprint(event, row))
            db.session.commit()
            return payload
        except CleanupConflict:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise CleanupFailure('Bereinigung nicht gespeichert. Bitte erneut versuchen.') from None

    @classmethod
    def undo(cls, payload, member):
        try:
            if not isinstance(payload, dict) or payload.get('member_id') != member.id or not payload.get('after'):
                raise CleanupConflict('Dieser Rückgängig-Nachweis ist nicht mehr gültig.')
            event, row = cls.lock(payload.get('event_id'), member)
            if not row or cls.protected(event, row, member.id) or cls.fingerprint(event, row) != payload['after']:
                raise CleanupConflict('Stand wurde inzwischen geändert. Rückgängig nicht möglich; alle aktuellen Daten bleiben erhalten.')
            previous = payload['prev']
            if not previous['had_row']:
                db.session.delete(row)
            else:
                row.teilnahme = previous['teilnahme']
                row.responded_at = datetime.fromisoformat(previous['responded_at']) if previous.get('responded_at') else None
            db.session.commit()
            return event.id
        except CleanupConflict:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise CleanupFailure('Rückgängig nicht gespeichert. Aktueller Stand bleibt erhalten; bitte erneut versuchen.') from None
