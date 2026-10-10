"""Isolated receipt/revision audit. All Drive transport replaced by synthetic responses."""
from pathlib import Path
from datetime import date, datetime
from unittest.mock import patch
import io
import json
import runpy
OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'), run_name='audit_setup')
from flask import g
from itsdangerous import URLSafeTimedSerializer
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.event import Event, EventType, EventAudience
from backend.models.accounting import Receipt, RevisionApproval
from backend.services.accounting import AccountingService as A
app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []

def client(m):
    g.pop('_login_user', None)
    c = app.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(m.id); s['_fresh'] = True; s['csrf_token'] = 'audit'
    return c

def run(name, fn):
    with app.app_context():
        db.create_all()
        ms = [Member(vorname='Audit', nachname=str(i), email=f'receipt{i}@example.test', passwort_hash='unused') for i in range(5)]
        ms[0].role = Role.ADMIN
        ms[1].funktion = Funktion.SCHATZMEISTER
        ms[2].funktion = Funktion.RECHNUNGSPRUEFER
        db.session.add_all(ms); db.session.commit()
        fy = A.get_or_create_fiscal_year(date.today().year)
        a = A.create_account('6100', 'Audit expense', 'expense', None)
        b = A.create_booking(fy.id, date.today(), 'AUDIT_PRIVATE_BOOKING', 2000, 'out', a.id, None, None, ms[1])
        try: results.append({'case': name, 'result': fn(ms, fy, b)})
        finally: db.session.remove(); db.drop_all()

def disclosure(ms, fy, b):
    e = Event(organisator_id=ms[0].id, datum=datetime.now(), event_typ=EventType.VORSTANDSSITZUNG,
              audience=EventAudience.BOARD, season=fy.year, restaurant='AUDIT_BOARD_RESTAURANT')
    db.session.add(e); db.session.commit()
    c = client(ms[3])
    r = c.get('/accounting/receipt/upload')
    body = r.get_data(as_text=True)
    return {'upload_http': r.status_code, 'booking_label_exposed': 'AUDIT_PRIVATE_BOOKING' in body,
            'board_label_exposed': 'AUDIT_BOARD_RESTAURANT' in body,
            'booking_detail_http': c.get(f'/accounting/booking/{b.id}').status_code,
            'event_visible': e.is_visible_to(ms[3])}
run('member_upload_choices_disclosure', disclosure)

def upload(ms, fy, b):
    with patch.object(A, 'get_receipt_folder_id', return_value='audit-folder'), patch('backend.services.accounting.DriveStorageService.upload_bytes', return_value={'id':'audit-file','name':'audit.pdf'}):
        c = client(ms[3])
        r = c.post('/accounting/receipt/upload', data={'file':(io.BytesIO(b'audit'),'audit.pdf'),
                   'booking_id': b.id, 'suggested_event_id': 0, 'suggested_account_id': 0}, content_type='multipart/form-data')
        target = r.headers.get('Location')
        follow = c.get(target).status_code if target else None
    receipt = Receipt.query.one()
    return {'http':r.status_code,'location':target,'follow_http':follow,
            'receipt_booking':receipt.booking_id,'uploader':receipt.uploader_id}
run('member_direct_receipt_upload_redirect', upload)

def roles(ms, fy, b):
    receipt = Receipt(drive_file_id='audit', drive_file_name='audit.pdf', drive_folder_id='audit', uploader_id=ms[3].id)
    db.session.add(receipt); db.session.commit()
    with patch.object(A, 'download_receipt', return_value=(b'audit','application/pdf','audit.pdf')) as download:
        checks = [{'role':label,'http':client(m).get(f'/accounting/receipt/{receipt.id}').status_code}
                  for m,label in zip(ms,['admin','treasurer','reviewer','owner','other_member'])]
    return {'checks':checks,'download_calls':download.call_count}
run('receipt_download_ownership', roles)

def cycle(ms, fy, b):
    A.submit_for_review(fy.id, ms[1]); A.approve_year(fy.id, ms[2])
    A.set_approval_report(fy.id, 'audit-old-report')
    A.revoke_approval(fy.id, ms[2])
    remaining = RevisionApproval.query.count()
    A.withdraw_from_review(fy.id, ms[1]); A.update_booking(b.id, amount_rappen=3000)
    A.submit_for_review(fy.id, ms[1])
    db.session.expire_all()
    try:
        A.approve_year(fy.id, ms[2]); error = None
    except Exception as exc: error = type(exc).__name__
    return {'approvals_after_revoke':remaining,'final_status':fy.status.value,
            'new_approval_error':error,'approval_count':RevisionApproval.query.count(),
            'report_ids':[a.report_drive_id for a in RevisionApproval.query.all()]}
run('revoke_correct_reapprove_history', cycle)

def comments(ms, fy, b):
    comment = A.add_revision_comment(b.id, None, ms[2], 'Audit unresolved')
    A.submit_for_review(fy.id, ms[1]); A.approve_year(fy.id, ms[2])
    token = URLSafeTimedSerializer(app.secret_key,salt='wtf-csrf-token').dumps('audit')
    rejected = client(ms[3]).post(f'/accounting/comment/{comment.id}/resolve',data={'csrf_token':token}).status_code
    r = client(ms[1]).post(f'/accounting/comment/{comment.id}/resolve',data={'csrf_token':token})
    return {'approved_with_open_comment':fy.status.value,'member_resolve_http':rejected,
            'treasurer_resolve_http':r.status_code,'resolved_after_close':comment.resolved}
run('unresolved_comment_approval_and_resolution', comments)

(OUT/'RECEIPT_CHECKS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
