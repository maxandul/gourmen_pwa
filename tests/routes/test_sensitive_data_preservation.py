"""U1a: unreadable synthetic member data must survive reads and writes."""

from datetime import datetime

import time

import pytest
from cryptography.fernet import Fernet

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService


@pytest.fixture
def sensitive_case(app, client, request):
    route = request.param
    app.config['CRYPTO_KEY'] = Fernet.generate_key().decode()
    with app.app_context():
        actor = Member(password_changed_at=datetime(2026, 1, 1),
                       vorname='Test', nachname='Actor', email='actor@example.test',
                       passwort_hash='unused', role=Role.ADMIN if route == 'admin' else Role.MEMBER)
        target = Member(password_changed_at=datetime(2026, 1, 1),
                        vorname='Test', nachname='Target', email='target@example.test',
                        passwort_hash='unused')
        db.session.add_all([actor, target])
        db.session.commit()
        actor_id = actor.id
        target_id = target.id if route == 'admin' else actor.id
    with client.session_transaction() as session:
        session['_user_id'] = str(actor_id)
        session['_fresh'] = True
        session['sensitive_access_until'] = int(time.time()) + 600
        session['sensitive_access_member_id'] = str(actor_id)
    url = (f'/admin/members/{target_id}/sensitive' if route == 'admin'
           else '/member/profile?tab=sensitive')
    prefix = '' if route == 'admin' else 'sensitive-'
    return client, url, target_id, prefix


def store(app, member_id, payload):
    with app.app_context():
        db.session.add(MemberSensitive(member_id=member_id, payload_encrypted=payload))
        db.session.commit()
    return snapshot(app, member_id)


def snapshot(app, member_id):
    # New context/session: verify persisted values, not cached ORM objects or HTTP alone.
    with app.app_context():
        row = MemberSensitive.query.filter_by(member_id=member_id).one()
        return row.id, row.payload_encrypted, row.created_at, row.updated_at


@pytest.mark.parametrize('sensitive_case', ['self', 'admin'], indirect=True)
@pytest.mark.parametrize('first_method', ['get', 'post'])
@pytest.mark.parametrize('failure', ['corrupt', 'wrong_key', 'missing_key', 'invalid_key',
                                     'invalid_json', 'invalid_utf8', 'wrong_shape', 'exception'])
def test_unreadable_data_survives_get_and_post(
        app, sensitive_case, failure, first_method, monkeypatch, caplog):
    client, url, member_id, prefix = sensitive_case
    key = app.config['CRYPTO_KEY']
    fernet = Fernet(key.encode())
    payload = fernet.encrypt(b'{"pass_nummer":"SYNTHETIC-PRIVATE"}').decode()
    if failure == 'corrupt':
        payload = 'SYNTHETIC-CORRUPT-PAYLOAD'
    elif failure == 'invalid_json':
        payload = fernet.encrypt(b'SYNTHETIC-INVALID-JSON').decode()
    elif failure == 'invalid_utf8':
        payload = fernet.encrypt(b'\xffSYNTHETIC-PRIVATE').decode()
    elif failure == 'wrong_shape':
        payload = fernet.encrypt(b'["SYNTHETIC-PRIVATE"]').decode()
    before = store(app, member_id, payload)
    if failure == 'wrong_key':
        app.config['CRYPTO_KEY'] = Fernet.generate_key().decode()
    elif failure == 'missing_key':
        app.config['CRYPTO_KEY'] = None
    elif failure == 'invalid_key':
        app.config['CRYPTO_KEY'] = 'SYNTHETIC-INVALID-KEY'
    elif failure == 'exception':
        def fail(_):
            raise RuntimeError('SYNTHETIC-EXCEPTION-SECRET')
        monkeypatch.setattr(SecurityService, 'decrypt_json', fail)

    # Direct POST, repeated GET, and a stale/empty form submission must all be safe.
    for method in [first_method, 'get', 'post']:
        response = getattr(client, method)(url, **({'data': {
            'active_tab': 'sensitive', prefix + 'pass_nummer': '',
        }} if method == 'post' else {}))
        assert snapshot(app, member_id) == before
        assert response.status_code == 500
        body = response.get_data(as_text=True)
        assert 'unverändert erhalten' in body
        assert 'name="' + prefix + 'pass_nummer"' not in body
        for secret in [payload, key, 'SYNTHETIC-PRIVATE', 'SYNTHETIC-INVALID-JSON',
                       'SYNTHETIC-INVALID-KEY', 'SYNTHETIC-EXCEPTION-SECRET']:
            assert secret not in body
            assert secret not in caplog.text


