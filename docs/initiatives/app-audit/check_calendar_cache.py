"""Isolated calendar contract probes; synthetic token never emitted."""
import json
import runpy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
# Bootstrap runtime before importing application dependencies.
ns = runpy.run_path(str(OUT / 'serve_ui_fixture.py'))
from icalendar import Calendar
from backend.services.calendar_feed import CalendarFeedService as Service
from backend.models.event import EventAudience

app, db, Member, Event = (ns[k] for k in ('app', 'db', 'Member', 'Event'))
results = []
with app.app_context():
    member = db.session.get(Member, 2)
    member.ical_token = 'synthetic-calendar-cache-probe-only'
    db.session.commit()
    endpoint = '/calendar/' + member.ical_token + '.ics'
    client = app.test_client()
    original = Service._build_vevent
    def fetch(stamp, etag=None):
        # Freeze only the timestamp passed by the generator into VEVENT.
        with patch.object(Service, '_build_vevent', side_effect=lambda event, now: original(event, stamp)):
            return client.get(endpoint, headers={'If-None-Match': etag} if etag else {})
    t1 = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 20, 12, 5, tzinfo=timezone.utc)
    first = fetch(t1)
    same = fetch(t1, first.headers['ETag'])
    later = fetch(t2, first.headers['ETag'])
    first_events = Calendar.from_ical(first.data).walk('VEVENT')
    later_events = Calendar.from_ical(later.data).walk('VEVENT')
    changed = sorted({str(key) for a,b in zip(first_events,later_events)
                      for key in set(a.keys()) | set(b.keys()) if a.get(key) != b.get(key)})
    results.append({'id':'CAL-01','case':'same timestamp, unchanged data',
                    'initial_status':first.status_code,'conditional_status':same.status_code})
    results.append({'id':'CAL-02','case':'five minutes later, unchanged data',
                    'conditional_status':later.status_code,'etag_changed':first.headers['ETag'] != later.headers['ETag'],
                    'changed_event_properties':changed,'event_count':len(first_events)})
    event = db.session.get(Event, 3)
    before = Service.calendar_relevant_state(event)
    seq = event.ical_sequence or 0
    a = original(event,t1)
    event.notizen = 'Andere synthetische Notiz'
    Service.bump_sequence_if_changed(event,before,Service.calendar_relevant_state(event))
    b = original(event,t1)
    results.append({'id':'CAL-03','case':'notes changed',
                    'description_changed':a['DESCRIPTION'] != b['DESCRIPTION'],
                    'sequence_before':seq,'sequence_after':event.ical_sequence or 0})
    before = Service.calendar_relevant_state(event)
    event.restaurant = 'Neuer synthetischer Ort'
    Service.bump_sequence_if_changed(event,before,Service.calendar_relevant_state(event))
    results.append({'id':'CAL-04','case':'restaurant changed positive control',
                    'sequence_after':event.ical_sequence or 0})
    before = Service.calendar_relevant_state(event)
    audience_values = list(EventAudience)
    event.audience = next(v for v in audience_values if v != event.audience)
    oldseq = event.ical_sequence or 0
    Service.bump_sequence_if_changed(event,before,Service.calendar_relevant_state(event))
    results.append({'id':'CAL-05','case':'audience changed',
                    'declared_relevant':'audience' in Service.RELEVANT_FIELDS,
                    'snapshot_contains_audience':'audience' in before,
                    'sequence_before':oldseq,'sequence_after':event.ical_sequence or 0})
    db.session.rollback()

assert results[0]['conditional_status'] == 304
assert results[1]['conditional_status'] == 200 and results[1]['changed_event_properties'] == ['DTSTAMP']
assert results[2]['description_changed'] and results[2]['sequence_before'] == results[2]['sequence_after']
assert results[3]['sequence_after'] == results[2]['sequence_after'] + 1
assert results[4]['sequence_before'] == results[4]['sequence_after']
(OUT/'CALENDAR_CACHE_CHECKS.json').write_text(json.dumps({
    'scope':'Original local route/service; frozen VEVENT timestamp argument; synthetic in-memory DB; no external calendar client. CSRF and rate limit disabled in testing.',
    'results':results},indent=2)+'\n',encoding='utf-8')
print('Five isolated calendar checks recorded; no token or feed body emitted.')
