"""Auth audit with real local password verification, synthetic accounts and blocked network."""
from pathlib import Path
from datetime import datetime, timedelta
import json
import runpy
OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'), run_name='audit_setup')
from flask import g
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.auth_token import AuthTokenPurpose
app = create_app('testing')
from backend.routes.auth import _issue_auth_token, _resolve_auth_token
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
PASSWORD = 'Audit-only-Secret-482!'
NEW_PASSWORD = 'Audit-only-Changed-593!'
results = []

def req(c, method, url, **kwargs):
    # Outer app context must not carry Flask-Login's cached identity across requests.
    g.pop('_login_user', None)
    return getattr(c, method)(url, **kwargs)

def login(c, m, suffix=''):
    return req(c,'post','/auth/login'+suffix,data={'email':m.email,'password':PASSWORD})

def run(name, fn):
    with app.app_context():
        db.create_all()
        ms = [Member(vorname='Audit',nachname=str(i),email=f'auth{i}@example.com') for i in range(2)]
        for m in ms: m.set_password(PASSWORD)
        db.session.add_all(ms); db.session.commit()
        try: results.append({'case':name,'result':fn(ms)})
        finally: db.session.remove(); db.drop_all()

def inactive(ms):
    c=app.test_client(); login(c,ms[0])
    ms[0].is_active=False; db.session.commit()
    r=req(c,'get','/member/profile')
    fresh=app.test_client(); r2=login(fresh,ms[0])
    with fresh.session_transaction() as s: fresh_logged_in='_user_id' in s
    return {'existing_session_http':r.status_code,'existing_location':r.headers.get('Location'),
            'fresh_login_http':r2.status_code,'fresh_logged_in':fresh_logged_in}
run('deactivated_account_sessions',inactive)

def step_transfer(ms):
    c=app.test_client(); login(c,ms[0])
    step=req(c,'post','/auth/step-up',data={'password':PASSWORD})
    req(c,'get','/auth/logout'); login(c,ms[1])
    r=req(c,'get','/member/profile?tab=sensitive')
    with c.session_transaction() as s:
        retained=bool(s.get('sensitive_access_until')); identity=s.get('_user_id')
    return {'step_http':step.status_code,'second_member_sensitive_http':r.status_code,
            'step_up_retained':retained,'second_member_logged_in':identity==str(ms[1].id)}
run('step_up_cross_account_after_logout',step_transfer)

def mandatory(ms):
    ms[0].password_changed_at=None; db.session.commit()
    c=app.test_client(); first=login(c,ms[0])
    profile=req(c,'get','/member/profile')
    c2=app.test_client(); bypass=login(c2,ms[0],'?next=/member/profile')
    return {'normal_location':first.headers.get('Location'),'profile_http':profile.status_code,
            'with_next_location':bypass.headers.get('Location'),'still_needs_change':ms[0].needs_password_change}
run('first_password_change_bypass',mandatory)

def redirect(ms):
    r=login(app.test_client(),ms[0],'?next=//example.invalid/audit')
    return {'http':r.status_code,'location':r.headers.get('Location')}
run('login_protocol_relative_redirect',redirect)

def mfa_next(ms):
    db.session.add(MemberMFA(member_id=ms[0].id,is_totp_enabled=True,totp_secret_encrypted='unused-synthetic'))
    db.session.commit()
    c=app.test_client(); r=login(c,ms[0],'?next=/member/profile')
    with c.session_transaction() as s:
        return {'location':r.headers.get('Location'),'pending':s.get('pending_2fa_user_id')==ms[0].id,
                'return_target_in_session':any('/member/profile' in str(v) for v in s.values())}
run('mfa_login_loses_return_target',mfa_next)

def reset_sessions(ms):
    old=app.test_client(); login(old,ms[0])
    token=_issue_auth_token(ms[0].id,AuthTokenPurpose.PASSWORD_RESET,timedelta(minutes=10),None)
    db.session.commit()
    public=app.test_client()
    r=req(public,'post','/auth/reset-password/'+token,data={'new_password':NEW_PASSWORD,'confirm_password':NEW_PASSWORD})
    old_r=req(old,'get','/member/profile')
    _,reuse=_resolve_auth_token(token,AuthTokenPurpose.PASSWORD_RESET)
    return {'reset_http':r.status_code,'password_changed':ms[0].check_password(NEW_PASSWORD),
            'old_session_http':old_r.status_code,'token_reuse':reuse}
run('reset_password_existing_session',reset_sessions)

def tokens(ms):
    expired=_issue_auth_token(ms[0].id,AuthTokenPurpose.PASSWORD_RESET,timedelta(seconds=-1),None)
    valid=_issue_auth_token(ms[0].id,AuthTokenPurpose.PASSWORD_RESET,timedelta(minutes=10),None)
    db.session.commit()
    _,e=_resolve_auth_token(expired,AuthTokenPurpose.PASSWORD_RESET)
    _,missing=_resolve_auth_token('synthetic-nonexistent',AuthTokenPurpose.PASSWORD_RESET)
    other=next(p for p in AuthTokenPurpose if p!=AuthTokenPurpose.PASSWORD_RESET)
    _,purpose=_resolve_auth_token(valid,other)
    return {'expired':e,'unknown':missing,'wrong_purpose':purpose}
run('token_expiry_and_purpose_guards',tokens)

(OUT/'AUTH_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
