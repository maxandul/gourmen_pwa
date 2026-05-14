"""Öffentlicher iCal-Feed (Token-URL). Phase 5 — docs/capabilities/calendar.md."""

from flask import Blueprint, Response

from backend.models.member import Member
from backend.services.calendar_feed import CalendarFeedService

bp = Blueprint("calendar_feed", __name__)


@bp.route("/calendar/<token>.ics", methods=["GET"])
def member_ical(token):
    """Liefert den persönlichen ICS-Feed; Rate-Limit und ETag siehe späterer Commit."""
    member = Member.query.filter_by(ical_token=token, is_active=True).first()
    if not member or not member.ical_token:
        return ("", 404)
    body = CalendarFeedService.generate_feed_for_member(member)
    return Response(
        body,
        mimetype="text/calendar; charset=utf-8",
    )
