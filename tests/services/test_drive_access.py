"""A-089: durable work, rollback, stale invites and idempotent external effects."""

from datetime import datetime
from tests.conftest import auth_id
from tests.action_confirmation_helpers import confirmed_post
from backend.services.security import SecurityService
import re
from unittest.mock import Mock

import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.drive_access_task import DriveAccessTask
from backend.services.drive_access import DriveAccessService
from backend.services.drive_storage import DriveStorageService
from backend.services.google_email_verification import GoogleEmailVerificationService


@pytest.fixture
def case(app, monkeypatch):
    app.config['GOOGLE_DRIVE_ID'] = 'synthetic-drive'
    external = Mock()
    monkeypatch.setattr(DriveStorageService, 'apply_membership', external)
    with app.app_context():
        member = Member(password_changed_at=datetime(2026, 1, 1),
                        vorname='Drive', nachname='Test', email='member@example.com',
                        passwort_hash='unused', google_email='old@example.com',
                        google_email_verified=True)
        admin = Member(password_changed_at=datetime(2026, 1, 1),
                       vorname='Admin', nachname='Test', email='admin@example.com',
                       passwort_hash=SecurityService.hash_password('Synthetic-drive-admin1!'), role=Role.ADMIN)
        db.session.add_all([member, admin])
        db.session.commit()
        return member.id, admin.id, external


def change(uid, email='new@example.com'):
    return GoogleEmailVerificationService.issue(uid, email=email)[0]


def test_change_snapshots_old_scope_and_retries_after_config_change(app, case):
    uid, _, external = case
    with app.app_context():
        change(uid)
        db.session.remove()
        task = DriveAccessTask.query.one()
        assert (task.email, task.drive_id, task.status) == ('old@example.com', 'synthetic-drive', 'pending')
        app.config['GOOGLE_DRIVE_ID'] = 'different-drive'
        external.side_effect = TimeoutError('secret external payload')
        assert not DriveAccessService.process_member(uid)
        db.session.remove()
        task = DriveAccessTask.query.one()
        assert (task.status, task.attempts, task.error_code) == ('failed', 1, 'drive_error')
        external.side_effect = None
        assert DriveAccessService.process_member(uid)
        assert DriveAccessService.process_member(uid)
        assert external.call_count == 2
        external.assert_called_with('synthetic-drive', 'old@example.com', 'revoke')


def test_address_and_task_rollback_together(app, case, monkeypatch):
    uid, _, external = case
    with app.app_context():
        with monkeypatch.context() as patch:
            patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(RuntimeError):
                change(uid)
        db.session.rollback()
        assert db.session.get(Member, uid).google_email == 'old@example.com'
        assert DriveAccessTask.query.count() == 0
        external.assert_not_called()


def test_verification_and_invite_rollback_together(app, case, monkeypatch):
    uid, _, external = case
    with app.app_context():
        delivery = change(uid)
        with monkeypatch.context() as patch:
            patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(RuntimeError):
                GoogleEmailVerificationService.consume(delivery.token)
        db.session.rollback()
        assert not db.session.get(Member, uid).google_email_verified
        assert AuthToken.query.one().used_at is None
        assert DriveAccessTask.query.filter_by(action='invite').count() == 0
        external.assert_not_called()


def test_multiple_changes_back_to_original_revoke_before_latest_invite(app, case):
    uid, _, external = case
    with app.app_context():
        first = change(uid)
        GoogleEmailVerificationService.consume(first.token)
        second = change(uid, 'old@example.com')
        GoogleEmailVerificationService.consume(second.token)
        external.side_effect = RuntimeError('temporary')
        assert not DriveAccessService.process_member(uid)
        assert external.call_args.args[2] == 'revoke'
        external.reset_mock(side_effect=True)
        assert DriveAccessService.process_member(uid)
        assert [call.args for call in external.call_args_list] == [
            ('synthetic-drive', 'old@example.com', 'revoke'),
            ('synthetic-drive', 'new@example.com', 'revoke'),
            ('synthetic-drive', 'old@example.com', 'invite'),
        ]
        assert DriveAccessTask.query.filter_by(action='invite', status='cancelled').count() == 1


def test_partial_success_persists_and_retry_skips_completed_step(app, case):
    uid, _, external = case
    with app.app_context():
        change(uid)
        latest = change(uid, 'third@example.com')
        GoogleEmailVerificationService.consume(latest.token)
        external.side_effect = [None, TimeoutError('failure')]
        assert not DriveAccessService.process_member(uid)
        assert DriveAccessTask.query.filter_by(status='done').count() == 1
        external.reset_mock(side_effect=True)
        assert DriveAccessService.process_member(uid)
        assert [call.args[1:] for call in external.call_args_list] == [
            ('new@example.com', 'revoke'), ('third@example.com', 'invite')]


