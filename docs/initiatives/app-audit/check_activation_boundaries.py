"""Original activation route, synthetic account/token and local password checks."""
from pathlib import Path
from datetime import timedelta
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.audit_event import AuditEvent

app = create_app('testing')
from backend.routes.auth import _issue_auth_token
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []
NEW_PASSWORD = 'Synthetic-Activation-Password-593!'

def snapshot():
    with app.app_context():
        member = db.session.get(Member,1)
        return dict(password_changed=member.check_password(NEW_PASSWORD),
                    token_used=AuthToken.query.first().used_at is not None,
                    audit_count=AuditEvent.query.count())

def probe(mode):
    with app.app_context():
        db.create_all()
        member = Member(id=1,vorname='Audit',nachname='Aktivierung',email='activation@example.com',is_active=mode != 'inactive')
        member.set_password('Synthetic-Old-Password-482!')
        db.session.add(member); db.session.commit()
        token = _issue_auth_token(1,AuthTokenPurpose.PASSWORD_RESET if mode == 'wrong_purpose' else AuthTokenPurpose.ONBOARDING,
                                 timedelta(minutes=-1 if mode == 'expired' else 10),None)
        db.session.commit()
    c = app.test_client()
    def fail(*args): raise OperationalError('synthetic audit insert',{},Exception('audit-only'))
    if mode == 'audit_failure': event.listen(AuditEvent,'before_insert',fail)
    password = 'weak' if mode == 'invalid_password' else NEW_PASSWORD
    try:
        response = c.post('/auth/activate/'+token,data={'new_password':password,'confirm_password':password})
        outcome = {'status':response.status_code,'redirect':response.location}
    except Exception as exc:
        outcome = {'exception':type(exc).__name__}
    finally:
        if mode == 'audit_failure': event.remove(AuditEvent,'before_insert',fail)
    with c.session_transaction() as s: authenticated = '_user_id' in s
    result = dict(case=mode,response=outcome,state=snapshot(),authenticated=authenticated)
    if mode in ('success','audit_failure'):
        # Fresh unauthenticated client checks actual token reuse guard.
        replay = app.test_client().post('/auth/activate/'+token,data={'new_password':NEW_PASSWORD,'confirm_password':NEW_PASSWORD})
        result['replay_status'] = replay.status_code
        result['replay_redirect'] = replay.location
        result['state_after_replay'] = snapshot()
    results.append(result)
    with app.app_context(): db.session.remove(); db.drop_all()
    return result

for mode in ('success','expired','inactive','wrong_purpose','invalid_password','audit_failure'):
    r = probe(mode)
    if mode == 'success':
        assert r['response']['status'] == 302 and r['authenticated'] and r['state']['token_used'] and r['state']['audit_count'] == 1
    elif mode == 'audit_failure':
        assert r['response'].get('exception') == 'PendingRollbackError' and not r['authenticated']
        assert r['state']['token_used'] and r['state']['password_changed'] and r['state']['audit_count'] == 0
    else:
        assert not r['state']['token_used'] and not r['state']['password_changed'] and not r['authenticated']
        assert r['response']['status'] == (200 if mode == 'invalid_password' else 302)
    if mode in ('success','audit_failure'):
        assert r['replay_redirect'] == '/auth/login' and r['state_after_replay'] == r['state']
output = dict(date='2026-09-28',groups=6,results=results,
              limits='Original form/route and local hashing; SQLite memory and testing CSRF/rate limits disabled. Tokens/passwords synthetic and never printed. No real mail/account changes. No browser, exact expiry instant, concurrent replay or MFA-enabled activation test.')
(OUT / 'ACTIVATION_BOUNDARY_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
