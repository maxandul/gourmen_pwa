"""Delete only simple future events in one audited transaction."""
from datetime import datetime
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.document import Document
from backend.models.accounting import Booking, MemberClaim, Receipt
from backend.models.audit_event import AuditEvent, AuditAction


class EventDeletionError(ValueError):
    pass


class EventDeletionService:
    @staticmethod
    def delete(event_id, actor):
        try:
            event = Event.query.filter_by(id=event_id).populate_existing().with_for_update().first()
            if not actor or not actor.is_active or not actor.is_admin() or not event or not event.is_visible_to(actor):
                raise EventDeletionError('Eventlöschung nicht erlaubt.')
            if event.datum.date() < datetime.utcnow().date():
                raise EventDeletionError('Vergangene Events können nicht gelöscht werden.')
            participants = Participation.query.filter_by(event_id=event.id).order_by(Participation.id).populate_existing().with_for_update().all()
            relations = ((EventRating, 'event_id'), (Document, 'event_id'), (Booking, 'event_id'),
                         (MemberClaim, 'event_id'), (Receipt, 'suggested_event_id'))
            if any(model.query.filter(getattr(model, field) == event.id).first() for model, field in relations):
                raise EventDeletionError('Event bleibt erhalten: Bewertungen, Dokumente, Belege oder Buchhaltungsdaten sind verknüpft.')
            event_fields = ('rechnungsbetrag_rappen', 'gesamtbetrag_rappen', 'trinkgeld_rappen',
                            'betrag_sparsam_rappen', 'betrag_normal_rappen', 'betrag_allin_rappen', 'bill_paid_by', 'bill_payer_member_id')
            participation_fields = ('esstyp', 'guess_bill_amount_rappen', 'diff_amount_rappen', 'rank', 'points', 'calculated_share_rappen')
            if event.billbro_closed or any(getattr(event, field) is not None for field in event_fields) or any(
                    getattr(p, field) is not None for p in participants for field in participation_fields):
                raise EventDeletionError('Event bleibt erhalten: BillBro- oder GGL-Daten benötigen einen eigenen Korrekturablauf.')
            db.session.add(AuditEvent(actor_id=actor.id, action=AuditAction.EVENT_DELETE, entity='event', entity_id=event.id,
                extra_json={'event_date': event.datum.isoformat(), 'participation_count': len(participants)}))
            for participation in participants:
                db.session.delete(participation)
            db.session.delete(event)
            db.session.commit()
        except EventDeletionError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise EventDeletionError('Event wurde nicht gelöscht. Ausgangszustand bleibt erhalten.') from None
