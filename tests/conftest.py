"""Gemeinsame pytest-Fixtures (App, DB, eingeloggter Test-User)."""

from __future__ import annotations

from datetime import datetime

import pytest
from werkzeug.security import generate_password_hash

import backend.models  # noqa: F401 – alle Modelle fuer db.create_all registrieren
from backend.app import create_app
from backend.extensions import db


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    application = create_app("testing")
    application.config["DRIVE_FEATURE_ENABLED"] = True
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_member_with_event() -> int:
    from backend.models.event import Event, EventType
    from backend.models.member import Member

    m = Member(
        vorname="Docs",
        nachname="Smoke",
        email="docs-smoke@example.test",
        passwort_hash=generate_password_hash("TestPasswortMind12"),
    )
    db.session.add(m)
    db.session.commit()
    ev = Event(
        organisator_id=m.id,
        datum=datetime(2026, 5, 1, 12, 0, 0),
        event_typ=EventType.MONATSESSEN,
        season=2026,
        restaurant="Cafe RueTest",
    )
    db.session.add(ev)
    db.session.commit()
    return m.id


@pytest.fixture
def logged_in_client(app, client):
    """Test-Client mit Session eines aktiven Mitglieds (ohne Login-Form)."""
    with app.app_context():
        uid = _seed_member_with_event()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(uid)
        sess["_fresh"] = True
    return client
