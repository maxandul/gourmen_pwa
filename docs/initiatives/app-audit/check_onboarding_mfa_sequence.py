"""Original create/login/MFA/activate route chain with intercepted mail only."""
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
import runpy
import json
import logging
import re

OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT/'check_onboarding_failures.py'),run_name='audit_helper')
app, db = ns['app'], ns['db']
Member, Role, Funktion = ns['Member'], ns['Role'], ns['Funktion']
from cryptography.fernet import Fernet
import pyotp
from backend.models.member_mfa import MemberMFA
from backend.models.auth_token import AuthToken

# Memory-only fixture key; never modifies ENV or any real encryption key.
app.config['CRYPTO_KEY'] = Fernet.generate_key().decode()
# App debug logging includes MFA material; suppress during synthetic enrollment.
logging.disable(logging.CRITICAL)
INITIAL = 'Synthetic-Initial-Password-482!'
FINAL = 'Synthetic-Activation-Password-593!'
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1,vorname='Audit',nachname='Admin',email='admin@example.com',role=Role.ADMIN,passwort_hash='unused'))
    db.session.commit()
admin = app.test_client()
with admin.session_transaction() as s: s.update(_user_id='1',_fresh=True)
captured = {}
def mail(**kwargs):
    captured['path'] = urlsplit(re.search(r'Aktiviere deinen Account hier: (\S+)',kwargs['text']).group(1)).path
    return {'success':True}
with patch.object(ns['MailService'],'send',side_effect=mail):
    created = admin.post('/admin/members/new',data={
        'vorname':'Audit','nachname':'Sequence','email':'sequence@example.com',
        'password':INITIAL,'role':Role.MEMBER.value,'funktion':Funktion.MEMBER.value,
        'is_active':'y','geburtsdatum':'1990-01-01','beitritt':'2026-09-01'})
assert created.status_code == 302
owner = app.test_client()
logged_in = owner.post('/auth/login',data={'email':'sequence@example.com','password':INITIAL})
with owner.session_transaction() as s: initial_session = '_user_id' in s
assert initial_session
enroll_get = owner.get('/auth/2fa/enroll')
with owner.session_transaction() as s: secret = s['2fa_secret']
enrolled = owner.post('/auth/2fa/enroll',data={'token':pyotp.TOTP(secret).now()})
with app.app_context():
    user = Member.query.filter_by(email='sequence@example.com').one()
    uid = user.id
    mfa_enabled = MemberMFA.query.filter_by(member_id=uid).one().is_totp_enabled
    token_unused = AuthToken.query.filter_by(member_id=uid).one().used_at is None
assert mfa_enabled and token_unused
control = app.test_client()
normal = control.post('/auth/login',data={'email':'sequence@example.com','password':INITIAL})
with control.session_transaction() as s:
    requires_mfa = s.get('pending_2fa_user_id') == uid and '_user_id' not in s
assert requires_mfa
activation_client = app.test_client()
activated = activation_client.post(captured['path'],data={'new_password':FINAL,'confirm_password':FINAL})
with activation_client.session_transaction() as s:
    full_session = s.get('_user_id') == str(uid)
    no_mfa_challenge = 'pending_2fa_user_id' not in s
dashboard = activation_client.get('/dashboard/')
assert full_session and no_mfa_challenge and dashboard.status_code == 200
output = dict(date='2026-10-10',groups=1,steps={
    'admin_create_status':created.status_code,'initial_password_login_status':logged_in.status_code,
    'initial_password_login_authenticated':initial_session,'enroll_get_status':enroll_get.status_code,
    'enroll_post_status':enrolled.status_code,'mfa_enabled_after_original_enrollment':mfa_enabled,
    'onboarding_token_still_unused':token_unused,'normal_login_requires_mfa':requires_mfa,
    'activation_status':activated.status_code,'activation_full_session':full_session,
    'activation_no_mfa_challenge':no_mfa_challenge,'dashboard_status':dashboard.status_code},
    limits='Complete original route chain, SQLite memory, synthetic account and local TOTP. Only mail transmission intercepted. Testing CSRF/rate limits disabled; memory-only crypto key. No real mail, credentials, production account or MFA secret output. Requires valid still-unused activation link within validity period; possession/frequency in production not measured.')
(OUT/'ONBOARDING_MFA_SEQUENCE_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output,indent=2))
