"""Synthetic Merch audit; no production, no external connections."""
from pathlib import Path
import json
import runpy
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from sqlalchemy import text
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.models.merch_order import MerchOrder
from backend.models.merch_order_item import MerchOrderItem
from backend.models.accounting import MemberClaim
app=create_app('testing')
assert app.config['TESTING'] and app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:'
results=[]

def client(m):
    g.pop('_login_user',None)
    c=app.test_client()
    with c.session_transaction() as s:
        s['_user_id']=str(m.id)
        s['_fresh']=True
    return c

def post(m,path,data):
    r=client(m).post(path,data=data)
    return {'status':r.status_code,'location':r.headers.get('Location'),
            'foreign_key_error_visible':'FOREIGN KEY constraint failed' in r.get_data(as_text=True)}

def form(a,qty='1',size='M'):
    return {f'color_{a.id}[]':['Navy'],f'size_{a.id}[]':[size],f'quantity_{a.id}[]':[qty]}

def snapshot():
    db.session.expire_all()
    return {'orders':[{'id':o.id,'total':o.total_member_price_rappen,'status':o.status.value,
                      'delivered_at':str(o.delivered_at) if o.delivered_at else None,
                      'items':len(o.order_items)} for o in MerchOrder.query.all()],
            'claims':[{'expected':c.expected_rappen,'paid':c.paid_rappen} for c in MemberClaim.query.all()]}

def run(name,fn):
    with app.app_context():
        db.create_all()
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        assert db.session.execute(text('PRAGMA foreign_keys')).scalar()==1
        admin=Member(vorname='Audit',nachname='Admin',email='admin@example.test',passwort_hash='unused',role=Role.ADMIN)
        member=Member(vorname='Audit',nachname='Member',email='member@example.test',passwort_hash='unused')
        a=MerchArticle(name='Audit Shirt',base_supplier_price_rappen=1000,base_member_price_rappen=2000)
        db.session.add_all([admin,member,a]); db.session.flush()
        v=MerchVariant(article_id=a.id,color='Navy',size='M',supplier_price_rappen=1000,member_price_rappen=2000)
        db.session.add(v); db.session.commit()
        try:
            results.append({'case':name,'result':fn(admin,member,a,v)})
        finally:
            db.session.remove(); db.drop_all()

for qty,size in [('0','M'),('-1','M'),('1','missing'),('1','M')]:
    run('order_'+qty+'_'+size,lambda ad,m,a,v,q=qty,s=size:
        {'response':post(m,'/member/merch/order',form(a,q,s)),'after':snapshot()})