def test_api_success_db_failure_leaves_work_retryable(app, case, monkeypatch):
    uid, _, external = case
    with app.app_context():
        change(uid)
        with monkeypatch.context() as patch:
            patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic')))
            assert not DriveAccessService.process_member(uid)
        db.session.remove()
        assert DriveAccessTask.query.one().status == 'pending'
        assert DriveAccessService.process_member(uid)
        assert external.call_count == 2


@pytest.mark.parametrize('invalid', ['inactive', 'unverified', 'changed'])
def test_stale_invite_never_calls_drive(app, case, invalid):
    uid, _, external = case
    with app.app_context():
        member = db.session.get(Member, uid)
        DriveAccessService.queue_invite(member)
        if invalid == 'inactive':
            member.is_active = False
        elif invalid == 'unverified':
            member.google_email_verified = False
        else:
            member.google_email = 'another@example.com'
        db.session.commit()
        assert DriveAccessService.process_member(uid)
        assert DriveAccessTask.query.one().status == 'cancelled'
        external.assert_not_called()


def login(client, uid):
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True


def member_form(active=False):
    data = dict(vorname='Drive', nachname='Test', email='member@example.com',
                role='MEMBER', funktion='MEMBER')
    if active:
        data['is_active'] = 'y'
    return data


def test_admin_deactivation_cancels_invite_and_retains_failed_revoke(app, client, case):
    uid, aid, external = case
    with app.app_context():
        delivery = change(uid)
        GoogleEmailVerificationService.consume(delivery.token)
    login(client, aid)
    external.side_effect = TimeoutError('do not leak')
    assert confirmed_post(client, f'/admin/members/{uid}/edit', data=member_form(), password='Synthetic-drive-admin1!').status_code == 302
    with app.app_context():
        member = db.session.get(Member, uid)
        assert not member.is_active and not member.google_email_verified
        assert DriveAccessTask.query.filter_by(action='invite', status='cancelled').count() == 1
        assert DriveAccessTask.query.filter_by(action='revoke', status='failed').count() == 1
    response = client.get('/admin/')
    assert response.status_code == 200
    assert 'Offene Drive-Aufgaben' in response.text
    assert 'do not leak' not in response.text
    external.reset_mock(side_effect=True)
    assert client.post(f'/admin/drive-access/{uid}/retry').status_code == 302
    assert all(call.args[2] == 'revoke' for call in external.call_args_list)


def test_reactivation_requires_new_google_verification(app, client, case):
    uid, aid, external = case
    with app.app_context():
        old = change(uid)
    login(client, aid)
    confirmed_post(client, f'/admin/members/{uid}/edit', data=member_form(), password='Synthetic-drive-admin1!')
    confirmed_post(client, f'/admin/members/{uid}/edit', data=member_form(True), password='Synthetic-drive-admin1!')
    external.reset_mock()
    with app.app_context():
        assert GoogleEmailVerificationService.consume(old.token)[0] is None
        assert not db.session.get(Member, uid).google_email_verified
        new, error = GoogleEmailVerificationService.issue(uid)
        assert not error
        assert GoogleEmailVerificationService.consume(new.token)[0]
        assert DriveAccessService.process_member(uid)
        assert external.call_args.args[2] == 'invite'


def test_deactivation_rollback_keeps_active_and_no_task(app, client, case):
    uid, aid, external = case
    login(client, aid)
    data = member_form()
    data['email'] = 'admin@example.com'
    assert confirmed_post(client, f'/admin/members/{uid}/edit', data=data, password='Synthetic-drive-admin1!').status_code == 200
    with app.app_context():
        assert db.session.get(Member, uid).is_active
        assert DriveAccessTask.query.count() == 0
    external.assert_not_called()


def test_admin_tasks_hidden_from_member_and_get_never_executes(app, client, case):
    uid, aid, external = case
    with app.app_context():
        change(uid)
    login(client, uid)
    assert 'Offene Drive-Aufgaben' not in client.get('/admin/').text
    assert client.post(f'/admin/drive-access/{uid}/retry').status_code == 403
    login(client, aid)
    assert 'Offene Drive-Aufgaben' in client.get('/admin/').text
    assert client.get(f'/admin/drive-access/{uid}/retry').status_code == 405
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(f'/admin/drive-access/{uid}/retry').status_code == 400
    external.assert_not_called()


