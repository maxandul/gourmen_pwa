"""Accounting audit on synthetic data. No external services or live finances."""
from pathlib import Path
from datetime import date
import runpy,json
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from flask import g
from itsdangerous import URLSafeTimedSerializer
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member,Role,Funktion
from backend.models.accounting import Account,AccountKind,Booking,Receipt,FiscalYearStatus,MemberClaim,ClaimType
from backend.services.accounting import AccountingService as A
app=create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI']=='sqlite:///:memory:' and app.config['TESTING']
results=[]

def client(m):
    g.pop('_login_user',None)
    c=app.test_client()
    with c.session_transaction() as s:
        s['_user_id']=str(m.id);s['_fresh']=True;s['csrf_token']='audit'
    return c

def token():
    return URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('audit')

def run(name,fn):
    with app.app_context():
        db.create_all()
        ms=[Member(vorname='Audit',nachname=str(i),email=f'accounting{i}@example.test',passwort_hash='unused') for i in range(4)]
        ms[0].role=Role.ADMIN;ms[1].funktion=Funktion.SCHATZMEISTER;ms[2].funktion=Funktion.RECHNUNGSPRUEFER
        db.session.add_all(ms);db.session.commit()
        fy=A.get_or_create_fiscal_year(2026)
        account=A.create_account('6100','Audit','expense',None)
        try: results.append({'case':name,'result':fn(ms,fy,account)})
        finally: db.session.remove();db.drop_all()

def booking(ms,fy,account,day=date(2026,6,1)):
    return A.create_booking(fy.id,day,'Audit',1999,'out',account.id,None,None,ms[1])

def form_case(ms,fy,account,day='2026-06-01'):
    r=client(ms[1]).post(f'/accounting/booking/new?year={fy.id}',data={
        'booking_date':day,'description':'Audit','amount_chf':'19.99','direction':'out',
        'account_id':account.id,'event_id':0,'member_id':0})
    rows=Booking.query.all()
    return {'status':r.status_code,'location':r.headers.get('Location'),
            'bookings':[{'date':str(b.booking_date),'fiscal_year':b.fiscal_year.year,'amount':b.amount_rappen} for b in rows]}
run('manual_booking_precision',form_case)
run('manual_booking_outside_year',lambda ms,fy,a:form_case(ms,fy,a,'2025-06-01'))

def locked(ms,fy,a,state):
    b=booking(ms,fy,a)
    fy.status=state;db.session.commit()
    errors=[]
    for fn in [lambda:booking(ms,fy,a),lambda:A.update_booking(b.id,amount_rappen=3000)]:
        try:fn();errors.append(None)
        except Exception as exc:db.session.rollback();errors.append(type(exc).__name__)
    return {'errors':errors,'booking_count':Booking.query.count(),'amount':db.session.get(Booking,b.id).amount_rappen}
for state in [FiscalYearStatus.IN_REVIEW,FiscalYearStatus.CLOSED]:
    run('locked_'+state.value,lambda ms,fy,a,s=state:locked(ms,fy,a,s))

def reattach(ms,fy,a):
    old=booking(ms,fy,a)
    receipt=Receipt(booking_id=old.id,drive_file_id='audit',drive_file_name='audit.pdf',drive_folder_id='audit',uploader_id=ms[1].id)
    db.session.add(receipt);db.session.commit()
    fy.status=FiscalYearStatus.CLOSED;db.session.commit()
    newfy=A.get_or_create_fiscal_year(2027)
    new=booking(ms,newfy,a,date(2027,1,1))
    r=client(ms[1]).post(f'/accounting/booking/{new.id}/receipt',data={'receipt_id':receipt.id,'csrf_token':token()})
    db.session.expire_all()
    return {'status':r.status_code,'old_booking':old.id,'new_booking':new.id,
            'receipt_booking':receipt.booking_id,'old_year_status':fy.status.value}
run('move_receipt_out_of_closed_year',reattach)

def role_matrix(ms,fy,a):
    b=booking(ms,fy,a)
    return [{'role':label,'index':client(m).get('/accounting/').status_code,
             'new_booking':client(m).get('/accounting/booking/new').status_code,
             'detail':client(m).get(f'/accounting/booking/{b.id}').status_code}
            for m,label in zip(ms,['admin','treasurer','reviewer','member'])]
run('read_create_role_matrix',role_matrix)

def claim_rights(ms,fy,a):
    claim=MemberClaim(member_id=ms[3].id,creditor_member_id=ms[1].id,
                      claim_type=ClaimType.SONSTIGES,expected_rappen=2000)
    db.session.add(claim);db.session.commit()
    errors=[]
    for m in [ms[3],ms[1],ms[1]]:
        try:A.confirm_private_payment(claim.id,m);errors.append(None)
        except Exception as exc:db.session.rollback();errors.append(type(exc).__name__)
    return {'errors_debtor_creditor_repeat':errors,'paid':claim.paid_rappen}
run('private_payment_ownership_repeat',claim_rights)
(OUT/'ACCOUNTING_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
