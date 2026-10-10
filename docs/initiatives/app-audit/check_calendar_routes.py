"""Actual event POSTs, synthetic SQLite only; no external calendar client."""
import json
import runpy
from datetime import datetime, date, timezone
from pathlib import Path
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT/'serve_ui_fixture.py'))
from backend.services.calendar_feed import CalendarFeedService as Service
from backend.models.event import EventAudience
from icalendar import Calendar
app,db,Event,Member = (ns[k] for k in ('app','db','Event','Member'))
results=[]
def client(uid):
    c=app.test_client()
    with c.session_transaction() as s:
        s['_user_id']=str(uid)
        s['_fresh']=True
    return c
def contains(event_id):
    with patch.object(Service,'_today_zurich',return_value=date(2026,9,20)):
        feed=Calendar.from_ical(Service.generate_feed_for_member(db.session.get(Member,2)))
    return any(str(e['UID'])==f'event-{event_id}@gourmen.ch' for e in feed.walk('VEVENT'))

with app.app_context():
    cases=[('unchanged',{},1,0),('date',{'datum':'2026-10-02'},1,1),
           ('notes',{'notizen':'Andere Audit-Notiz'},1,0),
           ('multiple',{'datum':'2026-10-03','restaurant':'Neuer Audit-Ort','notizen':'Andere Audit-Notiz'},1,1),
           ('audience',{'audience':'board'},1,0),
           ('board_type',{'event_typ':'VORSTANDSSITZUNG','audience':'board'},1,1),
           ('unauthorized',{'restaurant':'Unerlaubter Audit-Ort'},2,0)]
    for index,(name,changes,uid,expected_sequence) in enumerate(cases,13):
        event=Event(id=100+index,organisator_id=1,datum=datetime(2026,10,1),
                    season=2026,event_typ=ns['EventType'].MONATSESSEN,
                    audience=EventAudience.ALL,published=True,restaurant='Audit-Ort',
                    notizen='Audit-Notiz')
        db.session.add(event);db.session.commit()
        event_id=event.id
        stamp=datetime(2026,9,20,12,tzinfo=timezone.utc)
        before=Service._build_vevent(event,stamp)
        payload={'datum':'2026-10-01','event_typ':'MONATSESSEN','audience':'all',
                 'organisator_id':'1','restaurant':'Audit-Ort','notizen':'Audit-Notiz'}
        payload.update(changes)
        # Fresh app context prevents Flask-Login's g cache crossing test users.
        with app.app_context():
            response=client(uid).post(f'/events/{event_id}/edit',data=payload)
        db.session.expire_all();event=db.session.get(Event,event_id)
        after=Service._build_vevent(event,stamp)
        record={'id':f'CAL-{index:02}','case':name,'status':response.status_code,
                'sequence':event.ical_sequence or 0,'uid_stable':before['UID']==after['UID'],
                'audience':event.audience.value,'description_changed':before['DESCRIPTION']!=after['DESCRIPTION'],
                'date':event.datum.date().isoformat(),'restaurant':event.restaurant,
                'in_regular_feed':contains(event_id)}
        assert response.status_code==302 and record['sequence']==expected_sequence and record['uid_stable'], record
        if name=='date': assert record['date']=='2026-10-02'
        if name=='notes': assert record['description_changed']
        if name=='multiple': assert record['date']=='2026-10-03' and event.restaurant=='Neuer Audit-Ort'
        if name=='audience': assert record['audience']=='all'
        if name=='board_type': assert record['audience']=='board' and not record['in_regular_feed']
        if name=='unauthorized': assert event.restaurant=='Audit-Ort'
        results.append(record)
    # Delete only the newly seeded, unrelated synthetic last event.
    before_present=contains(event_id)
    with app.app_context():
        response=client(1).post(f'/events/{event_id}/delete')
    db.session.expire_all()
    after_present=contains(event_id)
    assert before_present and not after_present and db.session.get(Event,event_id) is None and response.status_code==302
    results.append({'id':'CAL-20','case':'admin delete isolated synthetic event',
                    'status':302,'feed_before':before_present,'feed_after':after_present})

(OUT/'CALENDAR_ROUTE_CHECKS.json').write_text(json.dumps({
    'scope':'Original POST routes and service; isolated synthetic SQLite. CSRF/rate-limit disabled; no real calendar client or external operations.',
    'results':results},indent=2)+'\n',encoding='utf-8')
print('Eight original-route calendar probes passed.')
