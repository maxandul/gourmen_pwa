"""Cross-module audit failure probes, synthetic users/events and memory database."""
from pathlib import Path
from datetime import datetime, timedelta
import runpy
import json

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role
from backend.models.event import Event, EventType
from backend.models.participation import Participation
from backend.models.audit_event import AuditEvent

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []

def seed():
    with app.app_context():
        db.create_all()
        m = Member(id=1, vorname='Audit', nachname='Routes', email='audit-routes@example.com', role=Role.ADMIN)
        m.set_password('SyntheticAuditOnly-472!')
        db.session.add(m); db.session.flush()
        db.session.add(Event(id=1, organisator_id=1, datum=datetime.now()+timedelta(days=10),
                            event_typ=EventType.MONATSESSEN, season=2026, restaurant='Audit', published=True))
        db.session.flush()
        db.session.add(Participation(member_id=1, event_id=1, teilnahme=False))
        db.session.commit()

def state():
    with app.app_context():
        p = Participation.query.filter_by(member_id=1, event_id=1).first()
        return dict(event_exists=db.session.get(Event,1) is not None,
                    participation=p.teilnahme if p else None,
                    calendar_enabled=bool(db.session.get(Member,1).ical_token),
                    audit_count=AuditEvent.query.count())

def fail(*args):
    raise OperationalError('synthetic audit insert', {}, Exception('audit-only failure'))

def probe(name, url, login=False, retry=False):
    seed()
    c = app.test_client()
    if not login:
        with c.session_transaction() as s: s.update(_user_id='1', _fresh=True)
    data = {'email':'audit-routes@example.com','password':'SyntheticAuditOnly-472!'} if login else {}
    event.listen(AuditEvent, 'before_insert', fail)
    try:
        response = c.post(url, data=data)
        response_data = dict(status=response.status_code, redirect=response.location)
    except Exception as exc:
        response_data = dict(exception=type(exc).__name__)
    finally:
        event.remove(AuditEvent, 'before_insert', fail)
    result = dict(case=name, response=response_data, durable_after_failure=state())
    if retry:
        response = c.post(url, data=data)
        result['retry_status'] = response.status_code
        result['durable_after_retry'] = state()
    with c.session_transaction() as s: result['session_authenticated'] = '_user_id' in s
    results.append(result)
    with app.app_context(): db.session.remove(); db.drop_all()
    return result

default = probe('login_default_redirect', '/auth/login', login=True)
assert default['response'].get('exception') == 'PendingRollbackError', default
explicit = probe('login_explicit_next', '/auth/login?next=/dashboard/', login=True)
assert explicit['response']['status'] == 302
rsvp = probe('rsvp_failure_then_retry', '/events/1/rsvp', retry=True)
assert rsvp['response'].get('exception') == 'PendingRollbackError'
assert rsvp['durable_after_failure']['participation'] is True
assert rsvp['durable_after_retry']['participation'] is False
calendar = probe('calendar_enable', '/member/settings/calendar/enable')
assert calendar['response']['status'] == 201 and calendar['durable_after_failure']['calendar_enabled']
deleted = probe('event_delete', '/events/1/delete')
assert deleted['response'].get('exception') == 'PendingRollbackError' and deleted['durable_after_failure']['event_exists']
output = dict(date='2026-09-21', groups=5, results=results,
              limits='Original Flask routes and audit helper. Synthetic audit insert error through ORM before_insert; SQLite memory; real local password verification, no real credentials. Exceptions propagate in testing, no claim about production HTTP body. Global testing CSRF/rate limits disabled. Fresh app context per request/state inspection. No emails, Drive or production operations.')
(OUT / 'AUDIT_FAILURE_ROUTE_CHECKS.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
print(json.dumps(output, indent=2))
