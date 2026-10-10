"""Synthetic MFA audit; real TOTP/hashing; generated test secrets never output."""
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
import json
import runpy
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from cryptography.fernet import Fernet
import pyotp
from flask import g
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.member_mfa import MemberMFA
from backend.models.mfa_backup_code import MFABackupCode
from backend.models.auth_token import AuthTokenPurpose
from backend.services.security import SecurityService as S
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
# Fresh memory-only key for synthetic fixtures; no environment or production key changed.
app.config['CRYPTO_KEY']=Fernet.generate_key().decode()
from backend.routes.auth import _issue_auth_token, _resolve_auth_token
PASSWORD='Audit-only-Secret-482!'
results=[]

def req(c,method,url,**kw):
    g.pop('_login_user',None)
    return getattr(c,method)(url,**kw)

def login(c,m):
    return req(c,'post','/auth/login',data={'email':m.email,'password':PASSWORD})

def logged_in(c):
    with c.session_transaction() as s: return '_user_id' in s

def enable_fixture(m):
    secret=pyotp.random_base32()
    row=MemberMFA(member_id=m.id,is_totp_enabled=True,totp_secret_encrypted=S.encrypt_json(secret))
    db.session.add(row);db.session.commit()
    return secret,row

def run(name,fn):
    with app.app_context():
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'mfa{i}@example.com') for i in range(2)]
        for m in ms:m.set_password(PASSWORD)
        db.session.add_all(ms);db.session.commit()
        # App currently logs TOTP secrets/codes. Capture only in memory, output booleans.
        try:
            with patch.object(app.logger,'info') as logs:
                results.append({'case':name,'result':fn(ms,logs)})
        finally:db.session.remove();db.drop_all()

def backup(ms,logs):
    enable_fixture(ms[0]);raw='AUDIT123'
    row=MFABackupCode(member_id=ms[0].id,code_hash=S.hash_backup_code(raw))
    db.session.add(row);db.session.commit()
    c=app.test_client();login(c,ms[0])
    r=req(c,'post','/auth/2fa/verify',data={'backup_code':raw})
    return {'stored_hash_verifies':S.check_backup_code(row.code_hash,raw),'http':r.status_code,
            'authenticated':logged_in(c),'used':row.used_at is not None}
run('valid_backup_code_rejected',backup)

def totp(ms,logs):
    secret,row=enable_fixture(ms[0]);code=pyotp.TOTP(secret).now()
    statuses=[]
    for _ in range(2):
        c=app.test_client();login(c,ms[0])
        r=req(c,'post','/auth/2fa/verify',data={'token':code})
        statuses.append({'http':r.status_code,'authenticated':logged_in(c)})
    captured=' '.join(str(call) for call in logs.call_args_list)
    return {'same_code_attempts':statuses,'submitted_code_in_log':code in captured}
run('totp_repeat_and_logging',totp)

def enroll(c):
    req(c,'get','/auth/2fa/enroll')
    with c.session_transaction() as s: secret=s['2fa_secret']
    r=req(c,'post','/auth/2fa/enroll',data={'token':pyotp.TOTP(secret).now()})
    return secret,r

def pretrust(ms,logs):
    c=app.test_client();login(c,ms[0])
    trusted=req(c,'post','/auth/2fa/remember-device')
    secret,r=enroll(c)
    req(c,'get','/auth/logout');again=login(c,ms[0])
    captured=' '.join(str(call) for call in logs.call_args_list)
    return {'remember_before_mfa_http':trusted.status_code,'enrollment_http':r.status_code,
            'subsequent_location':again.headers.get('Location'),'authenticated_without_new_totp':logged_in(c),
            'enrollment_secret_in_log':secret in captured}
run('trust_created_before_mfa_enrollment',pretrust)

def reenable(ms,logs):
    secret,mfa=enable_fixture(ms[0])
    old=MFABackupCode(member_id=ms[0].id,code_hash=S.hash_backup_code('AUDIT123'))
    db.session.add(old);db.session.commit()
    c=app.test_client();login(c,ms[0]);req(c,'post','/auth/2fa/verify',data={'token':pyotp.TOTP(secret).now()})
    req(c,'post','/auth/2fa/disable',data={'password':PASSWORD})
    _,r=enroll(c)
    follow=req(c,'get',r.headers['Location'])
    return {'reenabled':mfa.is_totp_enabled,'backup_page_http':follow.status_code,
            'total_codes':MFABackupCode.query.count(),
            'valid_codes':sum(x.is_valid for x in MFABackupCode.query.all())}
run('reenrollment_cannot_get_fresh_backup_codes',reenable)

def cross(ms,logs):
    c=app.test_client();login(c,ms[0]);req(c,'get','/auth/2fa/enroll')
    with c.session_transaction() as s: first=s['2fa_secret']
    req(c,'get','/auth/logout');login(c,ms[1]);req(c,'get','/auth/2fa/enroll')
    with c.session_transaction() as s: second=s['2fa_secret']
    return {'same_setup_secret_across_accounts':first==second}
run('enrollment_secret_survives_account_switch',cross)

def reset(ms,logs):
    secret,mfa=enable_fixture(ms[0])
    c=app.test_client();login(c,ms[0])
    req(c,'post','/auth/2fa/verify',data={'token':pyotp.TOTP(secret).now(),'remember_device':'on'})
    req(c,'get','/auth/logout')
    token=_issue_auth_token(ms[0].id,AuthTokenPurpose.MFA_RESET,timedelta(minutes=10),None)
    db.session.commit()
    reset_response=req(app.test_client(),'get','/auth/2fa/reset/'+token)
    disabled=not mfa.is_totp_enabled
    _,error=_resolve_auth_token(token,AuthTokenPurpose.MFA_RESET)
    owner=app.test_client();login(owner,ms[0]);enroll(owner)
    again=login(c,ms[0])
    return {'reset_get_http':reset_response.status_code,'disabled_by_get':disabled,
            'token_after_get':error,'old_device_location':again.headers.get('Location'),
            'old_device_authenticated_without_new_totp':logged_in(c)}
run('reset_get_and_old_device_after_reenroll',reset)

def negative(ms,logs):
    secret,mfa=enable_fixture(ms[0])
    code='000000'
    while pyotp.TOTP(secret).verify(code,valid_window=3):
        code=f'{int(code)+1:06d}'
    c=app.test_client();login(c,ms[0])
    r=req(c,'post','/auth/2fa/verify',data={'token':code})
    anonymous=req(app.test_client(),'post','/auth/2fa/remember-device')
    return {'invalid_totp_http':r.status_code,'invalid_totp_authenticated':logged_in(c),
            'anonymous_remember_http':anonymous.status_code,
            'anonymous_remember_location':anonymous.headers.get('Location')}
run('invalid_totp_and_anonymous_device_guards',negative)

(OUT/'MFA_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
