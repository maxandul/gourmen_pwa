"""Activation session boundaries with synthetic accounts; no real MFA material."""
from pathlib import Path
from datetime import timedelta
import runpy
import json

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.auth_token import AuthToken, AuthTokenPurpose
from backend.models.audit_event import AuditEvent
app = create_app('testing')
from backend.routes.auth import _issue_auth_token
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
OLD = 'Synthetic-Original-Password-482!'
NEW = 'Synthetic-Changed-Password-593!'
results = []

def seed(mfa=False):
    with app.app_context():
        db.create_all()
        for uid in (1,2):
            m = Member(id=uid,vorname='Audit',nachname=str(uid),email=f'activation{uid}@example.com')
            m.set_password(OLD); db.session.add(m)
        db.session.flush()
        token = _issue_auth_token(1,AuthTokenPurpose.ONBOARDING,timedelta(minutes=10),None)
        if mfa: db.session.add(MemberMFA(member_id=1,is_totp_enabled=True,totp_secret_encrypted='synthetic-unused'))
        db.session.commit()
        return token

def session_state(c):
    with c.session_transaction() as s:
        return {'user_id':s.get('_user_id'),'pending_mfa':s.get('pending_2fa_user_id')}

def clean():
    with app.app_context(): db.session.remove(); db.drop_all()

token = seed(mfa=True)
control = app.test_client()
r = control.post('/auth/login',data={'email':'activation1@example.com','password':OLD})
control_state = session_state(control)
assert r.location == '/auth/2fa/verify' and control_state['user_id'] is None
c = app.test_client()
r = c.post('/auth/activate/'+token,data={'new_password':NEW,'confirm_password':NEW})
activated = session_state(c)
dashboard = c.get('/dashboard/')
assert activated['user_id'] == '1' and activated['pending_mfa'] is None and dashboard.status_code == 200
results.append(dict(case='mfa_enabled_valid_onboarding',login_control=control_state,
                    activation_status=r.status_code,activation_session=activated,dashboard_status=dashboard.status_code))
clean()

token = seed()
c = app.test_client()
with c.session_transaction() as s: s.update(_user_id='2',_fresh=True)
r = c.post('/auth/activate/'+token,data={'new_password':NEW,'confirm_password':NEW})
with app.app_context():
    unchanged = db.session.get(Member,1).check_password(OLD) and AuthToken.query.first().used_at is None
assert unchanged and session_state(c)['user_id'] == '2' and r.location == '/dashboard/'
results.append(dict(case='other_account_already_logged_in',unchanged=unchanged,session=session_state(c),redirect=r.location))
clean()

token = seed()
c = app.test_client()
def fail(*args): raise OperationalError('synthetic audit insert',{},Exception('audit-only'))
event.listen(AuditEvent,'before_insert',fail)
try:
    c.post('/auth/activate/'+token,data={'new_password':NEW,'confirm_password':NEW})
    error = None
except Exception as exc: error = type(exc).__name__
finally: event.remove(AuditEvent,'before_insert',fail)
recovery = app.test_client()
r = recovery.post('/auth/login',data={'email':'activation1@example.com','password':NEW})
assert error == 'PendingRollbackError' and session_state(recovery)['user_id'] == '1'
results.append(dict(case='login_after_activation_audit_failure',activation_error=error,
                    recovery_status=r.status_code,recovery_session=session_state(recovery)))
clean()

output = dict(date='2026-09-28',groups=3,results=results,
              limits='Original routes, synthetic valid unused onboarding token plus directly seeded enabled MFA record, no real TOTP secret/code or MFA setup mutation. Demonstrates conditional route behavior, not prevalence/reachability of that combination in production. SQLite memory; testing CSRF/rate limits disabled. No mail or actual accounts.')
(OUT/'ACTIVATION_SESSION_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
