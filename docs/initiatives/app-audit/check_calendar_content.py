"""Synthetic calendar content boundaries; no real subscription or network."""
import json
import runpy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT / 'serve_ui_fixture.py'))
from icalendar import Calendar
from backend.services.calendar_feed import CalendarFeedService as Service
from backend.models.event import EventAudience, EventType

app, db, Member, Event = (ns[k] for k in ('app', 'db', 'Member', 'Event'))
results = []
with app.app_context():
    today = date(2026, 9, 20)
    stamp = datetime(2026, 9, 20, 12, tzinfo=timezone.utc)
    event = db.session.get(Event, 3)
    member = db.session.get(Member, 2)
    board = db.session.get(Member, 1)
    event.datum = datetime(2026, 9, 20, 1)
    event.audience = EventAudience.ALL
    db.session.commit()
    def has_event(who):
        with patch.object(Service, '_today_zurich', return_value=today):
            entries = Calendar.from_ical(Service.generate_feed_for_member(who)).walk('VEVENT')
        return any(str(e['UID']) == 'event-3@gourmen.ch' for e in entries)
    visible_today = has_event(member)
    event.datum = datetime(2026, 9, 19, 23)
    db.session.commit()
    visible_yesterday = has_event(member)
    assert visible_today and not visible_yesterday
    results.append({'id':'CAL-06','case':'local date boundary',
                    'today_01_included':visible_today,'yesterday_23_included':visible_yesterday})

    event.datum = datetime(2026, 9, 21, 19)
    event.audience = EventAudience.BOARD
    # Organizer privilege does not widen the personal member calendar.
    event.organisator_id = member.id
    db.session.commit()
    regular, board_visible = has_event(member), has_event(board)
    original_role = member.role
    member.role = ns['Role'].ADMIN
    db.session.commit()
    nonboard_admin = has_event(member)
    member.role = original_role
    assert not regular and board_visible and not nonboard_admin
    results.append({'id':'CAL-07','case':'board audience',
                    'regular_organizer':regular,'board_member':board_visible,
                    'nonboard_admin':nonboard_admin})

    event.audience = EventAudience.ALL
    event.published = False
    db.session.commit()
    assert not has_event(member)
    results.append({'id':'CAL-08','case':'unpublish','included':False})
    event.published = True
    event.organisator_id = 1
    db.session.commit()

    # Each independent change uses the actual snapshot/bump/serialization functions.
    matrix = []
    changes = {'datum':datetime(2026,9,22,19),'event_typ':EventType.AUSFLUG,
               'restaurant':'Anderer Audit-Ort','place_name':'Audit-Place',
               'place_address':'Audit-Strasse 42','organisator_id':2,
               'notizen':'Geaenderte Audit-Notiz'}
    for field, value in changes.items():
        db.session.expire_all()
        e = db.session.get(Event,3)
        old = Service._build_vevent(e,stamp)
        before = Service.calendar_relevant_state(e)
        oldseq = e.ical_sequence or 0
        setattr(e,field,value)
        db.session.flush()
        if field == 'organisator_id':
            db.session.expire(e,['organisator'])
        Service.bump_sequence_if_changed(e,before,Service.calendar_relevant_state(e))
        new = Service._build_vevent(e,stamp)
        row = {'field':field,'uid_stable':old['UID']==new['UID'],
               'sequence_delta':(e.ical_sequence or 0)-oldseq,
               'changed_properties':sorted(str(k) for k in set(old.keys())|set(new.keys())
                                           if old.get(k)!=new.get(k))}
        matrix.append(row)
        assert row['uid_stable'] and row['sequence_delta'] == (0 if field=='notizen' else 1)
        db.session.rollback()
    results.append({'id':'CAL-09','case':'seven-field matrix','rows':matrix})

    e = db.session.get(Event,3)
    before = Service._build_vevent(e,stamp)
    oldseq = e.ical_sequence or 0
    e.organisator.rufname = 'Audit-Neuer-Rufname'
    db.session.flush()
    after = Service._build_vevent(e,stamp)
    organizer_changed = before['ORGANIZER'].params['CN'] != after['ORGANIZER'].params['CN']
    assert organizer_changed and before['DESCRIPTION'] != after['DESCRIPTION'] and (e.ical_sequence or 0)==oldseq
    results.append({'id':'CAL-10','case':'organizer profile rename',
                    'organizer_cn_changed':organizer_changed,'description_changed':True,
                    'sequence_delta':0,'last_modified_changed':before['LAST-MODIFIED']!=after['LAST-MODIFIED']})
    db.session.rollback()

    offsets = []
    for day in (date(2026,3,28),date(2026,3,29),date(2026,10,24),date(2026,10,25)):
        e = db.session.get(Event,3)
        e.datum = datetime.combine(day,datetime.min.time())
        cal = Service._build_calendar_shell()
        cal.add_component(Service._build_vevent(e,stamp))
        parsed = Calendar.from_ical(cal.to_ical()).walk('VEVENT')[0]
        start,end = parsed.decoded('DTSTART'),parsed.decoded('DTEND')
        offsets.append({'date':day.isoformat(),'start_hour':start.hour,'end_hour':end.hour,
                        'utc_offset_hours':start.utcoffset().total_seconds()/3600})
    assert [r['utc_offset_hours'] for r in offsets]==[1,2,2,1]
    assert all(r['start_hour']==18 and r['end_hour']==23 for r in offsets)
    results.append({'id':'CAL-11','case':'serialized DST boundary roundtrip','rows':offsets})
    db.session.rollback()

    member = db.session.get(Member,2)
    member.ical_token = 'synthetic-content-probe-only'
    member.is_active = False
    db.session.commit()
    client=app.test_client()
    inactive=client.get('/calendar/'+member.ical_token+'.ics')
    unknown=client.get('/calendar/synthetic-unknown.ics')
    assert inactive.status_code==unknown.status_code==404 and not inactive.data and not unknown.data
    results.append({'id':'CAL-12','case':'inactive or unknown token','statuses':[404,404],'empty_bodies':True})

(OUT/'CALENDAR_CONTENT_CHECKS.json').write_text(json.dumps({
    'scope':'Original local service/route; in-memory synthetic data; fixed local day for inclusion and timestamp for serialization. No real client sync, rate limit or CSRF test.',
    'results':results},indent=2)+'\n',encoding='utf-8')
print('Seven calendar content groups passed; no tokens or feed bodies emitted.')
