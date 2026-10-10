"""Original GET render scaling for orders, claims, and booking/receipt pairs."""
from pathlib import Path
from datetime import date
from collections import Counter
import runpy,json,re
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order import MerchOrder
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import FiscalYear,Account,AccountKind,Booking,BookingDirection,Receipt,MemberClaim,ClaimType
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]
urls=['/dashboard/','/member/merch?tab=orders','/admin/merch?tab=orders',
      '/accounting/?year=1','/accounting/?year=1&tab=journal','/accounting/?year=1&tab=posten']
for name,orders,claims,bookings in [('baseline',5,5,5),('orders_40',40,5,5),('claims_40',5,40,5),('bookings_receipts_40',5,5,40)]:
    with app.app_context():
        db.create_all()
        for i in range(1,6):
            db.session.add(Member(id=i,vorname='Audit',nachname=f'Commerce {i}',email=f'commerce{i}@example.test',
                passwort_hash='unused',role=Role.ADMIN if i==1 else Role.MEMBER))
        db.session.add(FiscalYear(id=1,year=2026,start_date=date(2026,1,1),end_date=date(2026,12,31)))
        db.session.add(Account(id=1,code='6100',name='Audit Aufwand',kind=AccountKind.EXPENSE))
        db.session.add(MerchArticle(id=1,name='Audit Artikel',base_supplier_price_rappen=2000,base_member_price_rappen=3000))
        db.session.add(MerchVariant(id=1,article_id=1,color='Navy',size='M',supplier_price_rappen=2000,member_price_rappen=3000))
        db.session.flush()
        for i in range(1,orders+1):
            db.session.add(MerchOrder(id=i,member_id=1,order_number=f'AUDIT-{i}',total_member_price_rappen=3000,
                total_supplier_price_rappen=2000,total_profit_rappen=1000))
            db.session.add(MerchOrderItem(order_id=i,article_id=1,variant_id=1,quantity=1,
                unit_member_price_rappen=3000,unit_supplier_price_rappen=2000,total_member_price_rappen=3000,
                total_supplier_price_rappen=2000,total_profit_rappen=1000))
        for i in range(1,claims+1):
            db.session.add(MemberClaim(member_id=1,claim_type=ClaimType.SONSTIGES,fiscal_year_id=1,expected_rappen=2000))
        for i in range(1,bookings+1):
            db.session.add(Booking(id=i,fiscal_year_id=1,booking_date=date(2026,6,1),description=f'Audit {i}',
                amount_rappen=2000,direction=BookingDirection.OUT,account_id=1,created_by=1))
            db.session.add(Receipt(booking_id=i,drive_file_id=f'audit-{i}',drive_file_name=f'audit-{i}.pdf',
                drive_folder_id='audit',uploader_id=1))
        db.session.commit();db.session.remove()
        engine=db.engine
        for url in urls:
            for repetition in range(2):
                db.session.remove();g.pop('_login_user',None)
                c=app.test_client()
                with c.session_transaction() as s:s['_user_id']='1';s['_fresh']=True
                statements=Counter();loads=Counter()
                def sql(conn,cursor,statement,parameters,context,executemany):statements[re.sub(r'\s+',' ',statement).strip()]+=1
                def loaded(session,obj):loads[type(obj).__name__]+=1
                sa_event.listen(engine,'before_cursor_execute',sql);sa_event.listen(Session,'loaded_as_persistent',loaded)
                row=dict(fixture=name,orders=orders,claims=claims,bookings=bookings,receipts=bookings,url=url,repetition=repetition+1)
                try:
                    r=c.get(url,follow_redirects=False)
                    html=r.get_data(as_text=True)
                    row.update(http=r.status_code,html_bytes=len(r.data),
                        selected_tabs=re.findall(r'aria-selected="true"[^>]*>(.*?)</a>',html,re.S))
                    row['selected_tabs']=[re.sub('<[^>]+>','',x).strip() for x in row['selected_tabs']]
                except Exception as e:row.update(error=type(e).__name__,message=str(e)[:160])
                finally:
                    sa_event.remove(engine,'before_cursor_execute',sql);sa_event.remove(Session,'loaded_as_persistent',loaded)
                row.update(sql_count=sum(statements.values()),orm_loads=dict(loads),
                    writes=sum(n for s,n in statements.items() if s.split()[0].upper() in ('UPDATE','INSERT','DELETE')),
                    sql_profiles=[{'count':n,'sql':s} for s,n in statements.most_common()])
                results.append(row)
        db.session.remove();db.drop_all()
out={'method':'4 synthetic datasets x 6 URLs x 2 fresh ORM sessions, original Flask routes/templates; SQL/ORM counters, no latency.',
     'limitations':['SQLite memory, no PostgreSQL query plans or network.','5 fixed members; orders/claims all belong to admin 1, one item per order.','Booking and linked receipt counts vary together; no actual Drive files or operations.','No events or historical fiscal years; results not directly comparable to other fixture baselines.'], 'results':results}
(OUT/'COMMERCE_SCALING_CHECKS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for r in results:
    if r['repetition']==1:print(json.dumps({k:v for k,v in r.items() if k!='sql_profiles'}))
