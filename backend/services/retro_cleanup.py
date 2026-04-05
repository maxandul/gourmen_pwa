from datetime import datetime, timedelta, time
from typing import List, Optional, Tuple
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.member import Member


class RetroCleanupService:
    """Datenbereinigung: kommende Events (Fenster heute … +30 Tage) nur Zu-/Absage;
    vergangene Events (ab CUTOFF_DAYS nach Eventdatum) zusätzlich Bewertung.
    Reihenfolge: jüngstes Datum zuerst (nächstes Event oben)."""

    CUTOFF_DAYS = 7
    UPCOMING_WINDOW_DAYS = 30

    @classmethod
    def cutoff_date(cls) -> datetime:
        return datetime.utcnow() - timedelta(days=cls.CUTOFF_DAYS)

    @classmethod
    def _member_join_date(cls, member_id: int):
        member = Member.query.get(member_id)
        if not member or not member.beitritt:
            return None
        return datetime.combine(member.beitritt, time.min)

    @classmethod
    def _upcoming_window_bounds(cls) -> Tuple[datetime, datetime]:
        now = datetime.utcnow()
        today = now.date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today + timedelta(days=cls.UPCOMING_WINDOW_DAYS), time.max)
        return start, end

    @classmethod
    def _is_upcoming_scope(cls, event) -> bool:
        start, end = cls._upcoming_window_bounds()
        return start <= event.datum <= end

    @classmethod
    def _eligible_past_events_query(cls, member_join_dt: Optional[datetime] = None):
        cutoff = cls.cutoff_date()
        query = (
            Event.query.filter(Event.datum <= cutoff).filter(Event.published == True)  # noqa: E712
        )
        if member_join_dt:
            query = query.filter(Event.datum >= member_join_dt)
        return query

    @classmethod
    def _upcoming_events_query(cls, member_join_dt: Optional[datetime] = None):
        start, end = cls._upcoming_window_bounds()
        query = (
            Event.query.filter(Event.published == True)  # noqa: E712
            .filter(Event.datum >= start)
            .filter(Event.datum <= end)
        )
        if member_join_dt:
            query = query.filter(Event.datum >= member_join_dt)
        return query

    @classmethod
    def merged_candidate_events(cls, member_id: int) -> List[Event]:
        join_dt = cls._member_join_date(member_id)
        past = cls._eligible_past_events_query(join_dt).all()
        upcoming = cls._upcoming_events_query(join_dt).all()
        by_id = {e.id: e for e in past}
        for e in upcoming:
            by_id[e.id] = e
        return sorted(by_id.values(), key=lambda e: e.datum, reverse=True)

    @staticmethod
    def _get_participation(event_id: int, member_id: int):
        return Participation.query.filter_by(event_id=event_id, member_id=member_id).first()

    @staticmethod
    def _has_rating(event_id: int, member_id: int) -> bool:
        return EventRating.query.filter_by(event_id=event_id, participant_id=member_id).first() is not None

    @classmethod
    def _is_completed(cls, event, participation, has_rating: bool, member_id: int) -> bool:
        if cls._is_upcoming_scope(event):
            return participation is not None and participation.responded_at is not None

        if not participation or not participation.responded_at:
            return False

        if not getattr(event, "allow_ratings", True):
            return True

        if participation.teilnahme:
            return has_rating

        return True

    @classmethod
    def _is_open(cls, event, participation, has_rating: bool, member_id: int) -> bool:
        return not cls._is_completed(event, participation, has_rating, member_id)

    @classmethod
    def get_progress(cls, member_id: int) -> dict:
        events = cls.merged_candidate_events(member_id)
        total = len(events)
        completed = 0

        for event in events:
            participation = cls._get_participation(event.id, member_id)
            has_rating = cls._has_rating(event.id, member_id)

            if cls._is_completed(event, participation, has_rating, member_id):
                completed += 1

        pending = total - completed
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
        }

    @classmethod
    def get_next_open_event(cls, member_id: int):
        """Liefert das offene Event mit dem jüngsten Datum zuerst."""
        events = cls.merged_candidate_events(member_id)
        progress = cls.get_progress(member_id)

        for event in events:
            participation = cls._get_participation(event.id, member_id)
            has_rating = cls._has_rating(event.id, member_id)
            if cls._is_open(event, participation, has_rating, member_id):
                return {
                    "event": event,
                    "participation": participation,
                    "has_rating": has_rating,
                    "progress": progress,
                }

        return {
            "event": None,
            "participation": None,
            "has_rating": False,
            "progress": progress,
        }

    @classmethod
    def allows_cleanup_rsvp(cls, event) -> bool:
        """POST cleanup/rsvp: kommendes Fenster oder vergangenes Event in der Retro-Queue."""
        if cls._is_upcoming_scope(event):
            return True
        if event.datum <= cls.cutoff_date():
            return True
        return False
