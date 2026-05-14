"""HTTP-Tests: iCal-Feed ETag/304 und Rate-Limit."""

from __future__ import annotations

import pytest
from werkzeug.security import generate_password_hash

import backend.config as app_config
import backend.models  # noqa: F401
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.services.calendar_feed import CalendarFeedService


@pytest.fixture
def app_rl(monkeypatch):
    monkeypatch.setattr(app_config.TestingConfig, "RATELIMIT_ENABLED", True)
    monkeypatch.setattr(app_config.TestingConfig, "REDIS_URL", None)
    return create_app("testing")


@pytest.fixture
def client_rl(app_rl):
    with app_rl.app_context():
        db.create_all()
    yield app_rl.test_client()
    with app_rl.app_context():
        db.drop_all()


def _seed_member_token(app) -> tuple[str, str]:
    with app.app_context():
        m = Member(
            vorname="R",
            nachname="L",
            email="ratelimit-cal@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            ical_token="testtoken_rl_xx",
        )
        db.session.add(m)
        db.session.commit()
        t = m.ical_token
    return t, f"/calendar/{t}.ics"


def test_calendar_feed_304_when_etag_matches(app, client):
    with app.app_context():
        m = Member(
            vorname="E",
            nachname="Tag",
            email="etag-cal@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            ical_token="testtoken_etagger",
        )
        db.session.add(m)
        db.session.commit()
        tok = m.ical_token
        body = CalendarFeedService.generate_feed_for_member(m)
        etag = CalendarFeedService.feed_body_etag(body)
    url = f"/calendar/{tok}.ics"
    r = client.get(url, headers={"If-None-Match": etag})
    assert r.status_code == 304
    assert r.headers.get("ETag") == etag
    assert "private" in r.headers.get("Cache-Control", "")
    assert "max-age=300" in r.headers.get("Cache-Control", "")


def test_calendar_feed_200_has_cache_headers(app, client):
    with app.app_context():
        m = Member(
            vorname="C",
            nachname="H",
            email="cache-cal@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            ical_token="testtoken_cachehdr",
        )
        db.session.add(m)
        db.session.commit()
        tok = m.ical_token
    r = client.get(f"/calendar/{tok}.ics")
    assert r.status_code == 200
    assert r.headers.get("ETag")
    cc = r.headers.get("Cache-Control", "")
    assert "private" in cc and "max-age=300" in cc


def test_calendar_feed_429_after_60_requests(client_rl, app_rl):
    token, path = _seed_member_token(app_rl)
    assert token
    codes = []
    for _ in range(61):
        rv = client_rl.get(path)
        codes.append(rv.status_code)
    assert 429 in codes, f"expected 429 in responses, got tail={codes[-5:]}"


def test_calendar_feed_unknown_token_404_no_body(client, app):
    r = client.get("/calendar/doesnotexistXXXX.ics")
    assert r.status_code == 404
    assert (r.get_data(as_text=True) or "") == ""
