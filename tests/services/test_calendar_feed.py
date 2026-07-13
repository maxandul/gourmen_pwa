"""Tests für iCal CalendarFeedService (RFC 5545 / icalendar)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from icalendar import Calendar as ICalCalendar
from werkzeug.security import generate_password_hash

import backend.models  # noqa: F401
from backend.app import create_app
from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.member import Member
from backend.services.calendar_feed import CalendarFeedService


@pytest.fixture
def app_ctx(app):
    """Konkreter Organisator + veröffentlichtes Zukunfts-Event."""
    with app.app_context():
        m = Member(
            vorname="Alex",
            nachname="Test",
            email="cal-feed-org@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            spirit_animal="\U0001f43a",
            rufname="Andreas",
        )
        db.session.add(m)
        db.session.flush()
        future = date.today() + timedelta(days=30)
        ev = Event(
            organisator_id=m.id,
            datum=datetime.combine(future, datetime.min.time().replace(hour=12)),
            event_typ=EventType.MONATSESSEN,
            season=future.year,
            restaurant="Da Marco",
            place_name="Da Marco",
            place_address="Bahnhofstrasse 12, 8001 Z\u00fcrich",
            notizen="Reservierung 19:30",
            published=True,
            ical_sequence=2,
        )
        db.session.add(ev)
        db.session.commit()
        yield app, m.id, ev.id


def _walk_vevents(ical_bytes: bytes):
    cal = ICalCalendar.from_ical(ical_bytes)
    out = []
    for c in cal.walk():
        if c.name == "VEVENT":
            out.append(c)
    return cal, out


def test_feed_parses_and_has_vtimezone_and_vevent_properties(app_ctx):
    app, mid, eid = app_ctx
    with app.app_context():
        member = Member.query.get(mid)
        body = CalendarFeedService.generate_feed_for_member(member)
    cal, vevents = _walk_vevents(body)
    tzids = [c.get("TZID") for c in cal.walk() if c.name == "VTIMEZONE"]
    assert "Europe/Zurich" in tzids
    assert len(vevents) >= 1
    ve = vevents[0]
    assert str(ve["UID"]).startswith(f"event-{eid}@gourmen.ch")
    assert int(ve["SEQUENCE"]) == 2
    summary = str(ve["SUMMARY"])
    assert summary.startswith("\U0001f374 Gourmen - Da Marco")
    assert "STATUS" not in ve
    assert "VALARM" not in [x.name for x in ve.subcomponents]
    assert "ATTENDEE" not in ve
    org = ve["ORGANIZER"]
    assert "mailto:" in str(org).lower()
    params = org.params
    assert "CN" in params
    assert "Wolf" in params["CN"] or "Andreas" in params["CN"] or "\U0001f43a" in params["CN"]
    loc = str(ve["LOCATION"])
    assert "Da Marco" in loc
    assert "8001" in loc
    desc = str(ve["DESCRIPTION"])
    assert "Organisator:" in desc
    assert "Andreas" in desc or "\U0001f43a" in desc
    assert "Details:" in desc
    assert f"/events/{eid}" in desc
    assert "Reservierung" in desc
    cats = ve["CATEGORIES"]
    assert "MONATSESSEN" in str(cats)


def test_feed_dtstart_dtend_zurich_evening(app_ctx):
    app, mid, eid = app_ctx
    with app.app_context():
        ev = Event.query.get(eid)
        day = ev.datum.date()
        member = Member.query.get(mid)
        body = CalendarFeedService.generate_feed_for_member(member)
    _, vevents = _walk_vevents(body)
    ve = vevents[0]
    dtstart = ve["DTSTART"].dt
    dtend = ve["DTEND"].dt
    assert dtstart.hour == 18 and dtstart.minute == 0
    assert dtend.hour == 23 and dtend.minute == 0
    assert dtstart.date() == day and dtend.date() == day
    assert str(ve["DTSTART"].params.get("TZID", "")) == "Europe/Zurich"


def test_location_omitted_when_empty(app):
    with app.app_context():
        m = Member(
            vorname="O",
            nachname="R",
            email="cal-noloc@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
        )
        db.session.add(m)
        db.session.flush()
        future = date.today() + timedelta(days=40)
        ev = Event(
            organisator_id=m.id,
            datum=datetime.combine(future, datetime.min.time()),
            event_typ=EventType.AUSFLUG,
            season=future.year,
            restaurant=None,
            place_name=None,
            place_address=None,
            published=True,
        )
        db.session.add(ev)
        db.session.commit()
        body = CalendarFeedService.generate_feed_for_member(m)
    _, vevents = _walk_vevents(body)
    ve = vevents[0]
    assert "LOCATION" not in ve


def test_bump_sequence_on_datum_change(app):
    with app.app_context():
        m = Member(
            vorname="B",
            nachname="ump",
            email="bump@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
        )
        db.session.add(m)
        db.session.flush()
        d0 = date.today() + timedelta(days=50)
        ev = Event(
            organisator_id=m.id,
            datum=datetime.combine(d0, datetime.min.time()),
            event_typ=EventType.MONATSESSEN,
            season=d0.year,
            restaurant="R",
            published=True,
            ical_sequence=0,
        )
        db.session.add(ev)
        db.session.commit()
        before = CalendarFeedService.calendar_relevant_state(ev)
        ev.datum = ev.datum + timedelta(days=1)
        after = CalendarFeedService.calendar_relevant_state(ev)
        CalendarFeedService.bump_sequence_if_changed(ev, before, after)
        assert ev.ical_sequence == 1
        after_same = CalendarFeedService.calendar_relevant_state(ev)
        CalendarFeedService.bump_sequence_if_changed(ev, after_same, after_same)
        assert ev.ical_sequence == 1


def test_etag_is_stable_hash(app_ctx):
    app, mid, _eid = app_ctx
    with app.app_context():
        member = Member.query.get(mid)
        b1 = CalendarFeedService.generate_feed_for_member(member)
        b2 = CalendarFeedService.generate_feed_for_member(member)
    assert CalendarFeedService.feed_body_etag(b1) == CalendarFeedService.feed_body_etag(b2)
    assert len(CalendarFeedService.feed_body_etag(b1)) > 32


def test_past_events_not_listed(app):
    with app.app_context():
        m = Member(
            vorname="P",
            nachname="ast",
            email="past-ev@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
        )
        db.session.add(m)
        db.session.flush()
        past = date.today() - timedelta(days=5)
        ev = Event(
            organisator_id=m.id,
            datum=datetime.combine(past, datetime.min.time()),
            event_typ=EventType.MONATSESSEN,
            season=past.year,
            restaurant="Alt",
            published=True,
        )
        db.session.add(ev)
        db.session.commit()
        body = CalendarFeedService.generate_feed_for_member(m)
    _, vevents = _walk_vevents(body)
    assert len(vevents) == 0


def test_board_events_hidden_from_non_board_feed(app):
    with app.app_context():
        from backend.models.event import EventAudience

        org = Member(
            vorname="Org",
            nachname="Board",
            email="cal-board-org@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            vorstandsmitglied=True,
        )
        member = Member(
            vorname="Mem",
            nachname="Ber",
            email="cal-board-member@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            vorstandsmitglied=False,
        )
        db.session.add_all([org, member])
        db.session.flush()
        future = date.today() + timedelta(days=20)
        board_ev = Event(
            organisator_id=org.id,
            datum=datetime.combine(future, datetime.min.time().replace(hour=12)),
            event_typ=EventType.VORSTANDSSITZUNG,
            audience=EventAudience.BOARD,
            season=future.year,
            restaurant="Vereinslokal",
            published=True,
        )
        public_ev = Event(
            organisator_id=org.id,
            datum=datetime.combine(future + timedelta(days=1), datetime.min.time().replace(hour=12)),
            event_typ=EventType.MONATSESSEN,
            audience=EventAudience.ALL,
            season=future.year,
            restaurant="Da Marco",
            published=True,
        )
        db.session.add_all([board_ev, public_ev])
        db.session.commit()

        member_body = CalendarFeedService.generate_feed_for_member(member)
        board_body = CalendarFeedService.generate_feed_for_member(org)

    _, member_events = _walk_vevents(member_body)
    _, board_events = _walk_vevents(board_body)
    member_summaries = [str(ve["SUMMARY"]) for ve in member_events]
    board_summaries = [str(ve["SUMMARY"]) for ve in board_events]
    assert any("Da Marco" in s for s in member_summaries)
    assert not any("Vereinslokal" in s for s in member_summaries)
    assert any("Vereinslokal" in s for s in board_summaries)
    assert any("\U0001f4cb" in s for s in board_summaries)