"""A-141 password scope: stale password/activation links cannot replace credentials."""
from datetime import datetime, timedelta
from unittest.mock import Mock
import time

import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.services.security import SecurityService
from backend.services.mail import MailService

def _issue_auth_token(*args):
    from backend.routes.auth import _issue_auth_token as issue
    return issue(*args)


def _resolve_auth_token(*args):
    from backend.routes.auth import _resolve_auth_token as resolve
    return resolve(*args)


OLD = 'Synthetic-old-password'
NEW = 'Synthetic-new-password'
ATTACK = 'Synthetic-stale-link-password'


@pytest.fixture
def credentials(app, monkeypatch):
    monkeypatch.setattr(MailService, 'send_async', Mock())
    monkeypatch.setattr(SecurityService, 'log_audit_event', Mock())
    monkeypatch.setattr(SecurityService, 'generate_secure_password', lambda: NEW)
    with app.app_context():
        user = Member(vorname='Links', nachname='Test', email='links@example.com', role=Role.ADMIN)
        user.set_password(OLD)
        db.session.add(user)
        db.session.flush()
        uid = user.id
        tokens = {purpose: _issue_auth_token(uid, purpose, timedelta(days=1), None)
                  for purpose in AuthTokenPurpose}
        db.session.commit()
    return uid, tokens


def login(client, uid):
    with client.session_transaction() as state:
        state['_user_id'] = str(uid)
        state['_fresh'] = True
        state['sensitive_access_member_id'] = str(uid)
        state['sensitive_access_until'] = time.time() + 600


def replacement(client, path, password=NEW):
    return client.post(path, data={'new_password': password, 'confirm_password': password})


@pytest.mark.parametrize('entry', ['change', 'reset', 'activate', 'admin'])
@pytest.mark.parametrize('stale', [AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.ONBOARDING])
def test_success_revokes_password_links_only(app, client, credentials, entry, stale):
    uid, tokens = credentials
    if entry in ('change', 'admin'):
        login(client, uid)
        response = (client.post('/auth/change-password', data={'current_password': OLD,
                    'new_password': NEW, 'confirm_password': NEW}) if entry == 'change' else
                    client.post(f'/admin/members/{uid}/reset-password', data={'confirm': 'RESET'}))
    else:
        purpose = AuthTokenPurpose.PASSWORD_RESET if entry == 'reset' else AuthTokenPurpose.ONBOARDING
        response = replacement(client, f'/auth/{"reset-password" if entry == "reset" else "activate"}/{tokens[purpose]}')
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Member, uid).check_password(NEW)
        for purpose in AuthTokenPurpose:
            _, error = _resolve_auth_token(tokens[purpose], purpose)
            assert error == ('used' if purpose in (AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.ONBOARDING) else None)
    with client.session_transaction() as state:
        state.clear()
    path = 'reset-password' if stale == AuthTokenPurpose.PASSWORD_RESET else 'activate'
    replacement(client, f'/auth/{path}/{tokens[stale]}', ATTACK)
    with app.app_context():
        assert db.session.get(Member, uid).check_password(NEW)
    with client.session_transaction() as state:
        assert '_user_id' not in state


@pytest.mark.parametrize('purpose', [AuthTokenPurpose.PASSWORD_RESET, AuthTokenPurpose.ONBOARDING])
def test_new_issue_replaces_only_same_purpose(app, client, credentials, purpose):
    uid, tokens = credentials
    with app.app_context():
        new = _issue_auth_token(uid, purpose, timedelta(days=1), None)
        db.session.commit()
        assert _resolve_auth_token(tokens[purpose], purpose)[1] == 'used'
        assert _resolve_auth_token(new, purpose)[1] is None
        other = AuthTokenPurpose.ONBOARDING if purpose == AuthTokenPurpose.PASSWORD_RESET else AuthTokenPurpose.PASSWORD_RESET
        assert _resolve_auth_token(tokens[other], other)[1] is None


def test_failed_password_change_preserves_links(app, client, credentials):
    uid, tokens = credentials
    login(client, uid)
    assert client.post('/auth/change-password', data={'current_password': 'wrong',
        'new_password': NEW, 'confirm_password': NEW}).status_code == 200
    with app.app_context():
        assert db.session.get(Member, uid).check_password(OLD)
        assert all(row.used_at is None for row in AuthToken.query.all())


def test_new_reset_after_change_still_works(app, client, credentials):
    uid, tokens = credentials
    login(client, uid)
    client.post('/auth/change-password', data={'current_password': OLD,
                'new_password': NEW, 'confirm_password': NEW})
    with client.session_transaction() as state:
        state.clear()
    with app.app_context():
        new = _issue_auth_token(uid, AuthTokenPurpose.PASSWORD_RESET, timedelta(days=1), None)
        db.session.commit()
    replacement(client, '/auth/reset-password/' + new, ATTACK)
    with app.app_context():
        assert db.session.get(Member, uid).check_password(ATTACK)


