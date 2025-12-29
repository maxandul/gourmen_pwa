from datetime import datetime, timedelta
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.rating import EventRating


class RetroCleanupService:
    """Hilfsfunktionen für den Datenbereinigungs-Flow vergangener Events."""

    CUTOFF_DAYS = 7

    @classmethod
    def cutoff_date(cls) -> datetime:
        return datetime.utcnow() - timedelta(days=cls.CUTOFF_DAYS)

    @classmethod
    def _eligible_events_query(cls):
        cutoff = cls.cutoff_date()
        return (
            Event.query
            .filter(Event.datum <= cutoff)
            .filter(Event.published == True)  # noqa: E712
            .order_by(Event.datum.asc())
        )

    @staticmethod
    def _get_participation(event_id: int, member_id: int):
        return Participation.query.filter_by(event_id=event_id, member_id=member_id).first()

    @staticmethod
    def _has_rating(event_id: int, member_id: int) -> bool:
        return EventRating.query.filter_by(event_id=event_id, participant_id=member_id).first() is not None

    @staticmethod
    def _is_completed(event, participation, has_rating: bool, member_id: int) -> bool:
        """Erledigt wenn Zu-/Absage gesetzt und falls Rating erlaubt + Zusage (oder Org) auch bewertet."""
        if not participation or not participation.responded_at:
            return False

        if not getattr(event, 'allow_ratings', True):
            return True

        # Organisator darf bewerten; Pflicht nur wenn zugesagt
        if participation.teilnahme:
            return has_rating

        # Bei Absage ist nichts weiter nötig
        return True

    @staticmethod
    def _is_open(event, participation, has_rating: bool, member_id: int) -> bool:
        """Offen wenn keine Antwort oder bei Zusage (oder Org) noch ohne Rating (falls erlaubt)."""
        if participation is None or participation.responded_at is None:
            return True

        if getattr(event, 'allow_ratings', True) and participation.teilnahme and not has_rating:
            return True

        return False

    @classmethod
    def get_progress(cls, member_id: int) -> dict:
        events = cls._eligible_events_query().all()
        total = len(events)
        completed = 0

        for event in events:
            participation = cls._get_participation(event.id, member_id)
            has_rating = cls._has_rating(event.id, member_id)

            if cls._is_completed(event, participation, has_rating, member_id):
                completed += 1

        pending = total - completed
        return {
            'total': total,
            'completed': completed,
            'pending': pending
        }

    @classmethod
    def get_next_open_event(cls, member_id: int):
        """Liefert das älteste offene Event plus Statusdaten."""
        events = cls._eligible_events_query().all()
        progress = cls.get_progress(member_id)

        for event in events:
            participation = cls._get_participation(event.id, member_id)
            has_rating = cls._has_rating(event.id, member_id)
            if cls._is_open(event, participation, has_rating, member_id):
                return {
                    'event': event,
                    'participation': participation,
                    'has_rating': has_rating,
                    'progress': progress
                }

        return {
            'event': None,
            'participation': None,
            'has_rating': False,
            'progress': progress
        }

