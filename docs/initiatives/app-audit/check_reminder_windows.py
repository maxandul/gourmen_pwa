"""Frozen clock and fake delivery; original selection and push argument paths."""
from pathlib import Path
import runpy,json,inspect
from datetime import datetime,timedelta
from unittest.mock import patch,Mock
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType
from backend.services.push_notifications import PushNotificationService as Push
import pywebpush
class Clock(datetime):
    now_value=datetime(2026,9,21,8)
    @classmethod
    def utcnow(cls):return cls.now_value
app=create_app('testing');results=[]
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1,vorname='Audit',nachname='Clock',email='clock@example.test',passwort_hash='unused',role=Role.ADMIN))
    db.session.flush()
    event=Event(id=1,organisator_id=1,datum=datetime(2026,10,12,8),season=2026,event_typ=EventType.MONATSESSEN,published=True,restaurant='Audit')
    db.session.add(event);db.session.commit()
    with patch('backend.services.push_notifications.datetime',Clock),patch.object(Push,'send_event_reminder_to_organizer',return_value=True),patch.object(Push,'send_participation_reminder_to_members',return_value={'success':True}):
        selected=[]
        for stamp in [datetime(2026,9,21,8),datetime(2026,9,22,8)]:
            Clock.now_value=stamp;selected.append(Push.check_and_send_3_week_reminders()['processed_events'])
        assert selected==[1,0]
        results.append({'id':'TIME-01','scenario':'3_week_due_then_next_day','processed':selected})
    event.datum=datetime(2026,9,25,19);db.session.commit()
    with patch('backend.services.push_notifications.datetime',Clock),patch.object(Push,'send_event_week_reminder_to_participants',return_value={'success':True}):
        selected=[]
        for stamp in [datetime(2026,9,21,8),datetime(2026,9,22,8)]:
            Clock.now_value=stamp;selected.append(Push.check_and_send_weekly_reminders()['processed_events'])
        assert selected==[1,0]
        results.append({'id':'TIME-02','scenario':'weekly_monday_then_tuesday','processed':selected})
    event.datum=datetime(2026,9,20,19);db.session.commit()
    with patch('backend.services.push_notifications.datetime',Clock),patch.object(Push,'send_rating_reminder_to_participants',return_value={'success':True}):
        selected=[]
        for stamp in [datetime(2026,9,21,8),datetime(2026,9,22,8)]:
            Clock.now_value=stamp;selected.append(Push.check_and_send_rating_reminders()['processed_events'])
        assert selected==[1,0]
        results.append({'id':'TIME-03','scenario':'rating_next_day_then_day_after','processed':selected})
    with patch('backend.services.push_notifications.WEBPUSH_AVAILABLE',True),patch('backend.services.push_notifications.VAPIDService.get_vapid_private_key',return_value='synthetic-not-a-key'),patch('backend.services.push_notifications.VAPIDService.get_vapid_public_key',return_value='unused'),patch('backend.services.push_notifications.Vapid02.from_file',return_value=Mock()),patch('backend.services.push_notifications.webpush') as transport:
        result=Push.send_push_notification({'endpoint':'https://push.example.test/audit','keys':{}},{},True)
        assert result['success'] and 'timeout' not in transport.call_args.kwargs
        results.append({'id':'TIME-04','scenario':'current_push_transport_arguments','timeout_supplied':False,'installed_webpush_default_timeout':inspect.signature(pywebpush.webpush).parameters['timeout'].default})
    with patch('pywebpush.WebPusher') as pusher:
        pusher.return_value.send.return_value.status_code=201
        pywebpush.webpush({'endpoint':'https://push.example.test/audit','keys':{}},data='audit')
        value=pusher.return_value.send.call_args.kwargs['timeout']
        assert value is None
        results.append({'id':'TIME-05','scenario':'installed_webpush_forwards_default','timeout_to_send':value})
    db.session.remove();db.drop_all()
(OUT/'REMINDER_WINDOW_CHECKS.json').write_text(json.dumps({'method':'5 isolated frozen-clock/transport probes, SQLite memory; original date filters and installed pywebpush; no real scheduler/network or timing measurement','results':results},indent=2),encoding='utf-8')
print('5 reminder-window/transport probes verified')
