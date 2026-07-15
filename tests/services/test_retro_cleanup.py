"""Tests für RetroCleanupService (Bereinigungs-Completion)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from werkzeug.security import generate_password_hash

from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.member import Member
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.services.retro_cleanup import RetroCleanupService


def _event(allow_ratings: bool = True):
    return SimpleNamespace(allow_ratings=allow_ratings, id=1)


def _participation(teilnahme: bool, responded_at=None):
    return SimpleNamespace(teilnahme=teilnahme, responded_at=responded_at)


@pytest.mark.parametrize(
    "participation,has_rating,allow_ratings,expected",
    [
        (None, False, True, False),
        (_participation(False, None), False, True, True),
        (_participation(False, datetime(2026, 1, 1)), False, True, True),
        (_participation(True, None), False, True, False),
        (_participation(True, None), True, True, True),
        (_participation(True, None), False, False, True),
        (_participation(True, datetime(2026, 1, 1)), False, True, False),
        (_participation(True, datetime(2026, 1, 1)), True, True, True),
        (_participation(True, datetime(2026, 1, 1)), False, False, True),
    ],
)
def test_is_completed_matrix(participation, has_rating, allow_ratings, expected):
    event = _event(allow_ratings=allow_ratings)
    assert (
        RetroCleanupService._is_completed(event, participation, has_rating, member_id=1)
        is expected
    )


def test_list_open_skips_absent_without_responded_at_and_rated_without_responded_at(app):
    with app.app_context():
        member = Member(
            vorname="Cleanup",
            nachname="Tester",
            email="cleanup-test@example.test",
            passwort_hash=generate_password_hash("TestPasswortMind12"),
            beitritt=date(2020, 1, 1),
        )
        db.session.add(member)
        db.session.flush()

        past = datetime.utcnow() - timedelta(days=10)
        ev_absent = Event(
            organisator_id=member.id,
            datum=past,
            event_typ=EventType.MONATSESSEN,
            season=past.year,
            restaurant="Absent Stub",
            published=True,
            allow_ratings=True,
        )
        ev_rated = Event(
            organisator_id=member.id,
            datum=past - timedelta(days=1),
            event_typ=EventType.MONATSESSEN,
            season=past.year,
            restaurant="Rated Stub",
            published=True,
            allow_ratings=True,
        )
        ev_open = Event(
            organisator_id=member.id,
            datum=past - timedelta(days=2),
            event_typ=EventType.MONATSESSEN,
            season=past.year,
            restaurant="Open Stub",
            published=True,
            allow_ratings=True,
        )
        db.session.add_all([ev_absent, ev_rated, ev_open])
        db.session.flush()

        db.session.add(
            Participation(
                member_id=member.id,
                event_id=ev_absent.id,
                teilnahme=False,
                responded_at=None,
            )
        )
        db.session.add(
            Participation(
                member_id=member.id,
                event_id=ev_rated.id,
                teilnahme=True,
                responded_at=None,
            )
        )
        db.session.add(
            EventRating(
                event_id=ev_rated.id,
                participant_id=member.id,
                food_rating=4,
                drinks_rating=4,
                service_rating=4,
            )
        )
        # ev_open: keine Participation → offen
        db.session.commit()

        open_ids = [e.id for e in RetroCleanupService.list_open_cleanup_events(member.id)]
        assert ev_absent.id not in open_ids
        assert ev_rated.id not in open_ids
        assert ev_open.id in open_ids

        progress = RetroCleanupService.get_progress(member.id)
        assert progress["pending"] == len(open_ids)
        assert progress["pending"] >= 1
