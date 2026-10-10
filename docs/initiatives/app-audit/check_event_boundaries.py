"""Public/statistics/delete/reminder audit; network and actual dispatch blocked."""
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from flask import g
from backend.app import create_app
from backend.extensions import db
from backend.models.event import Event, EventType, EventAudience
from backend.models.member import Member, Role
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.push_subscription import PushSubscription
from backend.services.push_notifications import PushNotificationService as Push
from backend.services.monatsessen_stats import get_monatsessen_statistics

app = create_app('testing')
assert app.config['TESTING'] and app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]


def seed():
    ms=[Member(vorname=f'Audit{i}', nachname='Boundary', email=f'boundary{i}@example.test',
               passwort_hash='unused', vorstandsmitglied=(i==0)) for i in range(3)]
    db.session.add_all(ms)
    db.session.flush()
    e=Event(organisator_id=ms[0].id, datum=datetime.utcnow()-timedelta(days=2),
            season=2026, event_typ=EventType.MONATSESSEN, published=True,
            restaurant='AUDIT_BOARD_RESTAURANT', audience=EventAudience.BOARD)
    db.session.add(e)
    db.session.flush()
    db.session.add(Participation(event_id=e.id, member_id=ms[0].id, teilnahme=True))
    db.session.commit()
    return e,ms


def client(m=None):
    # Explicit outer app context is shared by test requests; clear Flask-Login's
    # cached identity when switching synthetic clients within one scenario.
    g.pop('_login_user',None)
    c=app.test_client()
    if m:
        with c.session_transaction() as s:
            s['_user_id']=str(m.id)
            s['_fresh']=True
    return c


def post(c,path,data=None):
    try:
        r=c.post(path,data=data or {})
        return {'status':r.status_code,'location':r.headers.get('Location')}
    except Exception as exc:
        db.session.rollback()
        return {'exception':type(exc).__name__,'message':str(exc).split('[SQL:')[0][:160]}


def run(name,fn):
    with app.app_context():
        db.create_all()
        try:
            results.append({'case':name,'result':fn(*seed())})
        finally:
            db.session.remove()
            db.drop_all()


def add_rating(e,m):
    db.session.add(EventRating(event_id=e.id,participant_id=m.id,food_rating=5,
                              drinks_rating=4,service_rating=3,highlights='AUDIT_REVIEW_TEXT'))
    db.session.commit()


def public_stats(e,ms):
    add_rating(e,ms[0])
    anon=client()
    member=client(ms[1])
    result={'detail':member.get(f'/events/{e.id}').status_code,
            'archive_has_name':e.restaurant in member.get('/events/?tab=archiv').get_data(as_text=True),
            'public_has_name':e.restaurant in anon.get('/restaurants').get_data(as_text=True),
            'statistics_has_name':e.restaurant in member.get('/events/?tab=stats').get_data(as_text=True)}
    stats=get_monatsessen_statistics(now=datetime.utcnow(),season_year=2026,
                                     organizer_id=None,current_member_id=ms[1].id)
    result['excluded_member_eligible_events']=stats['user_eligible_count']
    return result


run('board_event_public_and_stats_visibility',public_stats)


def disabled_stats(e,ms):
    e.audience=EventAudience.ALL
    e.allow_ratings=False
    db.session.commit()
    add_rating(e,ms[0])
    return {'public_has_name':e.restaurant in client().get('/restaurants').get_data(as_text=True),
            'stats_rating_rows':get_monatsessen_statistics(now=datetime.utcnow(),season_year=2026,
                organizer_id=None,current_member_id=ms[1].id)['charts_json']['restaurantRatings']}


run('disabled_ratings_statistic_policy',disabled_stats)


def reminder_permission(e,ms):
    e.audience=EventAudience.ALL
    e.datum=datetime.utcnow()+timedelta(days=7)
    db.session.commit()
    c=client(ms[1])
    with patch.object(Push,'send_participation_reminder_to_members',return_value={
            'success':True,'sent_count':0,'members_count':0}) as mocked:
        old=post(c,f'/events/{e.id}/send_rsvp_reminder')
        old_calls=mocked.call_count
        new=post(c,f'/events/api/events/{e.id}/send-reminders')
        return {'legacy':old,'legacy_service_calls':old_calls,'api':new,
                'additional_api_calls':mocked.call_count-old_calls}


