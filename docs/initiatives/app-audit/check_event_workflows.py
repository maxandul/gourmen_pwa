"""Audit reproductions only: synthetic SQLite, original routes, no external I/O."""
from pathlib import Path
import json
import runpy
from datetime import datetime, timedelta

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.models.event import Event, EventType, EventAudience, BillPaidBy
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import MemberClaim, ClaimStatus
from backend.services.ggl_rules import GGLService
from backend.services.accounting import AccountingService
from backend.services.retro_cleanup import RetroCleanupService
from backend.routes.billbro import calculate_weighted_shares

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
assert app.config['TESTING'] and 'events.cleanup' in app.view_functions
results = []


def seed():
    members = [Member(vorname=f'Audit{i}', nachname='Fixture',
                      email=f'audit{i}@example.test', passwort_hash='unused')
               for i in range(3)]
    db.session.add_all(members)
    db.session.flush()
    event = Event(organisator_id=members[0].id,
                  datum=datetime.utcnow()-timedelta(days=7), season=2026,
                  event_typ=EventType.MONATSESSEN, published=True,
                  restaurant='Audit Original', kueche='Audit Cuisine',
                  website='https://example.test')
    db.session.add(event)
    db.session.flush()
    for i, member in enumerate(members):
        db.session.add(Participation(member_id=member.id, event_id=event.id,
                                    teilnahme=True, esstyp=Esstyp.NORMAL,
                                    responded_at=datetime.utcnow(),
                                    guess_bill_amount_rappen=10000+i*100))
    db.session.commit()
    return event, members


def client_for(member):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = str(member.id)
        session['_fresh'] = True
    return client


def post(client, url, data=None):
    try:
        response = client.post(url, data=data or {}, follow_redirects=False)
        return {'status': response.status_code, 'location': response.headers.get('Location')}
    except Exception as exc:
        db.session.rollback()
        return {'exception': type(exc).__name__, 'message': str(exc)[:160]}


def finalized(event):
    event.rechnungsbetrag_rappen = 10000
    event.trinkgeld_rappen = 2000
    event.gesamtbetrag_rappen = 12000
    event.billbro_closed = True
    event.bill_paid_by = BillPaidBy.VEREINSKONTO
    calculate_weighted_shares(event, 12000)
    for p in event.participations:
        p.diff_amount_rappen = abs(p.guess_bill_amount_rappen-10000)
    GGLService.calculate_event_points(event.id)
    AccountingService.create_claims_for_billbro(event)


def inspect(event):
    db.session.expire_all()
    return {'bill': event.rechnungsbetrag_rappen, 'total': event.gesamtbetrag_rappen,
            'closed': event.billbro_closed, 'paid_by': event.bill_paid_by_value,
            'participations': [{'member': p.member_id, 'attends': p.teilnahme,
                               'guess': p.guess_bill_amount_rappen, 'diff': p.diff_amount_rappen,
                               'points': p.points, 'rank': p.rank,
                               'share': p.calculated_share_rappen} for p in event.participations],
            'claims': [{'member': c.member_id, 'expected': c.expected_rappen,
                        'paid': c.paid_rappen, 'creditor': c.creditor_member_id}
                       for c in MemberClaim.query.filter_by(event_id=event.id).all()]}


def run(name, fn):
    with app.app_context():
        db.create_all()
        try:
            event, members = seed()
            results.append({'case': name, 'result': fn(event, members)})
        finally:
            db.session.remove()
            db.drop_all()


def exact_guess(event, members):
    finalized(event)
    return inspect(event)


def mutation(event, members, action, data=None, as_member=False):
    finalized(event)
    response = post(client_for(members[1 if as_member else 0]),
                    action.format(e=event.id, m=members[1].id), data)
    return {'response': response, 'after': inspect(event)}


run('exact_guess_zero_diff', exact_guess)
run('reset_retains_points', lambda e, m: mutation(e, m, '/billbro/{e}/reset_bill'))
run('closed_attendance_changes_claim_stays', lambda e, m: mutation(e, m, '/billbro/{e}/mark_absent/{m}'))
run('member_rsvp_after_final', lambda e, m: mutation(e, m, '/events/{e}/rsvp', as_member=True))
run('cleanup_rsvp_after_final', lambda e, m: mutation(e, m, '/events/{e}/cleanup/rsvp', {'status': 'no'}, True))
run('closed_guess_regular_rejected', lambda e, m: mutation(e, m, '/billbro/{e}/compute',
                                                        {'esstyp': 'NORMAL', 'guess_amount': '103'}, True))
run('closed_guess_organizer_accepted', lambda e, m: mutation(e, m, '/billbro/{e}/record_guess/{m}',
                                                         {'esstyp': 'NORMAL', 'guess_amount': '103'}))


