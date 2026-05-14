"""iCal calendar feed per member (Phase 5, docs/capabilities/calendar.md)."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app
from icalendar import Calendar, Event as ICalEvent
from icalendar import Timezone, TimezoneDaylight, TimezoneStandard
from sqlalchemy.orm import joinedload

from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.member import Member

logger = logging.getLogger(__name__)

ZURICH = ZoneInfo("Europe/Zurich")


class CalendarFeedService:
    """RFC 5545 feed generation and iCal SEQUENCE / token lifecycle."""

    RELEVANT_FIELDS = frozenset(
        {
            "datum",
            "event_typ",
            "restaurant",
            "place_name",
            "place_address",
            "organisator_id",
            "published",
        }
    )

    _EMOJI_BY_TYPE = {
        EventType.MONATSESSEN: "\U0001f374",  # 🍴
        EventType.AUSFLUG: "\U0001f690",  # 🚐
        EventType.GENERALVERSAMMLUNG: "\U0001f3db\ufe0f",  # 🏛️
    }

    @classmethod
    def feed_body_etag(cls, body: bytes) -> str:
        digest = hashlib.sha256(body).hexdigest()
        return f'"{digest}"'

    @classmethod
    def _public_base_url(cls) -> str:
        return (
            current_app.config.get("PUBLIC_APP_BASE_URL", "https://gourmen.ch").rstrip(
                "/"
            )
        )

    @classmethod
    def feed_url_for_token(cls, token: str) -> str:
        return f"{cls._public_base_url()}/calendar/{token}.ics"

    @classmethod
    def webcal_url_for_token(cls, token: str) -> str:
        base_https = cls._public_base_url()
        if base_https.startswith("https://"):
            rest = base_https[len("https://") :]
            return f"webcal://{rest}/calendar/{token}.ics"
        if base_https.startswith("http://"):
            rest = base_https[len("http://") :]
            return f"webcal://{rest}/calendar/{token}.ics"
        return f"webcal://{base_https}/calendar/{token}.ics"

    @classmethod
    def event_detail_url(cls, event_id: int) -> str:
        return f"{cls._public_base_url()}/events/{event_id}"

    @classmethod
    def _generate_unique_token(cls) -> str:
        while True:
            candidate = secrets.token_urlsafe(32)
            if len(candidate) > 64:
                continue
            exists = Member.query.filter(Member.ical_token == candidate).first()
            if not exists:
                return candidate

    @classmethod
    def enable_feed_for_member(cls, member: Member) -> str:
        member.ical_token = cls._generate_unique_token()
        return cls.feed_url_for_token(member.ical_token)

    @classmethod
    def regenerate_token_for_member(cls, member: Member) -> str:
        member.ical_token = cls._generate_unique_token()
        return cls.feed_url_for_token(member.ical_token)

    @classmethod
    def disable_feed_for_member(cls, member: Member) -> None:
        member.ical_token = None

    @staticmethod
    def calendar_relevant_state(event: Event) -> dict:
        raw = event.datum
        if raw is None:
            d = None
        elif isinstance(raw, datetime):
            d = raw.date()
        elif isinstance(raw, date):
            d = raw
        else:
            d = raw
        et = (
            event.event_typ.value
            if event.event_typ and hasattr(event.event_typ, "value")
            else event.event_typ
        )
        return {
            "datum": d,
            "event_typ": et,
            "restaurant": event.restaurant,
            "place_name": event.place_name,
            "place_address": event.place_address,
            "organisator_id": event.organisator_id,
            "published": bool(event.published),
        }

    @classmethod
    def bump_sequence_if_changed(
        cls, event: Event, before: dict, after: dict
    ) -> None:
        for key in cls.RELEVANT_FIELDS:
            if before.get(key) != after.get(key):
                prev = event.ical_sequence
                if prev is None:
                    prev = 0
                event.ical_sequence = int(prev) + 1
                return

    @classmethod
    def _today_zurich(cls) -> date:
        return datetime.now(ZURICH).date()

    @classmethod
    def _format_summary(cls, event: Event) -> str:
        emoji = cls._EMOJI_BY_TYPE.get(event.event_typ, "\U0001f4c5")
        name = (event.place_name or event.restaurant or "").strip()
        if name:
            return f"{emoji} Gourmen - {name}"
        return f"{emoji} Gourmen"

    @classmethod
    def _format_location(cls, event: Event) -> str:
        parts = []
        name = event.place_name or event.restaurant
        if name:
            parts.append(name)
        if event.place_address:
            parts.append(event.place_address)
        return ", ".join(parts)

    @classmethod
    def _format_description(cls, event: Event) -> str:
        detail = cls.event_detail_url(event.id)
        notes = (event.notizen or "").strip()
        if notes:
            return f"{notes}\n\nDetails: {detail}"
        return f"Details: {detail}"

    @classmethod
    def _organizer_cn(cls, event: Event) -> str:
        org = event.organisator
        if org:
            return org.display_spirit_rufname
        return "Gourmen"

    @classmethod
    def _build_vtimezone(cls) -> Timezone:
        tz = Timezone()
        tz.add("TZID", "Europe/Zurich")
        std = TimezoneStandard()
        std.add("DTSTART", datetime(1970, 10, 25, 3, 0, 0))
        std.add("TZOFFSETFROM", timedelta(hours=2))
        std.add("TZOFFSETTO", timedelta(hours=1))
        std.add("RRULE", {"FREQ": "YEARLY", "BYDAY": "-1SU", "BYMONTH": 10})
        std.add("TZNAME", "CET")
        tz.add_component(std)
        dst = TimezoneDaylight()
        dst.add("DTSTART", datetime(1970, 3, 29, 2, 0, 0))
        dst.add("TZOFFSETFROM", timedelta(hours=1))
        dst.add("TZOFFSETTO", timedelta(hours=2))
        dst.add("RRULE", {"FREQ": "YEARLY", "BYDAY": "-1SU", "BYMONTH": 3})
        dst.add("TZNAME", "CEST")
        tz.add_component(dst)
        return tz

    @classmethod
    def _build_vevent(cls, event: Event, now_utc: datetime) -> ICalEvent:
        raw_d = event.datum
        if isinstance(raw_d, datetime):
            day = raw_d.date()
        elif isinstance(raw_d, date):
            day = raw_d
        else:
            day = None
        if not day:
            raise ValueError("Event ohne Datum")

        start = datetime.combine(day, datetime.min.time().replace(hour=18), tzinfo=ZURICH)
        end = datetime.combine(day, datetime.min.time().replace(hour=23), tzinfo=ZURICH)

        ve = ICalEvent()
        ve.add("uid", f"event-{event.id}@gourmen.ch")
        seq = event.ical_sequence if event.ical_sequence is not None else 0
        ve.add("sequence", int(seq))
        ve.add("dtstamp", now_utc)
        modified = event.updated_at or event.created_at or now_utc
        if modified.tzinfo is None:
            modified = modified.replace(tzinfo=timezone.utc)
        else:
            modified = modified.astimezone(timezone.utc)
        ve.add("last-modified", modified)
        ve.add("summary", cls._format_summary(event))
        ve.add("dtstart", start)
        ve.add("dtend", end)
        loc = cls._format_location(event)
        if loc:
            ve.add("location", loc)
        ve.add("description", cls._format_description(event))
        ve.add("url", cls.event_detail_url(event.id))
        et = (
            event.event_typ.value
            if event.event_typ and hasattr(event.event_typ, "value")
            else str(event.event_typ)
        )
        ve.add("categories", et)
        cn = cls._organizer_cn(event)
        mailto = current_app.config.get("MAIL_FROM_ADDRESS", "kontakt@gourmen.ch")
        ve.add(
            "organizer",
            f"mailto:{mailto}",
            parameters={"CN": cn},
        )
        return ve

    @classmethod
    def _build_calendar_shell(cls) -> Calendar:
        cal = Calendar()
        cal.add("prodid", "-//Gourmen Verein//PWA Calendar Feed//DE")
        cal.add("version", "2.0")
        cal.add("method", "PUBLISH")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", "Gourmen Vereinstermine")
        cal.add("x-wr-timezone", "Europe/Zurich")
        cal.add(
            "x-wr-caldesc",
            "Veröffentlichte Termine des Gourmen Vereins.",
        )
        cal.add_component(cls._build_vtimezone())
        return cal

    @classmethod
    def generate_feed_for_member(cls, member: Member) -> bytes:
        today = cls._today_zurich()
        now_utc = datetime.now(timezone.utc)
        rows = (
            Event.query.options(joinedload(Event.organisator))
            .filter(
                Event.published == True,  # noqa: E712
            )
            .order_by(Event.datum.asc())
            .all()
        )
        def _cal_day(ev: Event) -> date | None:
            raw = ev.datum
            if raw is None:
                return None
            if isinstance(raw, datetime):
                return raw.date()
            if isinstance(raw, date):
                return raw
            return None

        events = [e for e in rows if (cd := _cal_day(e)) is not None and cd >= today]
        cal = cls._build_calendar_shell()
        for ev in events:
            try:
                cal.add_component(cls._build_vevent(ev, now_utc))
            except Exception as e:
                logger.warning("Kalender-VEVENT übersprungen event_id=%s: %s", ev.id, e)
        return cal.to_ical()
