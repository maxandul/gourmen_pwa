"""Isolated credential changes followed by use of older access links."""
from pathlib import Path
from datetime import timedelta, datetime, timezone
import json
import logging
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
logging.disable(logging.CRITICAL)
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.auth_token import AuthToken, AuthTokenPurpose

app = create_app('testing')
from backend.routes.auth import _issue_auth_token
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
OLD = 'Synthetic-Initial-Password-471!'
CHANGED = 'Synthetic-Changed-Password-582!'
FINAL = 'Synthetic-Link-Password-693!'


def post_password(client, path, password, current=None):
    data = dict(new_password=password, confirm_password=password)
    if current is not None:
        data['current_password'] = current
    response = client.post(path, data=data)
    return dict(status=response.status_code, redirect=response.location)


def probe(purpose, change_method):
    with app.app_context():
        db.create_all()
        member = Member(id=1, vorname='Audit', nachname='Linkfolge',
                        email='token-lifecycle@example.com', is_active=True)
        member.set_password(OLD)
        db.session.add(member)
        db.session.commit()
        stale = _issue_auth_token(1, purpose, timedelta(hours=1), None)
        db.session.flush()
        stale_id = AuthToken.query.one().id
        reset = _issue_auth_token(1, AuthTokenPurpose.PASSWORD_RESET,
                                  timedelta(hours=1), None) if change_method == 'reset' else None
        db.session.commit()

    owner = app.test_client()
    if change_method == 'change':
        login = owner.post('/auth/login', data=dict(email='token-lifecycle@example.com', password=OLD))
        with owner.session_transaction() as session:
            assert session.get('_user_id') == '1'
        assert login.status_code == 302
        first = post_password(owner, '/auth/change-password', CHANGED, OLD)
    else:
        first = post_password(owner, '/auth/reset-password/' + reset, CHANGED)
    assert first['status'] == 302
    with app.app_context():
        assert db.session.get(Member, 1).check_password(CHANGED)
        stale_unused = db.session.get(AuthToken, stale_id).used_at is None
    assert stale_unused

    outsider = app.test_client()
    path = ('/auth/activate/' if purpose == AuthTokenPurpose.ONBOARDING else '/auth/reset-password/') + stale
    second = post_password(outsider, path, FINAL)
    with outsider.session_transaction() as session:
        authenticated = session.get('_user_id') == '1'
    with app.app_context():
        member = db.session.get(Member, 1)
        final_matches = member.check_password(FINAL)
        previous_rejected = not member.check_password(CHANGED)
        token_used = db.session.get(AuthToken, stale_id).used_at is not None
    assert second['status'] == 302 and final_matches and previous_rejected and token_used
    assert authenticated == (purpose == AuthTokenPurpose.ONBOARDING)
    replay = post_password(app.test_client(), path, CHANGED)
    with app.app_context():
        assert db.session.get(Member, 1).check_password(FINAL)
        db.session.remove()
        db.drop_all()
    assert replay['redirect'] == '/auth/login'
    return dict(case=purpose.value + '_after_' + change_method,
                first_change=first, older_token_unused_after_change=stale_unused,
                older_link_response=second, password_overwritten=final_matches,
                previous_password_rejected=previous_rejected,
                older_token_consumed=token_used, full_session=authenticated,
                replay_rejected=True)


results = [probe(purpose, method)
           for purpose in (AuthTokenPurpose.ONBOARDING, AuthTokenPurpose.PASSWORD_RESET)
           for method in ('change', 'reset')]
output = dict(date=datetime.now(timezone.utc).date().isoformat(), groups=len(results), results=results,
              limits='Original issuance helper, forms, login/change/reset/activate routes. Synthetic account and tokens; SQLite memory; no mail or external network. CSRF/rate limits disabled in testing. No MFA, browser, production, concurrent replay or exact expiry-boundary coverage. Token and password values never reported.')
(OUT / 'CREDENTIAL_TOKEN_LIFECYCLE_CHECKS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, indent=2))
