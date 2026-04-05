"""Shared logic: when to show the „rate last completed event“ prompt."""

from datetime import datetime

from backend.models.event import Event


def get_rating_prompt_event_for_member(member) -> Event | None:
    """
    Same rules as the former Events-index hint: the single most recent past
    published event, if the member participated (zugesagt), ratings allowed,
    and they have not rated yet.
    """
    now = datetime.utcnow()
    last_completed = (
        Event.query.filter(Event.published == True, Event.datum < now)
        .order_by(Event.datum.desc())
        .first()
    )
    if not last_completed:
        return None
    last_completed.participations
    user_p = next(
        (p for p in (last_completed.participations or []) if p.member_id == member.id),
        None,
    )
    if (
        last_completed.allow_ratings
        and user_p
        and user_p.teilnahme
        and not last_completed.has_rating_from_participant(member.id)
    ):
        return last_completed
    return None
