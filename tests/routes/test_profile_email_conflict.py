"""A-084: profile conflicts retain input and never partially save the member."""

from datetime import datetime
from tests.conftest import auth_id
import pytest
from sqlalchemy.exc import IntegrityError

from backend.extensions import db
from backend.models.member import Member
from backend.routes.member import ProfileForm


@pytest.fixture
def members(app, client):
    with app.app_context():
        owner = Member(password_changed_at=datetime(2026, 1, 1),
                       vorname='Original', nachname='Owner', email='owner@example.com',
                       passwort_hash='unused', telefon='original-phone')
        other = Member(password_changed_at=datetime(2026, 1, 1),
                       vorname='Other', nachname='Member', email='taken@example.com', passwort_hash='unused')
        db.session.add_all([owner, other])
        db.session.commit()
        ids = owner.id, other.id
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, ids[0])
        state['_fresh'] = True
    return ids


def submit(client, email):
    return client.post('/member/profile', data={
        'active_tab': 'profile', 'profile-vorname': 'Edited', 'profile-nachname': 'Owner',
        'profile-email': email, 'profile-telefon': 'edited-phone',
    })


def saved(app, uid):
    with app.app_context():
        row = db.session.get(Member, uid)
        return row.email, row.vorname, row.telefon


@pytest.mark.parametrize('active', [True, False])
def test_duplicate_email_preserves_profile_and_input(app, client, members, active):
    with app.app_context():
        db.session.get(Member, members[1]).is_active = active
        db.session.commit()
    before = saved(app, members[0])
    response = submit(client, 'taken@example.com')
    assert response.status_code == 200
    assert 'Diese E-Mail-Adresse wird bereits verwendet.' in response.get_data(as_text=True)
    assert b'value="Edited"' in response.data
    assert b'value="taken@example.com"' in response.data
    assert saved(app, members[0]) == before


@pytest.mark.parametrize('email', ['owner@example.com', 'new@example.com', 'MixedCase@example.com'])
def test_available_or_own_email_saves(app, client, members, email):
    response = submit(client, email)
    assert response.status_code == 302
    assert saved(app, members[0]) == (email.strip().lower(), 'Edited', 'edited-phone')


def test_db_conflict_after_precheck_rolls_back(app, client, members, monkeypatch):
    # Simulate a precheck that saw no competing row; exercise the real DB constraint.
    monkeypatch.setattr(ProfileForm, 'validate_email', lambda self, field: None, raising=False)
    before = saved(app, members[0])
    response = submit(client, 'taken@example.com')
    assert response.status_code == 200
    assert 'Diese E-Mail-Adresse wird bereits verwendet.' in response.get_data(as_text=True)
    assert b'value="Edited"' in response.data
    assert saved(app, members[0]) == before
    assert submit(client, 'free@example.com').status_code == 302


def test_other_integrity_failure_is_not_misreported_as_duplicate(app, client, members, monkeypatch):
    before = saved(app, members[0])
    with monkeypatch.context() as patch:
        def fail():
            raise IntegrityError('synthetic SQL private', {'private': 'synthetic-value'}, Exception('synthetic'))
        patch.setattr(db.session, 'commit', fail)
        response = submit(client, 'free@example.com')
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'Profil konnte nicht gespeichert werden.' in text
    assert 'synthetic-value' not in text
    assert 'synthetic SQL' not in text
    assert 'Diese E-Mail-Adresse wird bereits verwendet.' not in text
    assert saved(app, members[0]) == before


def test_profile_csrf_still_required(app, client, members):
    app.config['WTF_CSRF_ENABLED'] = True
    before = saved(app, members[0])
    assert submit(client, 'free@example.com').status_code == 400
    assert saved(app, members[0]) == before
