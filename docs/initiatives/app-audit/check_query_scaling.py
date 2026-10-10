"""Count SQL and ORM loads while rendering original routes with synthetic data."""
from pathlib import Path
from datetime import datetime,timedelta,date
from collections import Counter
import json,re,runpy
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.event import Event,EventType
from backend.models.participation import Participation
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]
urls=['/dashboard/','/events/','/events/?tab=archiv','/ggl/?tab=tabelle','/member/merch','/restaurants']
fixtures=[('baseline',5,5,3),('events_30',30,5,3),('members_30',5,30,3),('articles_30',5,5,30)]
for name,events,members,articles in fixtures:
    with app.app_context():
        db.create_all()
        now=datetime.now()
        for i in range(1,members+1):
            db.session.add(Member(id=i,vorname='Audit',nachname=f'Mitglied {i:03d}',
                email=f'scaling{i}@example.test',passwort_hash='unused',role=Role.MEMBER,
                beitritt=date(2020,1,1),is_active=True))
        db.session.flush()
        for i in range(1,events+1):
            db.session.add(Event(id=i,organisator_id=(i-1)%members+1,datum=now-timedelta(days=i),
                season=now.year,event_typ=EventType.MONATSESSEN,published=True,
                restaurant=f'Audit Restaurant {i:03d}',allow_ratings=True))
            for j in range(1,members+1):
                db.session.add(Participation(member_id=j,event_id=i,teilnahme=True,
                    guess_bill_amount_rappen=30000+j*100,points=10,diff_amount_rappen=j*100))
        for i in range(1,articles+1):
            db.session.add(MerchArticle(id=i,name=f'Audit Artikel {i:03d}',
                base_supplier_price_rappen=2000,base_member_price_rappen=3000))
            db.session.add(MerchVariant(article_id=i,color='Navy',size='M',
                supplier_price_rappen=2000,member_price_rappen=3000))
        db.session.commit();db.session.remove()
        engine=db.engine
        for url in urls:
            for repetition in range(2):
                db.session.remove();g.pop('_login_user',None)
                c=app.test_client()
                if url!='/restaurants':
                    with c.session_transaction() as s:s['_user_id']='1';s['_fresh']=True
                statements=Counter();loads=Counter()
                def sql(conn,cursor,statement,parameters,context,executemany):
                    statements[re.sub(r'\s+',' ',statement).strip()]+=1
                def loaded(session,obj):loads[type(obj).__name__]+=1
                sa_event.listen(engine,'before_cursor_execute',sql)
                sa_event.listen(Session,'loaded_as_persistent',loaded)
                row={'fixture':name,'events':events,'members':members,'articles':articles,'url':url,'repetition':repetition+1}
                try:
                    r=c.get(url,follow_redirects=False)
                    row.update(http=r.status_code,html_bytes=len(r.data))
                except Exception as e:row.update(error=type(e).__name__,message=str(e)[:160])
                finally:
                    sa_event.remove(engine,'before_cursor_execute',sql)
                    sa_event.remove(Session,'loaded_as_persistent',loaded)
                row.update(sql_count=sum(statements.values()),orm_loads=dict(loads),
                    writes=sum(n for s,n in statements.items() if s.split()[0].upper() in ('UPDATE','INSERT','DELETE')),
                    sql_profiles=[{'count':n,'sql':s} for s,n in statements.most_common()])
                results.append(row)
        db.session.remove();db.drop_all()
out={'method':'Original Flask routes/templates, SQLite memory, sockets blocked, 4 fixtures x 6 URLs x 2 fresh-session requests; SQL statements and ORM object loads, not latency.',
     'limitations':['No PostgreSQL query plans, row-scan counts, browser rendering or production timings.','Only past events in current season, one variant per article, no orders/claims/ratings.','Loaded ORM objects count load events, not necessarily unique database identities across a request.'],
     'results':results}
(OUT/'QUERY_SCALING_CHECKS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for r in results:
    if r['repetition']==1: print(json.dumps({k:v for k,v in r.items() if k!='sql_profiles'}))
