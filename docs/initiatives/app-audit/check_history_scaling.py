"""Separate season-history growth from fiscal-year-history growth."""
from pathlib import Path
from datetime import datetime,date
from collections import Counter
import runpy,json,re
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g,template_rendered
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType
from backend.models.participation import Participation
from backend.models.accounting import FiscalYear,Account,AccountKind,Booking,BookingDirection
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
year=datetime.utcnow().year
urls=['/dashboard/',f'/ggl/?tab=tabelle&season={year}',f'/ggl/?tab=performance&season={year}','/accounting/?year=1']
results=[]
for name,seasons,years in [('baseline',1,1),('seasons_6',6,1),('fiscal_years_6',1,6)]:
    with app.app_context():
        db.create_all()
        for i in range(1,6):
            db.session.add(Member(id=i,vorname='Audit',nachname=f'Historie {i}',email=f'history{i}@example.test',
                passwort_hash='unused',role=Role.ADMIN if i==1 else Role.MEMBER,beitritt=date(year-6,1,1)))
        db.session.add(Account(id=1,code='6100',name='Audit Aufwand',kind=AccountKind.EXPENSE))
        db.session.flush()
        for offset in range(seasons):
            for n in range(1,6):
                eid=offset*5+n
                db.session.add(Event(id=eid,organisator_id=1,datum=datetime(year-offset,1,n,19),season=year-offset,
                    event_typ=EventType.MONATSESSEN,published=True,allow_ratings=True,restaurant=f'Audit {eid}'))
                for mid in range(1,6):
                    db.session.add(Participation(event_id=eid,member_id=mid,teilnahme=True,
                        guess_bill_amount_rappen=30000+mid*100,points=10,diff_amount_rappen=mid*100))
        for offset in range(years):
            fyid=offset+1
            db.session.add(FiscalYear(id=fyid,year=year-offset,start_date=date(year-offset,1,1),end_date=date(year-offset,12,31)))
            db.session.flush()
            for n in range(2):
                db.session.add(Booking(fiscal_year_id=fyid,booking_date=date(year-offset,1,n+1),description='Audit Historie',
                    amount_rappen=2000,direction=BookingDirection.OUT,account_id=1,created_by=1))
        db.session.commit();db.session.remove()
        engine=db.engine
        for url in urls:
            for repetition in range(2):
                db.session.remove();g.pop('_login_user',None)
                c=app.test_client()
                with c.session_transaction() as s:s['_user_id']='1';s['_fresh']=True
                statements=Counter();loads=Counter();selection={}
                def sql(conn,cursor,statement,parameters,context,executemany):statements[re.sub(r'\s+',' ',statement).strip()]+=1
                def loaded(session,obj):loads[type(obj).__name__]+=1
                def rendered(sender,template,context,**kwargs):
                    selection['active_tab']=context.get('active_tab')
                    fy=context.get('fiscal_year')
                    selection['fiscal_year']=fy.year if fy else None
                    selection['table_selected_season']=context.get('table_selected_season')
                    ranking=context.get('season_ranking')
                    if ranking is not None:selection['ranking']=[{k:r[k] for k in ['member_id','rank','total_points']} for r in ranking]
                sa_event.listen(engine,'before_cursor_execute',sql);sa_event.listen(Session,'loaded_as_persistent',loaded)
                row=dict(fixture=name,seasons=seasons,fiscal_years=years,url=url,repetition=repetition+1)
                try:
                    with template_rendered.connected_to(rendered,app):r=c.get(url,follow_redirects=False)
                    row.update(http=r.status_code,html_bytes=len(r.data),selection=selection)
                except Exception as e:row.update(error=type(e).__name__,message=str(e)[:180])
                finally:
                    sa_event.remove(engine,'before_cursor_execute',sql);sa_event.remove(Session,'loaded_as_persistent',loaded)
                row.update(sql_count=sum(statements.values()),orm_loads=dict(loads),
                    writes=sum(n for s,n in statements.items() if s.split()[0].upper() in ('UPDATE','INSERT','DELETE')),
                    sql_profiles=[{'count':n,'sql':s} for s,n in statements.most_common()])
                results.append(row)
        db.session.remove();db.drop_all()
out={'method':'3 isolated histories x 4 current-year URLs x 2 fresh sessions, SQLite, original routes/templates, no network.',
     'year':year,'limitations':['Five January events per season, five members, two expense bookings per fiscal year; no receipts/claims/imports.','Adding seasons also adds past events; global cleanup cost remains part of request totals.','All fiscal years open for fixture simplicity; no close/revision scenario.','SQL/ORM counts and HTML bytes are not latency, PostgreSQL scan counts or production load.'], 'results':results}
(OUT/'HISTORY_SCALING_CHECKS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for r in results:
    if r['repetition']==1:print(json.dumps({k:v for k,v in r.items() if k!='sql_profiles'}))
