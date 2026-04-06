from datetime import datetime, timedelta, time
from typing import List, Optional, Tuple
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.member import Member


class RetroCleanupService:
    """Bereinigung nur für vergangene Events (Datum vor heute, UTC): fehlende Zu-/Absage
    und/oder fehlende Bewertung. Reihenfolge: jüngstes Datum zuerst (von „heute“ retour).

    Das 30-Tage-Fenster (heute … +30) dient der Dashboard-Kachel „Zu-/Absage“ und
    `get_upcoming_rsvp_prompt_event`, nicht der Cleanup-Seite."""

    UPCOMING_WINDOW_DAYS = 30

    @classmethod
    def _today_start_utc(cls) -> datetime:
        return datetime.combine(datetime.utcnow().date(), time.min)

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
    def _past_events_query(cls, member_join_dt: Optional[datetime] = None):
        today_start = cls._today_start_utc()
        query = Event.query.filter(Event.published == True).filter(Event.datum < today_start)  # noqa: E712
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
    def cleanup_candidate_events(cls, member_id: int) -> List[Event]:
        """Nur vergangene Events (vor heute), neuestes Datum zuerst."""
        join_dt = cls._member_join_date(member_id)
        past = cls._past_events_query(join_dt).all()
        return sorted(past, key=lambda e: e.datum, reverse=True)

    @classmethod
    def list_open_cleanup_events(cls, member_id: int) -> List[Event]:
        """Offene Bereinigungspositionen in derselben Reihenfolge wie cleanup_candidate_events."""
        open_events: List[Event] = []
        for event in cls.cleanup_candidate_events(member_id):
            participation = cls._get_participation(event.id, member_id)
            has_rating = cls._has_rating(event.id, member_id)
            if cls._is_open(event, participation, has_rating, member_id):
                open_events.append(event)
        return open_events

    @classmethod
    def get_upcoming_rsvp_prompt_event(cls, member_id: int) -> Optional[Event]:
        """Nächstes Event im Fenster heute…+30 ohne Zu-/Absage (frühestes Datum zuerst)."""
        join_dt = cls._member_join_date(member_id)
        q = cls._upcoming_events_query(join_dt).order_by(Event.datum.asc())
        for event in q:
            p = cls._get_participation(event.id, member_id)
            if p is None or p.responded_at is None:
                return event
        return None

    @classmethod
    def get_today_billbro_prompt_event(cls, member_id: int) -> Optional[Event]:
        """Heutiges veröffentlichtes Event (UTC-Kalendertag): BillBro-Link sinnvoll für Organisator
        oder Teilnehmer mit Zusage. Reihenfolge: frühestes ``datum`` zuerst."""
        join_dt = cls._member_join_date(member_id)
        today_utc = datetime.utcnow().date()
        day_start = datetime.combine(today_utc, time.min)
        day_end = day_start + timedelta(days=1)

        q = (
            Event.query.filter(Event.published == True)  # noqa: E712
            .filter(Event.datum >= day_start)
            .filter(Event.datum < day_end)
        )
        if join_dt:
            q = q.filter(Event.datum >= join_dt)
        events = q.order_by(Event.datum.asc()).all()
        for event in events:
            if event.organisator_id == member_id:
                return event
            p = cls._get_participation(event.id, member_id)
            if p and p.teilnahme:
                return event
        return None

    @staticmethod
    def _get_participation(event_id: int, member_id: int):
        return Participation.query.filter_by(event_id=event_id, member_id=member_id).first()

    @staticmethod
    def _has_rating(event_id: int, member_id: int) -> bool:
        return EventRating.query.filter_by(event_id=event_id, participant_id=member_id).first() is not None

    @classmethod
    def _is_completed(cls, event, participation, has_rating: bool, member_id: int) -> bool:
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
        events = cls.cleanup_candidate_events(member_id)
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
    def allows_cleanup_rsvp(cls, event) -> bool:
        """POST cleanup/rsvp: nur für vergangene Events (Cleanup-Seite)."""
        return event.datum < cls._today_start_utc()