@pytest.mark.parametrize('sensitive_case', ['self', 'admin'], indirect=True)
@pytest.mark.parametrize('existing', [False, True])
def test_valid_and_absent_data_remain_editable(app, sensitive_case, existing):
    client, url, member_id, prefix = sensitive_case
    if existing:
        with app.app_context():
            payload = SecurityService.encrypt_json({'pass_nummer': 'SYNTHETIC-OLD'})
        before = store(app, member_id, payload)
    response = client.get(url)
    assert response.status_code == 200
    if existing:
        assert 'SYNTHETIC-OLD' in response.get_data(as_text=True)
        assert snapshot(app, member_id) == before
    response = client.post(url, data={'active_tab': 'sensitive', prefix + 'pass_nummer': 'SYNTHETIC-NEW'})
    assert response.status_code == 302
    with app.app_context():
        row = MemberSensitive.query.filter_by(member_id=member_id).one()
        assert SecurityService.decrypt_json(row.payload_encrypted)['pass_nummer'] == 'SYNTHETIC-NEW'
    assert 'SYNTHETIC-NEW' in client.get(url).get_data(as_text=True)


@pytest.mark.parametrize('sensitive_case', ['self', 'admin'], indirect=True)
def test_retry_after_temporary_read_failure(app, sensitive_case, monkeypatch):
    client, url, member_id, _ = sensitive_case
    with app.app_context():
        payload = SecurityService.encrypt_json({'pass_nummer': 'SYNTHETIC-RETRY'})
    before = store(app, member_id, payload)
    with monkeypatch.context() as patch:
        patch.setattr(SecurityService, 'decrypt_json', lambda _: (_ for _ in ()).throw(ValueError()))
        assert client.get(url).status_code == 500
        assert snapshot(app, member_id) == before
    response = client.get(url)
    assert response.status_code == 200
    assert 'SYNTHETIC-RETRY' in response.get_data(as_text=True)
    assert snapshot(app, member_id) == before


@pytest.mark.parametrize('sensitive_case', ['self', 'admin'], indirect=True)
def test_audit_failure_does_not_delete_readable_data(app, sensitive_case, monkeypatch):
    client, url, member_id, _ = sensitive_case
    with app.app_context():
        payload = SecurityService.encrypt_json({'pass_nummer': 'SYNTHETIC-AUDIT'})
    before = store(app, member_id, payload)

    def fail_audit(*args, **kwargs):
        raise RuntimeError('Synthetic audit outage')

    monkeypatch.setattr(SecurityService, 'log_audit_event', fail_audit)
    with pytest.raises(RuntimeError, match='Synthetic audit outage'):
        client.get(url)
    assert snapshot(app, member_id) == before


@pytest.mark.parametrize('sensitive_case', ['self', 'admin'], indirect=True)
@pytest.mark.parametrize('method', ['get', 'post'])
def test_step_up_is_still_required(app, sensitive_case, method, monkeypatch):
    client, url, member_id, _ = sensitive_case
    before = store(app, member_id, 'SYNTHETIC-UNREADABLE')
    with client.session_transaction() as session:
        session.pop('sensitive_access_until')

    def unexpected_read(_):
        pytest.fail('Sensitive data read before step-up')

    monkeypatch.setattr(SecurityService, 'read_member_sensitive', unexpected_read)
    response = getattr(client, method)(url)
    assert response.status_code == 302
    assert '/auth/step-up' in response.location
    assert snapshot(app, member_id) == before
