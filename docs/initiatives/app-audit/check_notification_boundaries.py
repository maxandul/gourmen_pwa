"""Synthetic reminder records and replaced delivery; no real sends or credentials."""
from pathlib import Path
import runpy,json
from datetime import datetime,timedelta
from unittest.mock import patch,Mock
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import Flask
from backend.app import create_app
from backend.config import ProductionConfig
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType
from backend.models.push_subscription import PushSubscription
from backend.services.push_notifications import PushNotificationService as Push
from backend.services.mail import MailService
from backend.routes.cron import bp
results=[]
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1,vorname='Audit',nachname='Reminder',email='audit@example.test',passwort_hash='unused',role=Role.ADMIN))
    db.session.flush()
    db.session.add(Event(id=1,organisator_id=1,datum=datetime.utcnow()+timedelta(days=21),season=2026,event_typ=EventType.MONATSESSEN,published=True,restaurant='Audit'))
    db.session.add(PushSubscription(id=1,member_id=1,endpoint='https://push.example.test/audit',p256dh_key='unused',auth_key='unused'))
    db.session.commit()
    with patch.object(Push,'send_event_reminder_to_organizer',return_value=True) as organizer,patch.object(Push,'send_participation_reminder_to_members',return_value={'success':True,'sent_count':1}) as members:
        first=Push.check_and_send_3_week_reminders();second=Push.check_and_send_3_week_reminders()
        assert organizer.call_count==members.call_count==2
        results.append({'id':'NOT-01','scenario':'same_event_two_sequential_runs','organizer_calls':organizer.call_count,'member_batch_calls':members.call_count,'processed':[first['processed_events'],second['processed_events']]})
    with patch.object(Push,'send_event_reminder_to_organizer',return_value=False),patch.object(Push,'send_participation_reminder_to_members',return_value={'success':False,'sent_count':0,'message':'synthetic failure'}):
        value=Push.check_and_send_3_week_reminders()
        assert value['success'] is True and value['results'][0]['member_reminders']['success'] is False
        results.append({'id':'NOT-02','scenario':'all_deliveries_fail','batch_success':value['success'],'processed':value['processed_events'],'organizer_sent':value['results'][0]['organizer_reminder_sent'],'members_success':value['results'][0]['member_reminders']['success']})
    for status in [410,503]:
        subscription=db.session.get(PushSubscription,1);subscription.is_active=True;db.session.commit()
        with patch.object(Push,'send_push_notification',return_value={'success':False,'status':status}):
            Push._send_with_cleanup(subscription,{})
        db.session.expire_all()
        active=db.session.get(PushSubscription,1).is_active
        assert active==(status!=410)
        results.append({'id':'NOT-03' if status==410 else 'NOT-04','scenario':f'push_status_{status}','subscription_active':active})
    with patch('backend.services.mail.threading.Thread') as thread,patch.object(MailService,'send') as send:
        value=MailService.send_async('audit@example.test','Audit','Audit')
        assert value['queued'] and thread.call_args.kwargs['daemon'] and send.call_count==0
        results.append({'id':'NOT-05','scenario':'async_returns_before_delivery','result':value,'daemon':thread.call_args.kwargs['daemon'],'send_calls_before_worker':send.call_count})
        send.return_value={'success':False,'error':'synthetic failure'}
        with patch('backend.services.mail.logger') as logger:thread.call_args.kwargs['target']()
        assert logger.warning.called
        results.append({'id':'NOT-06','scenario':'async_worker_failure','caller_result_still_success':value['success'],'warning_logged':logger.warning.called})
    import run_cron_reminders
    from backend.services.cron_service import CronService
    with patch('backend.app.create_app',return_value=app),patch.object(CronService,'run_3_week_reminders',return_value={'success':True,'processed_events':1,'results':[{'event_id':1,'event_name':'Audit','organizer_reminder_sent':False,'member_reminders':{'success':False,'sent_count':0}}]}),patch.object(CronService,'run_weekly_reminders',return_value={'success':True,'processed_events':0,'results':[]}),patch.object(CronService,'run_rating_reminders',return_value={'success':True,'processed_events':0,'results':[]}),patch.object(run_cron_reminders,'logger'):
        exit_code=run_cron_reminders.run_all_reminders()
        assert exit_code==0
        results.append({'id':'NOT-09','scenario':'runner_nested_delivery_failure','exit_code':exit_code,'limits':'Original runner; batch results replaced; token cleanup on empty in-memory table.'})
    db.session.remove();db.drop_all()
# Original production config on an isolated Flask surface, no real app/DB setup.
surface=Flask('audit_cron_routes');surface.config.from_object(ProductionConfig)
surface.config['CRON_AUTH_TOKEN']='synthetic-unused';surface.register_blueprint(bp)
with patch('backend.routes.cron.CronService.run_3_week_reminders',return_value={'success':True,'processed_events':0}) as runner:
    client=surface.test_client();regular=client.post('/cron/3-week-reminders');test=client.post('/cron/test')
    assert regular.status_code==401 and test.status_code==200 and runner.call_count==1
    results.append({'id':'NOT-07','scenario':'production_class_no_token_request','debug':surface.debug,'ENV':surface.config.get('ENV'),'regular_status':regular.status_code,'test_status':test.status_code,'runner_calls':runner.call_count})
    surface.config['ENV']='production';denied=client.post('/cron/test')
    assert denied.status_code==403
    results.append({'id':'NOT-08','scenario':'explicit_ENV_production','test_status':denied.status_code})
(OUT/'NOTIFICATION_BOUNDARY_CHECKS.json').write_text(json.dumps({'method':'9 isolated probes; SQLite memory, original services/routes/runner, mocked delivery/thread; no real network, no concurrent process test','results':sorted(results,key=lambda r:r['id'])},indent=2),encoding='utf-8')
print('9 notification-boundary probes verified')