def test_inactive_admin_cannot_retry(app, client, case):
    uid, aid, external = case
    with app.app_context():
        change(uid)
        db.session.get(Member, aid).is_active = False
        db.session.commit()
    login(client, aid)
    response = client.post(f'/admin/drive-access/{uid}/retry')
    assert response.status_code == 302 and '/auth/login' in response.location
    external.assert_not_called()


def test_disabled_feature_preserves_visible_task_and_retry(app, client, case):
    uid, aid, external = case
    app.config['DRIVE_FEATURE_ENABLED'] = False
    with app.app_context():
        change(uid)
        assert not DriveAccessService.process_member(uid)
    login(client, aid)
    assert 'Offene Drive-Aufgaben' in client.get('/admin/').text
    external.assert_not_called()
    app.config['DRIVE_FEATURE_ENABLED'] = True
    assert client.post(f'/admin/drive-access/{uid}/retry').status_code == 302
    external.assert_called_once()


def test_missing_scope_requires_explicit_admin_binding(app, client, case):
    uid, aid, external = case
    app.config['GOOGLE_DRIVE_ID'] = None
    with app.app_context():
        change(uid)
        assert not DriveAccessService.process_member(uid)
    app.config['GOOGLE_DRIVE_ID'] = 'newly-configured'
    login(client, aid)
    client.post(f'/admin/drive-access/{uid}/retry')
    external.assert_not_called()
    client.post(f'/admin/drive-access/{uid}/retry', data={'bind_missing_drive': 'yes'})
    external.assert_called_once_with('newly-configured', 'old@example.com', 'revoke')


def test_unchanged_verified_address_does_not_revoke(app, case):
    uid, _, external = case
    with app.app_context():
        assert GoogleEmailVerificationService.issue(uid, email='old@example.com') == (None, 'verified')
        assert DriveAccessTask.query.count() == 0
        external.assert_not_called()


def test_valid_csrf_retry_records_actual_admin_and_no_external_details(app, client, case, caplog):
    from backend.models.audit_event import AuditEvent
    uid, aid, external = case
    with app.app_context():
        change(uid)
    app.config['WTF_CSRF_ENABLED'] = True
    login(client, aid)
    html = client.get('/admin/').text
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    external.side_effect = RuntimeError('SECRET_EXTERNAL_RESPONSE')
    response = client.post(f'/admin/drive-access/{uid}/retry', data={'csrf_token': token},
                           follow_redirects=True)
    assert response.status_code == 200
    assert 'SECRET_EXTERNAL_RESPONSE' not in response.text + caplog.text
    with app.app_context():
        event = AuditEvent.query.filter_by(entity='member', entity_id=uid).one()
        assert event.actor_id == aid
        assert event.extra_json == {'task_id': DriveAccessTask.query.one().id,
                                    'error_code': 'drive_error'}


def test_deactivation_commit_failure_rolls_back_task_and_tokens(app, client, case, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    uid, aid, external = case
    with app.app_context():
        delivery, _ = GoogleEmailVerificationService.issue(uid, email='new@example.com')
        DriveAccessService.process_member(uid)
    external.reset_mock()
    login(client, aid)
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=IntegrityError('synthetic', {}, None)))
        assert confirmed_post(client, f'/admin/members/{uid}/edit', data=member_form(), password='Synthetic-drive-admin1!').status_code == 200
    with app.app_context():
        assert db.session.get(Member, uid).is_active
        assert AuthToken.query.one().used_at is None
        assert DriveAccessTask.query.filter_by(status='pending').count() == 0
        assert DriveAccessTask.query.count() == 1
    external.assert_not_called()


def test_other_members_work_and_non_google_tokens_are_preserved(app, case):
    from datetime import datetime, timedelta
    uid, aid, external = case
    with app.app_context():
        db.session.add(DriveAccessTask(member_id=aid, email='other@example.com',
                                      action='revoke', drive_id='synthetic-drive'))
        db.session.add(AuthToken(member_id=uid, purpose=AuthTokenPurpose.PASSWORD_RESET,
                                token_hash='synthetic', expires_at=datetime.utcnow() + timedelta(hours=1)))
        member = db.session.get(Member, uid)
        DriveAccessService.deactivate(member)
        member.is_active = False
        db.session.commit()
        assert DriveAccessService.process_member(uid)
        assert DriveAccessTask.query.filter_by(member_id=aid).one().status == 'pending'
        assert AuthToken.query.one().used_at is None
        external.assert_called_once_with('synthetic-drive', 'old@example.com', 'revoke')
