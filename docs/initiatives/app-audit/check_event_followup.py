"""Second bounded workflow pass, synthetic data and original application only."""
from pathlib import Path
from datetime import datetime, timedelta
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from backend.models.event import Event, EventType
from backend.models.member import Member, Role
from backend.models.participation import Participation, Esstyp
from backend.models.rating import EventRating
from backend.services.ggl_rules import GGLService
from backend.routes.events import get_second_friday_of_month

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
assert app.config['TESTING'] and 'ratings.rate_event' in app.view_functions
results = []


def seed():
    ms = [Member(vorname=f'Audit{i}', nachname='Followup',
                 email=f'followup{i}@example.test', passwort_hash='unused') for i in range(3)]
    db.session.add_all(ms)
    db.session.flush()
    e = Event(organisator_id=ms[0].id, datum=datetime(2026, 5, 8, 23, 59, 59),
              season=2026, event_typ=EventType.MONATSESSEN, published=True)
    db.session.add(e)
    db.session.flush()
    for m in ms:
        db.session.add(Participation(member_id=m.id, event_id=e.id, teilnahme=True,
                                    esstyp=Esstyp.NORMAL, responded_at=datetime.utcnow()))
    db.session.commit()
    return e, ms


def client(m):
    c = app.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(m.id)
        s['_fresh'] = True
    return c


def request(c, path, data=None):
    try:
        r = c.post(path, data=data) if data is not None else c.get(path)
        return {'status': r.status_code, 'location': r.headers.get('Location')}
    except Exception as exc:
        db.session.rollback()
        return {'exception': type(exc).__name__, 'message': str(exc)[:130]}


def run(name, fn):
    with app.app_context():
        db.create_all()
        try:
            results.append({'case': name, 'result': fn(*seed())})
        finally:
            db.session.remove()
            db.drop_all()


def rating_data(**overrides):
    return dict(food_rating='5', drinks_rating='4', service_rating='3',
                highlights='AUDIT_HIGHLIGHT_UNIQUE') | overrides


def rating_redirect(e, ms):
    e.allow_ratings = False
    db.session.commit()
    return request(client(ms[1]), f'/ratings/event/{e.id}/rate?next=https://example.invalid/audit')


def invalid_rating(e, ms):
    c = client(ms[1])
    response = request(c, f'/ratings/event/{e.id}/rate', rating_data(food_rating='9'))
    body = c.get(response['location']).get_data(as_text=True)
    return {'response': response, 'rating_count': EventRating.query.count(),
            'entered_highlight_in_response': 'AUDIT_HIGHLIGHT_UNIQUE' in body,
            'range_error_visible': 'Bewertung muss zwischen 1 und 5 liegen' in body}


def future_rating(e, ms):
    e.datum = datetime.utcnow()+timedelta(days=30)
    db.session.commit()
    response = request(client(ms[1]), f'/ratings/event/{e.id}/rate', rating_data())
    return {'response': response, 'rating_count': EventRating.query.count()}


def rating_access(e, ms):
    db.session.add(EventRating(event_id=e.id, participant_id=ms[0].id,
                              food_rating=5, drinks_rating=4, service_rating=3,
                              highlights='AUDIT_HIGHLIGHT_UNIQUE'))
    Participation.query.filter_by(event_id=e.id, member_id=ms[1].id).one().teilnahme = False
    db.session.commit()
    c = client(ms[1])
    body = c.get(f'/events/{e.id}?tab=ratings').get_data(as_text=True)
    return {'api': request(c, f'/ratings/event/{e.id}/ratings/api'),
            'detail_displays_highlight': 'AUDIT_HIGHLIGHT_UNIQUE' in body,
            'new_rating': request(c, f'/ratings/event/{e.id}/rate', rating_data()),
            'rating_count': EventRating.query.count()}


run('rating_next_external_redirect', rating_redirect)
run('rating_invalid_loses_input', invalid_rating)
run('rating_future_event', future_rating)
run('rating_nonparticipant_access_difference', rating_access)


