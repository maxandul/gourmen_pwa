"""Original member creation with synthetic data and intercepted mail only."""
from pathlib import Path
from unittest.mock import patch
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.auth_token import AuthToken
from backend.models.audit_event import AuditEvent, AuditAction
from backend.routes.admin import MailService

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []

def probe(mode, retry=False):
    with app.app_context():
        db.create_all()
        db.session.add(Member(id=1,vorname='Audit',nachname='Admin',email='admin@example.com',role=Role.ADMIN,passwort_hash='unused'))
        db.session.commit()
    c = app.test_client()
    with c.session_transaction() as s: s.update(_user_id='1',_fresh=True)
    mail_observations = []
    def send(**kwargs):
        mail_observations.append({'pending_token_in_session':any(isinstance(obj,AuthToken) for obj in db.session.new)})
        if mode == 'mail_exception': raise RuntimeError('Synthetic mail exception')
        return {'success':mode != 'mail_failure', 'error':'Synthetic mail failure' if mode == 'mail_failure' else None}
    def fail(mapper, connection, target):
        wanted = AuditAction.ADMIN_CREATE_MEMBER if mode == 'first_audit_failure' else AuditAction.SEND_ONBOARDING_MAIL
        if target.action == wanted: raise OperationalError('synthetic audit insert',{},Exception('audit-only'))
    inject = mode in ('first_audit_failure','second_audit_failure')
    payload = {
        'vorname':'Audit','nachname':'Neumitglied','email':'new-member@example.com',
        'password':'Synthetic-only-Password-472!', 'role':Role.MEMBER.value,
        'funktion':Funktion.MEMBER.value,'is_active':'y',
        'geburtsdatum':'1990-01-01','beitritt':'2026-09-01'}
    if inject: event.listen(AuditEvent,'before_insert',fail)
    try:
        with patch.object(MailService,'send',side_effect=send):
            r = c.post('/admin/members/new',data=payload)
            response = {'status':r.status_code,'redirect':r.location}
            if r.status_code == 200:
                raise AssertionError('Synthetic form did not reach creation route')
    except (OperationalError, RuntimeError) as exc:
        response = {'exception':type(exc).__name__}
    except Exception as exc:
        if type(exc).__name__ != 'PendingRollbackError': raise
        response = {'exception':type(exc).__name__}
    finally:
        if inject: event.remove(AuditEvent,'before_insert',fail)
    with app.app_context():
        created = Member.query.filter_by(email='new-member@example.com').first()
        result = dict(case=mode,response=response,member_exists=created is not None,
                      token_count=AuthToken.query.count(),
                      audit_actions=[row.action.value for row in AuditEvent.query.all()],
                      intercepted_mail_calls=len(mail_observations),mail_observations=mail_observations)
    if retry:
        with patch.object(MailService,'send',return_value={'success':True}) as resend:
            try:
                repeated = c.post('/admin/members/new',data=payload)
                retry_response = {'status':repeated.status_code}
            except Exception as exc:
                retry_response = {'exception':type(exc).__name__}
        with app.app_context():
            result['retry'] = dict(response=retry_response,mail_calls=resend.call_count,
                matching_members=Member.query.filter_by(email='new-member@example.com').count(),
                token_count=AuthToken.query.count())
    with app.app_context():
        db.session.remove(); db.drop_all()
    with c.session_transaction() as s: result['flash_categories']=[f[0] for f in s.get('_flashes',[])]
    results.append(result)
    return result

if __name__ == '__main__':
    for mode in ('success','mail_failure','first_audit_failure','second_audit_failure','mail_exception'):
        r = probe(mode)
        assert r['member_exists'] and r['intercepted_mail_calls'] == 1
        if mode in ('success','mail_failure'):
            assert r['response']['status'] == 302 and r['token_count'] == 1 and len(r['audit_actions']) == 2
        if mode in ('first_audit_failure','mail_exception'): assert r['token_count'] == 0
        if mode == 'second_audit_failure': assert r['token_count'] == 1 and len(r['audit_actions']) == 1
    output = dict(date='2026-09-28',groups=5,results=results,
                  limits='Original member form/route, hashing and audit helper. MailService.send fully replaced; no message transmitted and no activation URL/token output. SQLite memory, testing CSRF/rate limits disabled, no real member or credentials. Mail exception is injected contract boundary, not a verified normal MailService return.')
    (OUT / 'ONBOARDING_FAILURE_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,indent=2))
