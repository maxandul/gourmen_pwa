"""Original legacy notifier with synthetic subscriptions and replaced transport."""
from pathlib import Path
import runpy,json
from datetime import datetime
from unittest.mock import patch,Mock
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType
from backend.models.participation import Participation
from backend.models.push_subscription import PushSubscription
from backend.services.notifier import NotifierService as Notifier
from backend.services.mail import MailService
from pywebpush import WebPushException
import requests
app=create_app('testing');results=[]
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1,vorname='Audit',nachname='Legacy',email='legacy@example.test',passwort_hash='unused',role=Role.ADMIN))
    db.session.flush()
    db.session.add(Event(id=1,organisator_id=1,datum=datetime(2026,9,20),season=2026,event_typ=EventType.MONATSESSEN,published=True,restaurant='Audit'))
    db.session.add(Participation(event_id=1,member_id=1,teilnahme=True));db.session.commit()
    def seed(active=True):
        row=PushSubscription(member_id=1,endpoint='https://push.example.test/audit',p256dh_key='unused',auth_key='unused',is_active=active)
        db.session.add(row);db.session.commit();return row
    response=requests.Response();response.status_code=503
    for code,error in [('LEG-01',requests.Timeout('synthetic timeout')),('LEG-02',WebPushException('synthetic unavailable',response=response))]:
        seed()
        with patch('backend.services.notifier.webpush',side_effect=error):value=Notifier.send_push_notification(1,'Audit','Audit')
        remaining=PushSubscription.query.count();assert not value and remaining==0
        results.append({'id':code,'scenario':'timeout' if code=='LEG-01' else 'http_503','success':value,'remaining_subscriptions':remaining})
    seed(False)
    with patch('backend.services.notifier.webpush',return_value=Mock(status_code=201)) as transport:
        value=Notifier.send_push_notification(1,'Audit','Audit')
        assert value and transport.call_count==1
        results.append({'id':'LEG-03','scenario':'inactive_subscription','transport_calls':transport.call_count,'timeout_supplied':'timeout' in transport.call_args.kwargs})
    PushSubscription.query.delete();db.session.commit()
    with patch('backend.services.notifier.webpush') as transport,patch.object(MailService,'send') as mail,patch.object(MailService,'send_async') as async_mail:
        client=app.test_client()
        with client.session_transaction() as s:s['_user_id']='1';s['_fresh']=True
        response=client.post('/billbro/1/start_session',follow_redirects=False)
        with client.session_transaction() as s:flashes=list(s.get('_flashes',[]))
        assert response.status_code==302 and any('Push-Nachrichten an 1 Teilnehmer gesendet' in msg for kind,msg in flashes)
        assert transport.call_count==mail.call_count==async_mail.call_count==0
        results.append({'id':'LEG-04','scenario':'billbro_start_without_subscription','http':response.status_code,'flashes':flashes,'push_calls':transport.call_count,'mail_calls':mail.call_count+async_mail.call_count})
    seed()
    value=Notifier.subscribe_user_to_push(1,{'endpoint':'https://push.example.test/second','keys':{'p256dh':'unused','auth':'unused'}})
    endpoints=[r.endpoint for r in PushSubscription.query.all()]
    assert value and endpoints==['https://push.example.test/second']
    results.append({'id':'LEG-05','scenario':'register_second_device','remaining_count':len(endpoints),'old_device_preserved':'https://push.example.test/audit' in endpoints})
    value=Notifier.subscribe_user_to_push(1,{'endpoint':'https://push.example.test/broken'})
    endpoints=[r.endpoint for r in PushSubscription.query.all()]
    assert not value and endpoints==['https://push.example.test/second']
    results.append({'id':'LEG-06','scenario':'invalid_registration_rollback','success':value,'previous_device_preserved':True})
    db.session.remove();db.drop_all()
(OUT/'LEGACY_NOTIFIER_CHECKS.json').write_text(json.dumps({'method':'6 isolated probes; original notifier and BillBro POST, in-memory SQLite, mocked push/mail, no real network; test CSRF disabled','results':results},indent=2,ensure_ascii=False),encoding='utf-8')
print('6 legacy-notifier probes verified')