def organizer_change(e, ms):
    p = Participation.query.filter_by(event_id=e.id, member_id=ms[0].id).one()
    p.guess_bill_amount_rappen = 10000
    p.calculated_share_rappen = 4000
    Participation.query.filter_by(event_id=e.id, member_id=ms[1].id).one().teilnahme = False
    db.session.commit()
    response = request(client(ms[0]), f'/events/{e.id}/edit',
                       {'datum': '2026-05-08', 'event_typ': 'MONATSESSEN',
                        'audience': 'all', 'organisator_id': ms[1].id})
    db.session.expire_all()
    return {'response': response, 'new_organizer': e.organisator_id,
            'old_organizer_row_exists': Participation.query.filter_by(event_id=e.id, member_id=ms[0].id).count(),
            'new_organizer_attends': Participation.query.filter_by(event_id=e.id, member_id=ms[1].id).one().teilnahme,
            'stored_datetime': e.datum.isoformat()}


run('organizer_change_deletes_data_and_leaves_absence', organizer_change)


def admin_create(e, ms, bad_places=False):
    ms[0].role = Role.ADMIN
    db.session.commit()
    data = {'datum': '2026-06-12', 'event_typ': 'VORSTANDSSITZUNG',
            'audience': 'all', 'organisator_id': ms[1].id}
    if bad_places:
        data.update(place_id='audit', place_lat='not-a-number')
    response = request(client(ms[0]), '/admin/events/new', data)
    created = Event.query.filter(Event.id != e.id).first()
    return {'response': response, 'created': {'audience': created.audience_value,
            'date': created.datum.isoformat(), 'organizer_participations': len(created.participations)}
            if created else None}


run('create_board_audience_enforced', admin_create)
run('create_invalid_places_number', lambda e, ms: admin_create(e, ms, True))


def planning(e, ms):
    ms[0].role = Role.ADMIN
    d = get_second_friday_of_month(2027, 1)
    e.datum = datetime(d.year, d.month, d.day, 23, 59, 59)
    e.season = 2027
    db.session.commit()
    c = client(ms[0])
    response = request(c, '/events/year-planning', {'year': '2027'})
    first_count = Event.query.count()
    response2 = request(c, '/events/year-planning', {'year': '2027'})
    return {'response': response, 'after_first': first_count,
            'repeat': response2, 'after_repeat': Event.query.count(),
            'january_dates': [x.datum.isoformat() for x in Event.query.order_by(Event.datum).all() if x.datum.month==1],
            'planned_participation_count': Participation.query.filter(Participation.event_id!=e.id).count()}


run('year_planning_duplicate_and_repeat', planning)


def ranked(e):
    e.rechnungsbetrag_rappen = 10000
    for p, guess in zip(e.participations, [9900, 10100, 10300]):
        p.guess_bill_amount_rappen = guess
        p.diff_amount_rappen = abs(guess-10000)
    GGLService.calculate_event_points(e.id)
    db.session.expire_all()


def ties(e, ms):
    ranked(e)
    table = GGLService.get_season_ranking(2026)
    return [{'member': m.id, 'db_points': Participation.query.filter_by(member_id=m.id, event_id=e.id).one().points,
             'table_rank': next(x['rank'] for x in table if x['member_id']==m.id),
             'table_points': next(x['total_points'] for x in table if x['member_id']==m.id),
             'performance_rank': GGLService.get_member_performance_view_context(m.id,2026)['rank'],
             'performance_points': GGLService.get_member_performance_view_context(m.id,2026)['user_points']}
            for m in ms]


run('ggl_fractional_and_tie_view_disagreement', ties)


def change_type(e, ms):
    ranked(e)
    response = request(client(ms[0]), f'/events/{e.id}/edit',
                       {'datum': '2026-05-08', 'event_typ': 'AUSFLUG',
                        'audience': 'all', 'organisator_id': ms[0].id})
    db.session.expire_all()
    return {'response': response, 'supports_ggl': e.supports_ggl,
            'season_points': [r['total_points'] for r in GGLService.get_season_ranking(2026)],
            'race_events': [x.id for x in GGLService.get_season_progression_data(2026)['events']]}


