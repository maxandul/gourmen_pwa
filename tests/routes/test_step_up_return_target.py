"""A-035: step-up never redirects to an external or ambiguous target."""

from datetime import datetime
import time
from urllib.parse import urlencode

import pytest

from backend.extensions import db
from backend.models.member import Member
from backend.services.security import SecurityService

PASSWORD = 'Synthetic-step-up-password'
TARGET = '/member/profile?tab=sensitive#details'


@pytest.fixture
def actor(app, client):
    with app.app_context():
        user = Member(password_changed_at=datetime(2026, 1, 1),
                      vorname='Return', nachname='StepUp', email='step-return@example.com',
                      passwort_hash=SecurityService.hash_password(PASSWORD))
        db.session.add(user)
        db.session.commit()
        uid = user.id
    with client.session_transaction() as state:
        state['_user_id'] = str(uid)
        state['_fresh'] = True
    return uid


@pytest.mark.parametrize('source', ['query', 'next', 'next_url', 'session'])
@pytest.mark.parametrize('granted', [False, True])
@pytest.mark.parametrize('target', ['//example.invalid/path', '/\\example.invalid/path'])
def test_unsafe_target_never_redirects(client, actor, source, granted, target):
    url = '/auth/step-up'
    data = {'password': PASSWORD}
    if source == 'query':
        url += '?' + urlencode({'next': target})
    elif source in ('next', 'next_url'):
        data[source] = target
    with client.session_transaction() as state:
        if source == 'session':
            state['step_up_next'] = target
        if granted:
            state['sensitive_access_until'] = int(time.time()) + 300
            state['sensitive_access_member_id'] = str(actor)
    response = client.post(url, data=data)
    assert response.status_code == 302
    assert response.location.rstrip('/') == '/dashboard'
    with client.session_transaction() as state:
        assert 'step_up_next' not in state


def test_valid_target_survives_wrong_password_and_retry(client, actor):
    assert client.get('/auth/step-up?' + urlencode({'next': TARGET})).status_code == 200
    assert client.post('/auth/step-up', data={'password': 'wrong'}).status_code == 200
    with client.session_transaction() as state:
        assert state['step_up_next'] == TARGET
        assert 'sensitive_access_until' not in state
    response = client.post('/auth/step-up', data={'password': PASSWORD})
    assert response.location == TARGET
    with client.session_transaction() as state:
        assert 'step_up_next' not in state
        assert state['sensitive_access_member_id'] == str(actor)


def test_invalid_new_target_does_not_mask_valid_stored_target(client, actor):
    with client.session_transaction() as state:
        state['step_up_next'] = TARGET
    response = client.post('/auth/step-up?next=//example.invalid', data={'password': PASSWORD})
    assert response.location == TARGET


def test_invalid_stored_target_removed_even_after_wrong_password(client, actor):
    with client.session_transaction() as state:
        state['step_up_next'] = '//example.invalid'
    response = client.post('/auth/step-up', data={'password': 'wrong'})
    assert response.status_code == 200
    assert b'//example.invalid' not in response.data
    with client.session_transaction() as state:
        assert 'step_up_next' not in state
        assert 'sensitive_access_until' not in state


def test_valid_target_with_existing_grant(client, actor):
    with client.session_transaction() as state:
        state['sensitive_access_until'] = int(time.time()) + 300
        state['sensitive_access_member_id'] = str(actor)
    response = client.get('/auth/step-up?' + urlencode({'next': TARGET}))
    assert response.location == TARGET
    with client.session_transaction() as state:
        assert 'step_up_next' not in state
