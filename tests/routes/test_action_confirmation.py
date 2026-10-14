"""U1w: action, actor, session, target and generation are independent boundaries."""
import base64
import re
import time
from unittest.mock import Mock

import pyotp
import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.member_mfa import MemberMFA
from backend.services.action_confirmation import ActionConfirmationService
from backend.services.security import SecurityService
from tests.conftest import auth_id

PASSWORD = 'Synthetic-action-password1!'
NEW = 'Synthetic-action-password2!'
SECRET = 'JBSWY3DPEHPK3PXP'


@pytest.fixture
def case(app, client):
    app.config['CRYPTO_KEY'] = base64.urlsafe_b64encode(bytes(range(32)))
    with app.app_context():
        rows = [Member(vorname=str(i), nachname='Test', email=f'action{i}@example.com',
                       role=Role.ADMIN if i == 0 else Role.MEMBER, funktion='MEMBER') for i in range(3)]
        for row in rows:
            row.set_password(PASSWORD)
        db.session.add_all(rows)
        db.session.commit()
        ids = [row.id for row in rows]
    sign_in(client, ids[0])
    return ids


def sign_in(client, uid):
    with client.session_transaction() as state:
        state.clear()
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True


def intent(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    return re.search(r'name="action_token" value="([^"]+)"', response.text).group(1)


def generation(app, uid):
    with app.app_context():
        return db.session.get(Member, uid).auth_generation


def edit_data():
    return {'vorname': 'Edited', 'nachname': 'Test', 'email': 'action1@example.com',
            'role': 'MEMBER', 'funktion': 'SCHATZMEISTER', 'is_active': 'y'}


def prepare(app, client, ids, action):
    if action == 'password':
        return '/auth/change-password', {'current_password': PASSWORD, 'new_password': NEW,
                                         'confirm_password': NEW}, ids[0]
    if action in ('enroll', 'disable'):
        if action == 'disable':
            with app.app_context():
                db.session.add(MemberMFA(member_id=ids[0], is_totp_enabled=True,
                                        totp_secret_encrypted=SecurityService.encrypt_json(SECRET)))
                db.session.commit()
        else:
            with client.session_transaction() as state:
                state['2fa_secret'] = SECRET
        return '/auth/2fa/' + action, {'token': pyotp.TOTP(SECRET).now(),
                                     'password': PASSWORD, 'action_password': PASSWORD}, ids[0]
    if action == 'permissions':
        return f'/admin/members/{ids[1]}/edit', dict(edit_data(), action_password=PASSWORD), ids[1]
    return f'/admin/members/{ids[1]}/reset-' + action, {'confirm': 'RESET', 'action_password': PASSWORD}, ids[1]


@pytest.mark.parametrize('action', ['password', 'enroll', 'disable', 'password-admin', '2fa', 'permissions'])
@pytest.mark.parametrize('proof', ['missing', 'wrong_password', 'valid'])
def test_every_write_requires_its_own_inline_proof(app, client, case, action, proof):
    if action == 'password-admin':
        path, data, uid = f'/admin/members/{case[1]}/reset-password', {'confirm': 'RESET', 'action_password': PASSWORD}, case[1]
    else:
        path, data, uid = prepare(app, client, case, action)
    before = generation(app, uid)
    token = intent(client, path)
    with client.session_transaction() as state:
        state['sensitive_access_member_id'] = auth_id(client, case[0])
        state['sensitive_access_until'] = time.time() + 300
    if proof != 'missing':
        data['action_token'] = token
    if proof == 'wrong_password':
        data.update(current_password='wrong', password='wrong', action_password='wrong')
    response = client.post(path, data=data)
    assert response.status_code in (200, 302)
    assert (generation(app, uid) != before) == (proof == 'valid')
    assert response.headers['Cache-Control'] == 'no-store'
    if proof != 'valid':
        assert response.status_code == 200


@pytest.mark.parametrize('boundary', ['action', 'target', 'session', 'account', 'tamper', 'expired', 'target_change', 'actor_change'])
def test_intent_boundaries(app, client, case, monkeypatch, boundary):
    path = f'/admin/members/{case[1]}/reset-2fa'
    token = intent(client, path)
    before = generation(app, case[1])
    if boundary == 'action':
        path = f'/admin/members/{case[1]}/reset-password'
    elif boundary == 'target':
        path = f'/admin/members/{case[2]}/reset-2fa'
    elif boundary == 'session':
        other = app.test_client()
        sign_in(other, case[0])
        intent(other, path)
        client = other
    elif boundary == 'account':
        with app.app_context():
            db.session.get(Member, case[2]).role = Role.ADMIN
            db.session.commit()
        sign_in(client, case[2])
        intent(client, path)
    elif boundary == 'tamper':
        token = 'invalid.' + token
    elif boundary == 'expired':
        monkeypatch.setattr('itsdangerous.timed.TimestampSigner.get_timestamp', lambda self: int(time.time()) + 601)
    elif boundary in ('target_change', 'actor_change'):
        with app.app_context():
            db.session.get(Member, case[1] if boundary == 'target_change' else case[0]).rotate_auth_generation()
            db.session.commit()
        before = generation(app, case[1])
    response = client.post(path, data={'confirm': 'RESET', 'action_token': token, 'action_password': PASSWORD})
    assert response.status_code in (200, 302)
    assert generation(app, case[1]) == before
    with app.app_context():
        assert db.session.get(Member, case[2]).check_password(PASSWORD)


def test_replay_old_cookie_and_second_tab_cannot_repeat_admin_reset(app, client, case):
    path = f'/admin/members/{case[1]}/reset-password'
    token = intent(client, path)
    second = intent(client, path)
    cookie = client.get_cookie('session').value
    payload = {'confirm': 'RESET', 'action_token': token, 'action_password': PASSWORD}
    assert client.post(path, data=payload).status_code == 302
    after = generation(app, case[1])
    for old_token in (token, second):
        client.set_cookie('session', cookie)
        response = client.post(path, data=dict(payload, action_token=old_token))
        assert response.status_code == 200
        assert generation(app, case[1]) == after


def test_failed_proof_and_abandonment_do_not_grant_anything(app, client, case):
    path = f'/admin/members/{case[1]}/reset-2fa'
    token = intent(client, path)
    before = generation(app, case[1])
    client.get('/member/profile')
    assert generation(app, case[1]) == before
    payload = {'confirm': 'RESET', 'action_token': token, 'action_password': 'wrong'}
    assert client.post(path, data=payload).status_code == 200
    assert generation(app, case[1]) == before
    payload['action_password'] = PASSWORD
    assert client.post(path, data=payload).status_code == 302
    with client.session_transaction() as state:
        assert PASSWORD not in str(dict(state))
        assert 'sensitive_access_until' not in state


def test_rollback_does_not_consume_intent(app, client, case, monkeypatch):
    path = f'/admin/members/{case[1]}/reset-2fa'
    token = intent(client, path)
    before = generation(app, case[1])
    payload = {'confirm': 'RESET', 'action_token': token, 'action_password': PASSWORD}
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
        with pytest.raises(RuntimeError):
            client.post(path, data=payload)
    assert generation(app, case[1]) == before
    assert client.post(path, data=payload).status_code == 302
    assert generation(app, case[1]) != before


def test_ordinary_edit_does_not_need_confirmation(app, client, case):
    data = edit_data()
    data['funktion'] = 'MEMBER'
    before = generation(app, case[1])
    assert client.post(f'/admin/members/{case[1]}/edit', data=data).status_code == 302
    assert generation(app, case[1]) == before
    with app.app_context():
        assert db.session.get(Member, case[1]).vorname == 'Edited'


def test_csrf_still_required(app, client, case):
    path = f'/admin/members/{case[1]}/reset-2fa'
    token = intent(client, path)
    before = generation(app, case[1])
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(path, data={'confirm': 'RESET', 'action_token': token,
                                   'action_password': PASSWORD}).status_code == 400
    assert generation(app, case[1]) == before


def test_login_boundary_clears_session_binding(app, client, case):
    path = f'/admin/members/{case[1]}/reset-2fa'
    token = intent(client, path)
    client.get('/auth/logout')
    client.post('/auth/login', data={'email': 'action0@example.com', 'password': PASSWORD})
    intent(client, path)
    before = generation(app, case[1])
    assert client.post(path, data={'confirm': 'RESET', 'action_token': token,
                                   'action_password': PASSWORD}).status_code == 200
    assert generation(app, case[1]) == before
