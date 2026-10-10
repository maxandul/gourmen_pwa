"""Profile/admin audit on synthetic data; no external writes or real sensitive records."""
from pathlib import Path
from unittest.mock import patch
import json
import runpy
import time
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from cryptography.fernet import Fernet
from flask import g
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role,Funktion
from backend.models.member_sensitive import MemberSensitive
from backend.services.security import SecurityService as S
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
app.config['CRYPTO_KEY']=Fernet.generate_key().decode()
results=[]

def client(m,step=False):
    g.pop('_login_user',None)
    c=app.test_client()
    with c.session_transaction() as s:
        s['_user_id']=str(m.id);s['_fresh']=True
        if step:s['sensitive_access_until']=int(time.time())+600
    return c

def run(name,fn):
    with app.app_context():
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'profile{i}@example.com',passwort_hash='unused') for i in range(3)]
        ms[0].role=Role.ADMIN
        db.session.add_all(ms);db.session.commit()
        try:results.append({'case':name,'result':fn(ms)})
        finally:db.session.remove();db.drop_all()

def profile_data(m,**extra):
    values={'profile-vorname':m.vorname,'profile-nachname':m.nachname,'profile-email':m.email,
            'profile-nationalitaet':'','profile-zimmerwunsch':'','active_tab':'profile'}
    values.update(extra);return values

def duplicate(ms):
    try:
        r=client(ms[1]).post('/member/profile',data=profile_data(ms[1],**{'profile-email':ms[2].email}))
        error=None;status=r.status_code
    except Exception as exc:
        error=type(exc).__name__;status=None;db.session.rollback()
    return {'error':error,'http':status,'original_email_retained':ms[1].email=='profile1@example.com'}
run('profile_duplicate_email',duplicate)

def negative(ms):
    r=client(ms[1]).post('/member/profile',data=profile_data(ms[1],**{'profile-koerpergroesse':'-5','profile-koerpergewicht':'-2','profile-schuhgroesse':'-1'}))
    return {'http':r.status_code,'height':ms[1].koerpergroesse,'weight':ms[1].koerpergewicht,'shoe':ms[1].schuhgroesse}
run('negative_physical_values',negative)

def clear(ms):
    ms[1].telefon='synthetic';db.session.commit()
    r=client(ms[1]).post('/member/profile',data=profile_data(ms[1],**{'profile-telefon':'','role':'ADMIN','profile-role':'ADMIN','is_active':''}))
    return {'http':r.status_code,'phone_cleared':not ms[1].telefon,'role':ms[1].role.value,'active':ms[1].is_active}
run('clear_optional_and_ignore_privileged_fields',clear)

def admin_number(ms):
    data={'vorname':'Audit','nachname':'1','email':ms[1].email,'role':'MEMBER','is_active':'y',
          'funktion':Funktion.MEMBER.value,'geburtsdatum':'1990-01-01','beitritt':'2020-01-01',
          'nationalitaet':'','zimmerwunsch':'','koerpergroesse':'abc'}
    try:
        r=client(ms[0]).post(f'/admin/members/{ms[1].id}/edit',data=data)
        error=None;status=r.status_code
    except Exception as exc:
        error=type(exc).__name__;status=None;db.session.rollback()
    return {'http':status,'error':error,'height':ms[1].koerpergroesse}
run('admin_invalid_numeric_field',admin_number)

def decrypt_failure(ms,admin=False):
    ciphertext=S.encrypt_json({'allergien':'synthetic-only'})
    db.session.add(MemberSensitive(member_id=ms[1].id,payload_encrypted=ciphertext));db.session.commit()
    c=client(ms[0] if admin else ms[1],step=True)
    path=f'/admin/members/{ms[1].id}/sensitive' if admin else '/member/profile?tab=sensitive'
    with patch.object(S,'decrypt_json',side_effect=RuntimeError('synthetic temporary decrypt failure')):
        try:r=c.get(path);status=r.status_code;error=None
        except Exception as exc:status=None;error=type(exc).__name__
    return {'http':status,'error':error,'sensitive_rows_after_get':MemberSensitive.query.count()}
run('self_sensitive_get_deletes_on_error',decrypt_failure)
run('admin_sensitive_get_deletes_on_error',lambda ms:decrypt_failure(ms,True))

def healthy_admin(ms):
    db.session.add(MemberSensitive(member_id=ms[1].id,payload_encrypted=S.encrypt_json({'allergien':'synthetic-only'})))
    db.session.commit()
    try:r=client(ms[0],step=True).get(f'/admin/members/{ms[1].id}/sensitive');status=r.status_code;error=None
    except Exception as exc:status=None;error=type(exc).__name__
    return {'http':status,'error':error,'sensitive_rows':MemberSensitive.query.count()}
run('admin_sensitive_valid_data_render',healthy_admin)

def permissions(ms):
    edit=client(ms[1]).get(f'/admin/members/{ms[2].id}/edit')
    other=client(ms[1],step=True).get(f'/admin/members/{ms[2].id}/sensitive')
    own=client(ms[1]).get('/member/profile?tab=sensitive')
    return {'admin_edit_http':edit.status_code,'other_sensitive_http':other.status_code,
            'own_sensitive_without_step_http':own.status_code,'own_location':own.headers.get('Location')}
run('member_admin_and_sensitive_guards',permissions)
(OUT/'PROFILE_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
