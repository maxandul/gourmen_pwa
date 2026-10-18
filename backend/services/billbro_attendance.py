"""Actual attendance changes preserve the original RSVP and saved inputs."""
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation
from backend.services.area_permissions import AreaPermissionService
from backend.services.billbro_state import BillBroStateService
from backend.services.ggl_rules import GGLService


class AttendanceError(ValueError):
    pass


class BillBroAttendanceService:
    @staticmethod
    def mark(event_id, member_id, actor, attending):
        try:
            event = Event.query.filter_by(id=event_id).populate_existing().with_for_update().first()
            if not event or not event.is_visible_to(actor) or not AreaPermissionService.can_manage_event(actor, event):
                raise AttendanceError('Keine Berechtigung für diese Anwesenheit.')
            if BillBroStateService.requires_correction(event):
                raise AttendanceError('Abschluss vorhanden. Anwesenheit mit Vorschau korrigieren.')
            part = Participation.query.filter_by(event_id=event_id, member_id=member_id).populate_existing().with_for_update().first()
            eligible = event.eligible_members_query().filter_by(id=member_id).first()
            if not eligible and (attending or not part):
                raise AttendanceError('Mitglied ist für dieses Event nicht auswählbar.')
            if part is None:
                part = Participation(event_id=event_id, member_id=member_id, teilnahme=None)
                db.session.add(part)
            part.billbro_attendance = attending
            db.session.flush()
            if event.supports_ggl and event.rechnungsbetrag_rappen:
                parts = Participation.query.filter_by(event_id=event_id).all()
                projected = GGLService.project_points(parts, event.rechnungsbetrag_rappen)
                for row in parts:
                    for field, value in projected[row.id].items():
                        setattr(row, field, value)
            elif not attending:
                part.diff_amount_rappen = part.rank = part.points = None
            db.session.commit()
        except AttendanceError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise AttendanceError('Anwesenheit konnte nicht gespeichert werden. Angaben bleiben erhalten.') from None
