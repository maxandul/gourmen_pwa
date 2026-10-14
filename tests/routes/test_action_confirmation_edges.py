"""Extra race, secrecy and enabled-limiter checks for U1w."""
import logging

import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.services.security import SecurityService
from tests.routes.test_action_confirmation import (case, PASSWORD, NEW, intent, generation,
                                                  edit_data, sign_in)


def test_target_switch_does_not_mutate_either_account(app, client, case):
    first, second = case[1:]
    token = intent(client, f'/admin/members/{first}/reset-2fa')
    before = [generation(app, uid) for uid in (first, second)]
    assert client.post(f'/admin/members/{second}/reset-2fa', data={
        'action_token': token, 'action_password': PASSWORD, 'confirm': 'RESET'}).status_code == 200
    assert [generation(app, uid) for uid in (first, second)] == before


@pytest.mark.parametrize('who', ['actor', 'target', 'actor_deactivation', 'actor_demotion'])
def test_recheck_after_request_authentication_before_lock(app, client, case, monkeypatch, who):
    path = f'/admin/members/{case[1]}/reset-password'
    token = intent(client, path)
    lock = SecurityService.lock_credential_member
    changed = False
    uid = case[1] if who == 'target' else case[0]
    def intervening(member_id):
        nonlocal changed
        if not changed:
            changed = True
            values = {'auth_generation': 'synthetic-intervening'}
            if who == 'actor_deactivation':
                values['is_active'] = False
            elif who == 'actor_demotion':
                values['role'] = Role.MEMBER
            db.session.execute(Member.__table__.update().where(Member.id == uid).values(**values))
            db.session.commit()
        return lock(member_id)
    monkeypatch.setattr(SecurityService, 'lock_credential_member', intervening)
    response = client.post(path, data={'action_token': token, 'action_password': PASSWORD, 'confirm': 'RESET'})
    assert response.status_code == (200 if who == 'target' else 403)
    with app.app_context():
        assert db.session.get(Member, case[1]).check_password(PASSWORD)
        assert db.session.get(Member, uid).auth_generation == 'synthetic-intervening'


def test_permission_error_preserves_fields_but_not_password(app, client, case, caplog):
    path = f'/admin/members/{case[1]}/edit'
    token = intent(client, path)
    before = generation(app, case[1])
    with caplog.at_level(logging.INFO):
        response = client.post(path, data=dict(edit_data(), action_token=token,
                                               action_password='Synthetic-private-wrong'))
    assert response.status_code == 200
    assert 'value="Edited"' in response.text
    assert 'Synthetic-private-wrong' not in response.text + caplog.text
    assert generation(app, case[1]) == before
    with client.session_transaction() as state:
        assert 'Synthetic-private-wrong' not in str(dict(state))
    with app.app_context():
        assert db.session.get(Member, case[1]).vorname == '1'


def test_confirmation_rate_limit_with_enabled_app(monkeypatch):
    from backend.app import create_app
    from backend.config import TestingConfig
    monkeypatch.setattr(TestingConfig, 'RATELIMIT_ENABLED', True)
    monkeypatch.setattr(TestingConfig, 'REDIS_URL', None)
    app = create_app('testing')
    try:
        with app.app_context():
            db.create_all()
            row = Member(vorname='Rate', nachname='Test', email='rate@example.com')
            row.set_password(PASSWORD)
            db.session.add(row)
            db.session.commit()
            uid = row.id
        client = app.test_client()
        sign_in(client, uid)
        token = intent(client, '/auth/change-password')
        data = {'action_token': token, 'current_password': 'wrong',
                'new_password': NEW, 'confirm_password': NEW}
        for _ in range(5):
            assert client.post('/auth/change-password', data=data).status_code == 200
        response = client.post('/auth/change-password', data=data)
        assert response.status_code == 429
        assert response.headers['Cache-Control'] == 'no-store'
        with app.app_context():
            assert db.session.get(Member, uid).check_password(PASSWORD)
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