run('nonorganizer_legacy_reminder_permission',reminder_permission)


def subscription(m):
    db.session.add(PushSubscription(member_id=m.id,endpoint=f'https://example.invalid/{m.id}',
                                   p256dh_key='unused',auth_key='unused'))


def recipients(e,ms):
    e.audience=EventAudience.ALL
    e.datum=datetime.utcnow()+timedelta(days=7)
    db.session.add(Participation(event_id=e.id,member_id=ms[1].id,teilnahme=False,responded_at=None))
    for m in ms:
        subscription(m)
    db.session.commit()
    delivered=[]
    def fake(sub,payload):
        delivered.append(sub.member_id)
        return {'success':True}
    with patch.object(Push,'_send_with_cleanup',side_effect=fake):
        response=Push.send_participation_reminder_to_members(e.id)
    return {'result':response,'would_receive_members':delivered,
            'member_with_unanswered_row':ms[1].id,'member_without_row':ms[2].id}


run('rsvp_reminder_unanswered_row_excluded',recipients)


def rating_reminder(e,ms):
    e.datum=datetime.utcnow()-timedelta(days=1)
    e.allow_ratings=False
    ms[0].is_active=False
    subscription(ms[0])
    subscription(ms[1])
    db.session.add(Participation(event_id=e.id,member_id=ms[1].id,teilnahme=True))
    db.session.commit()
    captures=[]
    def fake(sub,payload):
        captures.append({'member':sub.member_id,'url':payload['data']['url']})
        return {'success':True}
    with patch.object(Push,'_send_with_cleanup',side_effect=fake):
        result=Push.check_and_send_rating_reminders()
    return {'processed_events':result.get('processed_events'),'would_send':captures,
            'target_status':client(ms[1]).get(captures[0]['url']).status_code if captures else None}


run('rating_reminder_disabled_inactive_and_target',rating_reminder)


def deleting(e,ms,with_rating=False):
    ms[0].role=Role.ADMIN
    e.datum=datetime.utcnow()+timedelta(days=1)
    db.session.commit()
    if with_rating:
        add_rating(e,ms[0])
    response=post(client(ms[0]),f'/events/{e.id}/delete')
    return {'response':response,'events_remaining':Event.query.count(),
            'participations_remaining':Participation.query.count(),'ratings_remaining':EventRating.query.count()}


run('delete_without_dependencies',deleting)
run('delete_with_rating_partial_commit',lambda e,ms:deleting(e,ms,True))


def delete_guards(e,ms):
    e.audience=EventAudience.ALL
    db.session.commit()
    denied=post(client(ms[1]),f'/events/{e.id}/delete')
    ms[0].role=Role.ADMIN
    db.session.commit()
    past=post(client(ms[0]),f'/events/{e.id}/delete')
    return {'nonadmin':denied,'past_admin':past,'events':Event.query.count(),
            'participations':Participation.query.count()}


run('delete_role_and_past_guards',delete_guards)


def own_rating(e,ms):
    e.audience=EventAudience.ALL
    db.session.commit()
    add_rating(e,ms[1])
    other=client(ms[2])
    denied=post(other,f'/ratings/event/{e.id}/rating/delete')
    count_after_other=EventRating.query.count()
    c=client(ms[1])
    edited=post(c,f'/ratings/event/{e.id}/rating/edit',
                {'food_rating':'2','drinks_rating':'3','service_rating':'4','highlights':'CHANGED'})
    score=EventRating.query.one().food_rating
    deleted=post(c,f'/ratings/event/{e.id}/rating/delete')
    return {'other_delete':denied,'count_after_other':count_after_other,
            'own_edit_without_participation':edited,'new_score':score,
            'own_delete':deleted,'remaining':EventRating.query.count()}


run('rating_ownership_edit_delete',own_rating)
(OUT/'EVENT_BOUNDARY_CHECKS.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(results,indent=2,ensure_ascii=True))
