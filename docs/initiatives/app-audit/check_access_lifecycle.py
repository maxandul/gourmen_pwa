"""Synthetic Google/calendar/admin lifecycle audit. Mail and Drive fully mocked."""
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlsplit
import json
import re
import runpy
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role,Funktion
from backend.models.auth_token import AuthTokenPurpose
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
app.config['DRIVE_FEATURE_ENABLED']=True
from backend.routes.auth import _issue_auth_token
results=[]

def client(m=None):
    g.pop('_login_user',None)
    c=app.test_client()
    if m:
        with c.session_transaction() as s:s['_user_id']=str(m.id);s['_fresh']=True
    return c

def run(name,fn):
    with app.app_context():
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'access{i}@example.com',passwort_hash='unused') for i in range(2)]
        ms[0].role=Role.ADMIN
        db.session.add_all(ms);db.session.commit()
        try:results.append({'case':name,'result':fn(ms)})
        finally:db.session.remove();db.drop_all()

def changed_address(ms):
    invited=[]
    with patch('backend.routes.member.MailService.send_async') as mail, patch('backend.services.drive_storage.DriveStorageService.invite_member_to_drive',side_effect=lambda m:invited.append(m.google_email)):
        c=client(ms[1])
        c.post('/member/google-email/save',data={'google_email':'old-audit@example.com'})
        text=mail.call_args.kwargs['text']
        link=re.search(r'https?://\S+/member/google-email/verify/\S+',text).group()
        c.post('/member/google-email/save',data={'google_email':'new-audit@example.com'})
        r=client().get(urlsplit(link).path)
    return {'http':r.status_code,'current_address':ms[1].google_email,
            'verified_by_old_address_link':ms[1].google_email_verified,'invited_addresses':invited}
run('old_email_token_verifies_new_address',changed_address)

def no_revoke(ms):
    ms[1].google_email='old-audit@example.com';ms[1].google_email_verified=True;db.session.commit()
    with patch('backend.routes.member.MailService.send_async'),patch('backend.services.drive_storage.DriveStorageService.remove_member_from_drive') as revoke:
        r=client(ms[1]).post('/member/google-email/save',data={'google_email':'new-audit@example.com'})
    return {'http':r.status_code,'verified':ms[1].google_email_verified,'drive_removal_calls':revoke.call_count}
run('google_address_change_no_revoke',no_revoke)

def inactive_google(ms):
    ms[1].google_email='audit@example.com';ms[1].is_active=False
    token=_issue_auth_token(ms[1].id,AuthTokenPurpose.GOOGLE_EMAIL_VERIFY,timedelta(minutes=5),None)
    db.session.commit()
    with patch('backend.services.drive_storage.DriveStorageService.invite_member_to_drive') as invite:
        r=client().get('/member/google-email/verify/'+token)
    return {'http':r.status_code,'verified':ms[1].google_email_verified,'invites':invite.call_count}
run('inactive_google_verification_guard',inactive_google)

def calendar(ms):
    c=client(ms[1])
    first=c.post('/member/settings/calendar/enable');old=urlsplit(first.json['feed_url']).path
    again=c.post('/member/settings/calendar/enable')
    public=client();before=public.get(old)
    c=client(ms[1]);new=c.post('/member/settings/calendar/regenerate');newpath=urlsplit(new.json['feed_url']).path
    public=client();old_status=public.get(old).status_code;new_status=public.get(newpath).status_code
    c=client(ms[1]);disabled=c.post('/member/settings/calendar/disable')
    after=client().get(newpath).status_code
    return {'enable':first.status_code,'repeat_enable':again.status_code,
            'same_token_on_repeat':first.json==again.json,'before':before.status_code,
            'old_after_regenerate':old_status,'new_after_regenerate':new_status,
            'disable':disabled.status_code,'new_after_disable':after}
run('calendar_enable_regenerate_disable',calendar)

def inactive_calendar(ms):
    c=client(ms[1]);r=c.post('/member/settings/calendar/enable');path=urlsplit(r.json['feed_url']).path
    ms[1].is_active=False;db.session.commit()
    return {'inactive_feed_http':client().get(path).status_code}
run('inactive_calendar_guard',inactive_calendar)

def admin_data(m):
    return {'vorname':m.vorname,'nachname':m.nachname,'email':m.email,'role':'MEMBER','is_active':'y',
            'funktion':Funktion.MEMBER.value,'geburtsdatum':'1990-01-01','beitritt':'2020-01-01',
            'nationalitaet':'','zimmerwunsch':''}

def last_admin(ms):
    r=client(ms[0]).post(f'/admin/members/{ms[0].id}/edit',data=admin_data(ms[0]))
    return {'http':r.status_code,'remaining_active_admins':Member.query.filter_by(role=Role.ADMIN,is_active=True).count(),
            'former_admin_edit_http':client(ms[0]).get(f'/admin/members/{ms[1].id}/edit').status_code}
run('last_admin_self_demotion',last_admin)

def deactivate_drive(ms):
    ms[1].google_email='audit@example.com';ms[1].google_email_verified=True;db.session.commit()
    data=admin_data(ms[1]);data.pop('is_active')
    with patch('backend.services.drive_storage.DriveStorageService.remove_member_from_drive') as revoke:
        r=client(ms[0]).post(f'/admin/members/{ms[1].id}/edit',data=data)
    return {'http':r.status_code,'active':ms[1].is_active,'drive_removal_calls':revoke.call_count}
run('member_deactivation_no_drive_revoke',deactivate_drive)
(OUT/'ACCESS_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
