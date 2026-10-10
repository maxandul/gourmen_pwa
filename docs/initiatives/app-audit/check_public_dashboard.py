"""Public/dashboard source behavior with synthetic events and captured template contexts."""
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
import runpy,json
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g,template_rendered
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType,EventAudience
from backend.models.participation import Participation
from backend.services.monatsessen_stats import get_landing_extras,get_landing_restaurant_table
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]
def client(m=None):
    g.pop('_login_user',None)
    c=app.test_client()
    if m:
        with c.session_transaction() as s:s['_user_id']=str(m.id);s['_fresh']=True
    return c
def capture(c,url):
    contexts=[]
    def receiver(sender,template,context,**kw):contexts.append(context)
    with template_rendered.connected_to(receiver,app):r=c.get(url)
    return r,contexts[-1] if contexts else {}
def event(ms,label,when=None,**kw):
    e=Event(organisator_id=ms[0].id,datum=when or datetime.now()-timedelta(days=5),season=datetime.now().year,
            event_typ=EventType.MONATSESSEN,restaurant=label,published=True,**kw)
    db.session.add(e);db.session.commit();return e
def run(name,fn):
    with app.app_context():
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'public{i}@example.com',passwort_hash='unused') for i in range(2)]
        ms[0].role=Role.ADMIN;db.session.add_all(ms);db.session.commit()
        try:results.append({'case':name,'result':fn(ms)})
        finally:db.session.remove();db.drop_all()

def hidden_next(ms):
    e=event(ms,'AUDIT_BOARD_NEXT',datetime.now()+timedelta(days=2),audience=EventAudience.BOARD)
    public,pc=capture(client(),'/')
    dash,dc=capture(client(ms[1]),'/dashboard/')
    return {'public_http':public.status_code,'public_restaurant':pc.get('next_essen_restaurant'),
            'dashboard_http':dash.status_code,'dashboard_next':dc['next_event'].id if dc.get('next_event') else None,
            'event_visible':e.is_visible_to(ms[1])}
run('public_next_event_audience',hidden_next)

def bill(ms):
    e=event(ms,'AUDIT_BOARD_BILL',audience=EventAudience.BOARD)
    db.session.add(Participation(member_id=ms[1].id,event_id=e.id,teilnahme=True,calculated_share_rappen=2500));db.session.commit()
    c=client(ms[1]);r,ctx=capture(c,'/dashboard/')
    return {'http':r.status_code,'bill_selected':ctx['latest_bill_event'].id==e.id,
            'bill_link_rendered':f'/events/{e.id}?tab=billbro' in r.get_data(as_text=True),
            'target_http':c.get(f'/events/{e.id}').status_code,'event_visible':e.is_visible_to(ms[1])}
run('dashboard_bill_link_after_audience_change',bill)

def same_day(ms):
    now=datetime.now().replace(hour=12,minute=0,second=0,microsecond=0)
    e=event(ms,'AUDIT_TODAY',now.replace(hour=0))
    next_info=get_landing_extras(now)
    rows,*_=get_landing_restaurant_table(now)
    return {'next_restaurant_at_noon':next_info['next_essen_restaurant'],
            'in_visited_table_at_noon':any(r['restaurant']=='AUDIT_TODAY' for r in rows)}
run('today_event_public_date_boundary',same_day)

def fallback(ms):
    with patch('backend.routes.public.get_landing_restaurant_table',side_effect=RuntimeError('synthetic dependency failure')):
        r,ctx=capture(client(),'/restaurants?q=Audit&sort=name&page=2')
    return {'http':r.status_code,'total':ctx['table_total'],'query':ctx['table_query'],'sort':ctx['hitlist_sort'],
            'flashes':len(ctx.get('get_flashed_messages',lambda:[])())}
run('public_query_failure_becomes_empty_result',fallback)

def paging(ms):
    for i in range(12):event(ms,f'Audit {i:02d}')
    rows,total,pages,page,base=get_landing_restaurant_table(datetime.now(),page=999,per_page=10,sort='name')
    searched=get_landing_restaurant_table(datetime.now(),query='Audit 03')
    r,ctx=capture(client(),'/restaurants?page=invalid&sort=invalid')
    return {'clamped_page':page,'pages':pages,'total':total,'rows':len(rows),'baseline':base,
            'search_total':searched[1],'search_baseline':searched[4],
            'invalid_input_http':r.status_code,'invalid_input_page':ctx['table_page'],'invalid_input_sort':ctx['hitlist_sort']}
run('search_pagination_and_invalid_parameters',paging)

def identities(ms):
    event(ms,'Audit Bistro',place_id='synthetic-place-A',place_locality='City A')
    event(ms,'Audit Bistro',place_id='synthetic-place-B',place_locality='City B')
    rows,total,*_=get_landing_restaurant_table(datetime.now())
    return {'distinct_place_ids':2,'restaurant_rows':total,'cities':[r['ort'] for r in rows]}
run('same_name_different_restaurants_merged',identities)

def entry(ms):
    anonymous=client().get('/dashboard/')
    signed=client(ms[1]);redirect=signed.get('/');show=signed.get('/?show=1')
    return {'anonymous_dashboard':anonymous.status_code,'signed_landing_location':redirect.headers.get('Location'),'explicit_public_http':show.status_code}
run('public_private_entry_guards',entry)
(OUT/'PUBLIC_DASHBOARD_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