def payment_change(event, members):
    finalized(event)
    claim = MemberClaim.query.filter_by(event_id=event.id, member_id=members[1].id).one()
    claim.paid_rappen = 100
    claim.status = ClaimStatus.TEILWEISE
    db.session.commit()
    response = post(client_for(members[0]), f'/billbro/{event.id}/set_payment',
                    {'paid_by': BillPaidBy.MITGLIED.value, 'payer_member_id': members[0].id})
    return {'response': response, 'after': inspect(event)}


run('payment_change_with_partial_claim', payment_change)
for amount in ['abc', 'NaN', '-10', '0']:
    run('bill_input_'+amount, lambda e, m, a=amount:
        {'response': post(client_for(m[0]), f'/billbro/{e.id}/enter_bill', {'rechnungsbetrag': a}),
         'after': inspect(e)})


def edit_event(event, members):
    response = post(client_for(members[0]), f'/events/{event.id}/edit',
                    {'datum': event.datum.strftime('%Y-%m-%d'),
                     'event_typ': 'MONATSESSEN', 'organisator_id': members[0].id,
                     'audience': 'board', 'restaurant': '', 'kueche': '', 'website': ''})
    db.session.expire_all()
    return {'response': response, 'audience': event.audience_value,
            'restaurant': event.restaurant, 'kueche': event.kueche, 'website': event.website}


run('edit_audience_and_clear_fields', edit_event)


def cleanup_focus(event, members):
    newer = Event(organisator_id=members[0].id, datum=event.datum+timedelta(days=1),
                  season=2026, event_typ=EventType.MONATSESSEN, published=True)
    db.session.add(newer)
    for p in event.participations:
        p.responded_at = None
    db.session.commit()
    response = post(client_for(members[1]), f'/events/{event.id}/cleanup/rsvp', {'status': 'yes'})
    open_ids = [e.id for e in RetroCleanupService.list_open_cleanup_events(members[1].id)]
    return {'target_event': event.id, 'response': response, 'open_ids': open_ids,
            'default_next_event': open_ids[0]}


run('cleanup_nonfirst_yes_loses_focus', cleanup_focus)


def rounding(event, members):
    calculate_weighted_shares(event, 10000)
    return {'total': 10000, 'shares': [p.calculated_share_rappen for p in event.participations],
            'sum': sum(p.calculated_share_rappen for p in event.participations),
            'stored_rule': event.rounding_rule}


run('rounding_three_equal_shares', rounding)


def hidden_event(event, members):
    event.audience = EventAudience.BOARD
    db.session.commit()
    c = client_for(members[1])
    return {'detail': c.get(f'/events/{event.id}').status_code,
            'compute': post(c, f'/billbro/{event.id}/compute', {'esstyp': 'NORMAL', 'guess_amount': '103'})}


run('board_visibility_denies_nonboard', hidden_event)


def undo_later_data(event, members):
    p = Participation.query.filter_by(event_id=event.id, member_id=members[1].id).one()
    db.session.delete(p)
    db.session.commit()
    c = client_for(members[1])
    first = post(c, f'/events/{event.id}/cleanup/rsvp', {'status': 'yes'})
    second = post(c, f'/billbro/{event.id}/compute', {'esstyp': 'NORMAL', 'guess_amount': '104'})
    before = inspect(event)
    undo = post(c, '/events/cleanup/undo-rsvp')
    return {'first': first, 'second': second, 'before_undo': before,
            'undo': undo, 'after': inspect(event)}


run('cleanup_undo_deletes_later_guess', undo_later_data)


def cleanup_queries(event, members):
    from sqlalchemy import event as sa_event
    counts = []
    for extra in [0, 20]:
        for i in range(extra):
            db.session.add(Event(organisator_id=members[0].id,
                                 datum=event.datum-timedelta(days=i+1), season=2026,
                                 event_typ=EventType.MONATSESSEN, published=True))
        db.session.commit()
        db.session.expire_all()
        statements = []
        def count(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith('SELECT'):
                statements.append(statement)
        sa_event.listen(db.engine, 'before_cursor_execute', count)
        try:
            progress = RetroCleanupService.get_progress(members[1].id)
            RetroCleanupService.list_open_cleanup_events(members[1].id)
        finally:
            sa_event.remove(db.engine, 'before_cursor_execute', count)
        counts.append({'events': progress['total'], 'select_queries': len(statements)})
    return counts


run('cleanup_query_scaling', cleanup_queries)
(OUT / 'EVENT_WORKFLOW_CHECKS.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps([{'case': r['case'], 'response': r['result'].get('response')
                  if isinstance(r['result'], dict) else r['result']} for r in results],
                 indent=2, ensure_ascii=True))
