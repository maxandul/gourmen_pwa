"""Synthetic revision checks; external reports/notifications replaced, no live writes."""
from pathlib import Path
from datetime import date
from unittest.mock import patch
import runpy
import json
OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'), run_name='audit_setup')
from flask import g
from itsdangerous import URLSafeTimedSerializer
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.accounting import FiscalYearStatus, BudgetEntry, RevisionApproval
from backend.services.accounting import AccountingService as A
app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []

def post(m, url, **data):
    g.pop('_login_user', None)
    c = app.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(m.id); s['_fresh'] = True; s['csrf_token'] = 'audit'
    data['csrf_token'] = URLSafeTimedSerializer(app.secret_key, salt='wtf-csrf-token').dumps('audit')
    return c.post(url, data=data)

def run(name, fn):
    with app.app_context():
        db.create_all()
        ms = [Member(vorname='Audit', nachname=str(i), email=f'revision{i}@example.test', passwort_hash='unused') for i in range(4)]
        ms[0].role = Role.ADMIN
        ms[1].funktion = Funktion.SCHATZMEISTER
        ms[2].funktion = Funktion.RECHNUNGSPRUEFER
        db.session.add_all(ms); db.session.commit()
        fy = A.get_or_create_fiscal_year(2026)
        a = A.create_account('6100', 'Audit expense', 'expense', 'Audit')
        try:
            results.append({'case': name, 'result': fn(ms, fy, a)})
        finally:
            db.session.remove(); db.drop_all()

def book(ms, fy, a, amount=2000, direction='out'):
    return A.create_booking(fy.id, date(fy.year, 6, 1), 'Audit', amount, direction, a.id, None, None, ms[1])

def budget(ms, fy, a, state):
    A.set_budget(fy.id, a.id, 2000, ms[1])
    fy.status = state; db.session.commit()
    r = post(ms[1], f'/accounting/year/{fy.id}/budget', account_id=a.id, amount_chf='90.00')
    return {'http': r.status_code, 'year_status': fy.status.value,
            'budget': BudgetEntry.query.one().amount_rappen}
run('budget_during_review', lambda ms, fy, a: budget(ms, fy, a, FiscalYearStatus.IN_REVIEW))
run('budget_closed_blocked', lambda ms, fy, a: budget(ms, fy, a, FiscalYearStatus.CLOSED))

def deactivate(ms, fy, a):
    book(ms, fy, a)
    A.submit_for_review(fy.id, ms[1]); A.approve_year(fy.id, ms[2])
    before = sum(r['actual_rappen'] for r in A.get_budget_vs_actual(fy.id))
    A.update_account(a.id, is_active=False)
    return {'year_status': fy.status.value, 'detail_before': before,
            'detail_after': sum(r['actual_rappen'] for r in A.get_budget_vs_actual(fy.id)),
            'summary_expense': A.get_year_summary(fy.id)['expense_rappen']}
run('deactivated_account_closed_report', deactivate)

def refund(ms, fy, a):
    book(ms, fy, a, 2000, 'out'); book(ms, fy, a, 500, 'in')
    return {'account_actual': A.get_budget_vs_actual(fy.id)[0]['actual_rappen'],
            'year_result': A.get_year_summary(fy.id)['result_rappen']}
run('opposite_directions_same_account', refund)

def opening(ms, fy, a):
    earlier = A.get_or_create_fiscal_year(2025)
    b = book(ms, earlier, a)
    A.submit_for_review(fy.id, ms[1]); A.approve_year(fy.id, ms[2])
    before = A.get_opening_balance(fy.id)
    A.update_booking(b.id, amount_rappen=5000)
    return {'closed_year': fy.status.value, 'prior_year': earlier.status.value,
            'opening_before': before, 'opening_after': A.get_opening_balance(fy.id)}
run('closed_year_opening_changes', opening)

def failure(ms, fy, a):
    A.submit_for_review(fy.id, ms[1])
    with patch('backend.routes.accounting.AccountingPdfService.generate_report', side_effect=RuntimeError('synthetic report failure')) as report:
        r1 = post(ms[2], f'/accounting/year/{fy.id}/approve')
        r2 = post(ms[2], f'/accounting/year/{fy.id}/approve')
    approval = RevisionApproval.query.one()
    return {'http': [r1.status_code, r2.status_code], 'year_status': fy.status.value,
            'report_id': approval.report_drive_id, 'report_attempts': report.call_count}
run('report_failure_then_retry', failure)

def roles(ms, fy, a):
    rows = []
    with patch('backend.routes.accounting.NotifierService.send_push_notification'), patch('backend.routes.accounting.AccountingPdfService.generate_report', return_value=b'audit'), patch('backend.routes.accounting.AccountingService.get_receipt_folder_id', return_value='audit'), patch('backend.routes.accounting.DriveStorageService.upload_bytes', return_value={'id':'audit-report'}):
        for action, state in [('submit', FiscalYearStatus.OPEN), ('approve', FiscalYearStatus.IN_REVIEW), ('withdraw', FiscalYearStatus.IN_REVIEW), ('revoke', FiscalYearStatus.CLOSED)]:
            for m, label in zip(ms, ['admin','treasurer','reviewer','member']):
                # A distinct year prevents stale relationships between role probes.
                test_fy = A.get_or_create_fiscal_year(2030 + len(rows))
                if state == FiscalYearStatus.CLOSED:
                    A.submit_for_review(test_fy.id, ms[1]); A.approve_year(test_fy.id, ms[2])
                else:
                    test_fy.status = state; db.session.commit()
                r = post(m, f'/accounting/year/{test_fy.id}/{action}')
                db.session.expire_all()
                rows.append({'action': action, 'role': label, 'http': r.status_code, 'state': test_fy.status.value})
    return rows
run('revision_action_role_matrix', roles)
(OUT/'REVISION_CHECKS.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results, indent=2))