run('event_type_change_retains_ggl_scores', change_type)


def inactive(e, ms):
    ranked(e)
    ms[1].is_active = False
    db.session.commit()
    return {'table_members': [r['member_id'] for r in GGLService.get_season_ranking(2026)],
            'race_members': [r['id'] for r in GGLService.get_season_progression_data(2026)['members']]}


run('ggl_inactive_member_views', inactive)


def admin_actions(e, ms):
    ms[1].role = Role.ADMIN
    db.session.commit()
    c = client(ms[1])
    body = c.get(f'/events/{e.id}?tab=billbro').get_data(as_text=True)
    response = request(c, f'/billbro/{e.id}/enter_bill', {'rechnungsbetrag': '100'})
    db.session.expire_all()
    return {'organizer_action_in_html': f'/billbro/{e.id}/set_payment' in body,
            'enter_bill': response, 'stored_bill': e.rechnungsbetrag_rappen}


run('admin_ui_actions_denied_by_routes', admin_actions)


def repeated_rating(e, ms):
    c = client(ms[1])
    first = request(c, f'/ratings/event/{e.id}/rate', rating_data())
    second = request(c, f'/ratings/event/{e.id}/rate', rating_data(food_rating='1'))
    row = EventRating.query.one()
    return {'first': first, 'second': second, 'count': EventRating.query.count(),
            'food_rating': row.food_rating}


run('rating_repeated_post_no_duplicate', repeated_rating)


def rating_undo_invalidated(e, ms):
    c = client(ms[1])
    request(c, f'/events/{e.id}/cleanup/rsvp', {'status': 'yes'})
    response = request(c, f'/ratings/event/{e.id}/rate', rating_data())
    from backend.routes.events import CLEANUP_RSVP_UNDO_SESSION_KEY
    with c.session_transaction() as s:
        undo_exists = CLEANUP_RSVP_UNDO_SESSION_KEY in s
    return {'rating': response, 'rating_count': EventRating.query.count(), 'undo_exists': undo_exists}


run('rating_clears_matching_cleanup_undo', rating_undo_invalidated)


def edit_today(e, ms):
    now = datetime.utcnow()
    e.datum = now.replace(hour=23, minute=59, second=59, microsecond=0)
    db.session.commit()
    before = e.is_past
    response = request(client(ms[0]), f'/events/{e.id}/edit',
                       {'datum': now.strftime('%Y-%m-%d'), 'event_typ': 'MONATSESSEN',
                        'audience': 'all', 'organisator_id': ms[0].id})
    db.session.expire_all()
    return {'response': response, 'before_is_past': before, 'after_is_past': e.is_past,
            'after_datetime': e.datum.isoformat(), 'still_is_today': e.is_today}


run('edit_today_switches_past_classification', edit_today)


def planning_access(e, ms):
    c = client(ms[1])
    unauthorized = request(c, '/events/year-planning', {'year': '2027'})
    unauthorized_count = Event.query.count()
    ms[1].role = Role.ADMIN
    db.session.commit()
    invalid = request(client(ms[1]), '/events/year-planning', {'year': '9999'})
    return {'nonadmin': unauthorized, 'count_after_nonadmin': unauthorized_count,
            'invalid_year': invalid, 'count_after_invalid': Event.query.count()}


run('planning_rejects_nonadmin_and_invalid_year', planning_access)


def change_season(e, ms):
    ranked(e)
    response = request(client(ms[0]), f'/events/{e.id}/edit',
                       {'datum': '2025-05-08', 'event_typ': 'MONATSESSEN',
                        'audience': 'all', 'organisator_id': ms[0].id})
    db.session.expire_all()
    return {'response': response, 'stored_season': e.season,
            'old_season_points': [r['total_points'] for r in GGLService.get_season_ranking(2026)],
            'new_season_points': [r['total_points'] for r in GGLService.get_season_ranking(2025)]}


run('event_date_updates_ggl_season', change_season)
(OUT / 'EVENT_FOLLOWUP_CHECKS.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(results,indent=2,ensure_ascii=True))