def status_edit(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    post(ad,f'/admin/merch/orders/{o.id}/status-update',{'status':'GELIEFERT'})
    first=snapshot()
    post(ad,f'/admin/merch/orders/{o.id}/status-update',{'status':'BESTELLT'})
    edited=post(m,f'/member/merch/order/{o.id}/edit',form(a,'3'))
    post(ad,f'/admin/merch/orders/{o.id}/status-update',{'status':'WIRD_GELIEFERT'})
    return {'first':first,'edit':edited,'after':snapshot()}
run('reopen_edit_stale_claim',status_edit)

def article_edit(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    response=post(ad,f'/admin/merch/articles/{a.id}/edit',{'name':'Changed','colors':['Navy'],
        'sizes':['M'],'base_supplier_price_chf':'10','base_member_price_chf':'20','is_active':'on'})
    db.session.expire_all()
    return {'response':response,'name':a.name,'variants':MerchVariant.query.count(),'after':snapshot()}
run('edit_article_with_existing_order',article_edit)

def inactive_edit(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    v.is_active=False; db.session.commit()
    response=post(m,f'/member/merch/order/{o.id}/edit',form(a))
    return {'response':response,'after':snapshot()}
run('inactive_variant_silently_removed',inactive_edit)

def rights(ad,m,a,v):
    post(ad,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    read=client(m).get(f'/member/merch/order/{o.id}').status_code
    edit=post(m,f'/member/merch/order/{o.id}/edit',form(a,'3'))
    status=post(m,f'/admin/merch/orders/{o.id}/status-update',{'status':'GELIEFERT'})
    return {'other_order_read':read,'other_order_edit':edit,'status_as_member':status,'after':snapshot()}
run('ownership_and_status_guards',rights)

def repeat(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    post(m,'/member/merch/order',form(a))
    return snapshot()
run('repeat_order_post',repeat)

def inactive_get(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    v.is_active=False; db.session.commit()
    try:
        response={'status':client(m).get('/member/merch').status_code}
    except Exception as exc:
        response={'exception':type(exc).__name__,'message':str(exc).split('[SQL:')[0][:150]}
        db.session.rollback()
    return {'response':response,'variants_remaining':MerchVariant.query.count(),'after':snapshot()}
run('get_shop_inactive_ordered_variant',inactive_get)

def claim_failure(ad,m,a,v):
    from unittest.mock import patch
    from backend.services.accounting import AccountingService
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    with patch.object(AccountingService,'create_claim_for_merch_order',side_effect=RuntimeError('Audit injected failure')):
        response=post(ad,f'/admin/merch/orders/{o.id}/status-update',{'status':'WIRD_GELIEFERT'})
    return {'response':response,'after':snapshot()}
run('status_committed_before_claim_failure',claim_failure)

def new_article(ad,m,a,v,price='19.99',colors=None):
    response=post(ad,'/admin/merch/articles/new',{'name':'New Audit','colors':colors or ['Navy'],
        'sizes':['M'],'base_supplier_price_chf':'10','base_member_price_chf':price,'is_active':'on'})
    created=MerchArticle.query.filter(MerchArticle.id!=a.id).first()
    return {'response':response,'price':created.base_member_price_rappen if created else None,
            'variants':[{'color':x.color,'size':x.size} for x in created.variants] if created else []}
run('price_decimal_precision',new_article)
run('price_negative',lambda ad,m,a,v:new_article(ad,m,a,v,'-5'))
run('duplicate_variant_input',lambda ad,m,a,v:new_article(ad,m,a,v,'20',['Navy','Navy']))

def uneven(ad,m,a,v):
    data=form(a)
    data[f'quantity_{a.id}[]']=['1','9']
    response=post(m,'/member/merch/order',data)
    return {'response':response,'after':snapshot()}
run('uneven_form_arrays',uneven)

def redirect_target(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    return post(ad,f'/admin/merch/orders/{o.id}/status',
                {'status':'BESTELLT','next':'//example.invalid/audit'})
run('status_protocol_relative_redirect',redirect_target)

def repricing(ad,m,a,v):
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    v.member_price_rappen=3000; db.session.commit()
    before=snapshot()
    response=post(m,f'/member/merch/order/{o.id}/edit',form(a))
    return {'before_edit':before,'response':response,'after':snapshot()}
run('unchanged_order_repriced',repricing)

def stats_filters(ad,m,a,v):
    from flask import template_rendered
    post(m,'/member/merch/order',form(a))
    o=MerchOrder.query.one()
    post(ad,f'/admin/merch/orders/{o.id}/status-update',{'status':'GELIEFERT'})
    rows=[]
    for sort in ['member','article']:
        captured=[]
        def record(sender,template,context,**extra):
            captured.append(context)
        template_rendered.connect(record,app)
        try:
            response=client(ad).get('/admin/merch?tab=orders&sort='+sort)
        finally:
            template_rendered.disconnect(record,app)
        ctx=captured[-1]
        rows.append({'sort':sort,'status':response.status_code,'status_filter':ctx.get('status_filter'),
                     'order_count':len(ctx['orders']) if ctx.get('orders') is not None else ctx.get('orders_group_count')})
    return rows
run('grouping_changes_status_filter',stats_filters)
(OUT/'MERCH_CHECKS.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(results,indent=2,ensure_ascii=True))
