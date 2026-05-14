"""Öffentlicher iCal-Feed (Token-URL). Phase 5 — docs/capabilities/calendar.md."""

from flask import Blueprint, Response, request

from backend.extensions import limiter
from backend.models.member import Member
from backend.services.calendar_feed import CalendarFeedService

bp = Blueprint("calendar_feed", __name__)


def _calendar_feed_rate_limit_key() -> str:
    return request.view_args.get("token") or ""


@bp.route("/calendar/<token>.ics", methods=["GET"])
@limiter.limit(
    "60 per minute",
    key_func=_calendar_feed_rate_limit_key,
    methods=["GET"],
    override_defaults=True,
)
def member_ical(token):
    """Cache-Control private + ETag; 304 bei If-None-Match."""
    member = Member.query.filter_by(ical_token=token, is_active=True).first()
    if not member or not member.ical_token:
        return ("", 404)
    body = CalendarFeedService.generate_feed_for_member(member)
    etag = CalendarFeedService.feed_body_etag(body)
    inm = (request.headers.get("If-None-Match") or "").strip()
    if inm and inm == etag:
        resp = Response(status=304)
        resp.headers["Cache-Control"] = "private, max-age=300"
        resp.headers["ETag"] = etag
        return resp
    resp = Response(body, mimetype="text/calendar; charset=utf-8")
    resp.headers["Cache-Control"] = "private, max-age=300"
    resp.headers["ETag"] = etag
    return resp