@pytest.mark.parametrize('entry,purpose', [('reset-password', AuthTokenPurpose.PASSWORD_RESET),
                                         ('activate', AuthTokenPurpose.ONBOARDING)])
@pytest.mark.parametrize('intervening', ['revoke', 'expire', 'deactivate'])
def test_link_is_rechecked_after_intervening_change(app, client, credentials, monkeypatch,
                                                   entry, purpose, intervening):
    from backend.routes.auth import ResetPasswordForm
    uid, tokens = credentials
    validate = ResetPasswordForm.validate_on_submit
    def validate_then_change(form):
        valid = validate(form)
        if intervening == 'deactivate':
            db.session.get(Member, uid).is_active = False
        else:
            row = AuthToken.query.filter_by(member_id=uid, purpose=purpose).one()
            if intervening == 'revoke':
                row.used_at = datetime.utcnow()
            else:
                row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()
        return valid
    monkeypatch.setattr(ResetPasswordForm, 'validate_on_submit', validate_then_change)
    response = replacement(client, f'/auth/{entry}/{tokens[purpose]}')
    assert response.location.endswith('/auth/login')
    with app.app_context():
        assert db.session.get(Member, uid).check_password(OLD)
    with client.session_transaction() as state:
        assert '_user_id' not in state


@pytest.mark.parametrize('entry', ['change', 'reset'])
def test_commit_failure_rolls_back_password_and_revocation(app, client, credentials, monkeypatch, entry):
    uid, tokens = credentials
    if entry == 'change':
        login(client, uid)
    with monkeypatch.context() as patch:
        patch.setattr(db.session, 'commit', Mock(side_effect=RuntimeError('synthetic commit failure')))
        with pytest.raises(RuntimeError):
            if entry == 'change':
                client.post('/auth/change-password', data={'current_password': OLD,
                    'new_password': NEW, 'confirm_password': NEW})
            else:
                replacement(client, '/auth/reset-password/' + tokens[AuthTokenPurpose.PASSWORD_RESET])
    with app.app_context():
        assert db.session.get(Member, uid).check_password(OLD)
        assert all(row.used_at is None for row in AuthToken.query.all())


def test_get_and_invalid_form_preserve_links(app, client, credentials):
    uid, tokens = credentials
    for entry, purpose in [('reset-password', AuthTokenPurpose.PASSWORD_RESET),
                           ('activate', AuthTokenPurpose.ONBOARDING)]:
        path = f'/auth/{entry}/{tokens[purpose]}'
        assert client.get(path).status_code == 200
        assert replacement(client, path, 'short').status_code == 200
    with app.app_context():
        assert db.session.get(Member, uid).check_password(OLD)
        assert all(row.used_at is None for row in AuthToken.query.all())


def test_issue_rollback_preserves_previous_link(app, credentials):
    uid, tokens = credentials
    with app.app_context():
        _issue_auth_token(uid, AuthTokenPurpose.PASSWORD_RESET, timedelta(days=1), None)
        db.session.rollback()
        assert _resolve_auth_token(tokens[AuthTokenPurpose.PASSWORD_RESET], AuthTokenPurpose.PASSWORD_RESET)[1] is None
        assert AuthToken.query.count() == len(AuthTokenPurpose)


def test_other_account_links_remain_valid(app, client, credentials):
    uid, tokens = credentials
    with app.app_context():
        other = Member(vorname='Other', nachname='Account', email='other@example.com', passwort_hash='unused')
        db.session.add(other)
        db.session.flush()
        other_token = _issue_auth_token(other.id, AuthTokenPurpose.PASSWORD_RESET, timedelta(days=1), None)
        db.session.commit()
    login(client, uid)
    client.post('/auth/change-password', data={'current_password': OLD,
                'new_password': NEW, 'confirm_password': NEW})
    with app.app_context():
        assert _resolve_auth_token(other_token, AuthTokenPurpose.PASSWORD_RESET)[1] is None
    with client.session_transaction() as state:
        assert state['_user_id'] == str(uid)


def test_two_forgot_password_requests_only_latest_works(app, client, credentials):
    import re
    uid, _ = credentials
    links = []
    for _ in range(2):
        assert client.post('/auth/forgot-password', data={'email': 'links@example.com'}).status_code == 302
        text = MailService.send_async.call_args.kwargs['text']
        links.append(re.search(r'/auth/reset-password/([^\s]+)', text).group(1))
    replacement(client, '/auth/reset-password/' + links[0])
    with app.app_context():
        assert db.session.get(Member, uid).check_password(OLD)
    replacement(client, '/auth/reset-password/' + links[1])
    with app.app_context():
        assert db.session.get(Member, uid).check_password(NEW)
