"""Validierung MemberForm / ProfileForm — leere Dates und Legacy-Selects."""

from __future__ import annotations

from backend.models.member import (
    NATIONALITAET_CHOICES,
    select_choices_with_legacy,
)
from backend.routes.admin import MemberForm
from backend.routes.member import ProfileForm, _parse_optional_float


def test_select_choices_with_legacy_keeps_unknown_value():
    choices = select_choices_with_legacy(NATIONALITAET_CHOICES, 'Schweiz')
    keys = {c[0] for c in choices}
    assert 'Schweiz' in keys
    assert 'CH' in keys


def test_member_form_accepts_empty_optional_dates(app):
    with app.test_request_context(
        '/admin/members/1/edit',
        method='POST',
        data={
            'vorname': 'Max',
            'nachname': 'Muster',
            'email': 'max@example.com',
            'role': 'MEMBER',
            'geburtsdatum': '',
            'beitritt': '',
            'nationalitaet': '',
            'zimmerwunsch': '',
            'funktion': 'MEMBER',
        },
    ):
        form = MemberForm(meta={'csrf': False})
        assert form.validate(), form.errors
        assert form.geburtsdatum.data is None
        assert form.beitritt.data is None


def test_member_form_empty_dates_have_no_field_errors(app):
    """Regression: leeres Geburtsdatum/Beitritt darf validate() nicht blockieren."""
    with app.test_request_context(
        method='POST',
        data={
            'vorname': 'Max',
            'nachname': 'Muster',
            'email': 'max@example.com',
            'role': 'MEMBER',
            'geburtsdatum': '',
            'beitritt': '',
            'funktion': 'MEMBER',
        },
    ):
        form = MemberForm(meta={'csrf': False})
        ok = form.validate()
        assert 'geburtsdatum' not in form.errors
        assert 'beitritt' not in form.errors
        assert ok, form.errors


def test_profile_form_accepts_legacy_nationalitaet(app):
    with app.test_request_context(
        method='POST',
        data={
            'profile-vorname': 'Max',
            'profile-nachname': 'Muster',
            'profile-email': 'max@example.com',
            'profile-nationalitaet': 'Schweiz',
            'profile-zimmerwunsch': '',
            'profile-active_tab': 'profile',
        },
    ):
        form = ProfileForm(prefix='profile', meta={'csrf': False})
        form.nationalitaet.choices = select_choices_with_legacy(
            NATIONALITAET_CHOICES, 'Schweiz'
        )
        assert form.validate(), form.errors


def test_parse_optional_float_accepts_comma():
    assert _parse_optional_float('42,5') == 42.5
    assert _parse_optional_float('') is None
    assert _parse_optional_float(None) is None
