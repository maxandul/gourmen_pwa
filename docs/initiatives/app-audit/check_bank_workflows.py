"""Reproduce bank-import boundaries with synthetic CSVs and memory-only SQLite."""
from pathlib import Path
import csv
import io
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from flask import g
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import text
from werkzeug.datastructures import FileStorage
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Funktion
from backend.models.accounting import (Booking, BankTransaction, MemberClaim,
                                       ClaimType, FiscalYearStatus)
from backend.services.accounting import AccountingService as A
from backend.services.bank_import import BankImportService as B

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
results = []
HEADER = ['Datum', 'Buchungstext', 'Belastung CHF', 'Gutschrift CHF',
          'ZKB-Referenz', 'Valuta', 'Betrag Detail', 'Whg', 'Zahlungszweck', 'Details']

def payload(rows):
    out = io.StringIO()
    w = csv.writer(out, delimiter=';')
    w.writerow(HEADER)
    w.writerows(rows)
    return out.getvalue().encode('utf-8')

def row(amount='20.00', ref='AUDIT-1', direction='in', purpose='Audit'):
    return ['01.06.2026', 'Gutschrift Auftraggeber: Audit Member',
            amount if direction == 'out' else '', amount if direction == 'in' else '',
            ref, '', '', '', purpose, '']

def upload(ms, rows):
    return B.import_statement(FileStorage(stream=io.BytesIO(payload(rows)),
                                         filename='synthetic-audit.csv'), ms[0])

def client(ms):
    g.pop('_login_user', None)
    c = app.test_client()
    with c.session_transaction() as s:
        s['_user_id'] = str(ms[0].id)
        s['_fresh'] = True
        s['csrf_token'] = 'audit'
    return c

def post_book(ms, tx, account, claim, member=None):
    token = URLSafeTimedSerializer(app.secret_key, salt='wtf-csrf-token').dumps('audit')
    return client(ms).post(f'/accounting/import/tx/{tx.id}/book', data={
        'csrf_token': token, 'account_id': account.id, 'claim_id': claim.id,
        'member_id': member.id if member else ''})

def claim_for(ms, fy, kind=ClaimType.MERCH):
    claim = MemberClaim(member_id=ms[1].id, fiscal_year_id=fy.id,
                        claim_type=kind, expected_rappen=2000)
    db.session.add(claim)
    db.session.commit()
    return claim

def snapshot(tx, claim):
    db.session.expire_all()
    return {'tx_status': tx.status.value, 'tx_amount': tx.amount_rappen,
            'paid': claim.paid_rappen, 'claim_status': claim.status.value,
            'bookings': [{'amount': b.amount_rappen, 'member': b.member_id,
                          'direction': b.direction.value} for b in Booking.query.order_by(Booking.id)]}

def run(name, fn):
    with app.app_context():
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        assert db.session.execute(text('PRAGMA foreign_keys')).scalar() == 1
        db.create_all()
        ms = [Member(vorname='Audit', nachname=f'Member{i}',
                     email=f'bank{i}@example.test', passwort_hash='unused') for i in range(3)]
        ms[0].funktion = Funktion.SCHATZMEISTER
        db.session.add_all(ms)
        db.session.commit()
        fy = A.get_or_create_fiscal_year(2026)
        account = A.create_account('3400', 'Audit Merch', 'income', None)
        try:
            results.append({'case': name, 'result': fn(ms, fy, account)})
        finally:
            db.session.remove()
            db.drop_all()

def duplicate(ms, fy, a):
    first = upload(ms, [row()])
    second = upload(ms, [row()])
    return {'first_new': first.new_count, 'second_new': second.new_count,
            'second_duplicates': second.duplicate_count, 'tx_count': BankTransaction.query.count()}
run('repeat_import_same_reference', duplicate)

def no_ref(ms, fy, a):
    s = upload(ms, [row(ref='', purpose='Invoice A'), row(ref='', purpose='Invoice B')])
    return {'new': s.new_count, 'duplicates': s.duplicate_count,
            'purposes_retained': [t.zahlungszweck for t in BankTransaction.query.all()]}
run('different_purpose_without_reference', no_ref)

def split(ms, fy, a, complete=False):
    parent = row(amount='100.00')
    parent[1] = 'Gutschriften eBanking (2)'
    detail = ['', 'First Member', '', '', '', '', '40.00', 'CHF', '', '']
    rows = [parent, detail]
    if complete:
        rows.append(['', 'Second Member', '', '', '', '', '60.00', 'CHF', '', ''])
    s = upload(ms, rows)
    return {'new': s.new_count, 'rows': [{'amount': t.amount_rappen,
             'original': t.amount_original, 'status': t.status.value} for t in s.transactions]}
run('collective_missing_detail', split)
run('collective_complete', lambda ms, fy, a: split(ms, fy, a, complete=True))

def retry(ms, fy, a):
    c = claim_for(ms, fy)
    upload(ms, [row(amount='25.00')])
    tx = BankTransaction.query.one()
    states = []
    for _ in range(2):
        r = post_book(ms, tx, a, c)
        states.append({'http': r.status_code, **snapshot(tx, c)})
    return states
run('missing_rounding_account_retry', retry)

def overpay(ms, fy, a):
    A.create_account('3410', 'Audit rounding', 'income', None)
    c = claim_for(ms, fy)
    statement = upload(ms, [row(amount='25.00')])
    tx = BankTransaction.query.one()
    r = post_book(ms, tx, a, c)
    try:
        B.delete_import(statement.id)
        error = None
    except Exception as exc:
        error = type(exc).__name__
    return {'http': r.status_code, 'delete_error': error, **snapshot(tx, c)}
run('overpayment_split_and_delete_guard', overpay)

def assign(ms, fy, a, direction='in', mismatch=False):
    c = claim_for(ms, fy)
    upload(ms, [row(direction=direction)])
    tx = BankTransaction.query.one()
    r = post_book(ms, tx, a, c, ms[2] if mismatch else None)
    return {'http': r.status_code, 'claim_member': c.member_id, **snapshot(tx, c)}
run('outgoing_payment_settles_claim', lambda ms, fy, a: assign(ms, fy, a, direction='out'))
run('booking_member_differs_from_claim', lambda ms, fy, a: assign(ms, fy, a, mismatch=True))

def partial(ms, fy, a):
    c = claim_for(ms, fy)
    upload(ms, [row(amount='8.00'), row(amount='12.00', ref='AUDIT-2')])
    states = []
    for tx in BankTransaction.query.order_by(BankTransaction.id).all():
        B.book_transaction(tx.id, account_id=a.id, claim_id=c.id, booked_by=ms[0])
        states.append(snapshot(tx, c))
    try:
        B.book_transaction(tx.id, account_id=a.id, claim_id=c.id, booked_by=ms[0])
        error = None
    except Exception as exc:
        error = type(exc).__name__
    return {'states': states, 'repeat_error': error, 'count_after_repeat': Booking.query.count()}
run('partial_full_and_repeat', partial)

def edit(ms, fy, a):
    c = claim_for(ms, fy)
    upload(ms, [row()])
    tx = BankTransaction.query.one()
    b = B.book_transaction(tx.id, account_id=a.id, claim_id=c.id, booked_by=ms[0])
    r = client(ms).post(f'/accounting/booking/{b.id}/edit', data={
        'booking_date': '2026-06-01', 'description': 'Audit correction',
        'amount_chf': '5.00', 'direction': 'in', 'account_id': a.id,
        'event_id': 0, 'member_id': ms[1].id})
    return {'http': r.status_code, **snapshot(tx, c)}
run('edit_imported_booking_amount', edit)

def locked(ms, fy, a):
    c = claim_for(ms, fy)
    upload(ms, [row()])
    tx = BankTransaction.query.one()
    fy.status = FiscalYearStatus.CLOSED
    db.session.commit()
    try:
        B.book_transaction(tx.id, account_id=a.id, claim_id=c.id, booked_by=ms[0])
        error = None
    except Exception as exc:
        error = type(exc).__name__
    return {'error': error, **snapshot(tx, c)}
run('closed_year_import_booking_blocked', locked)

def malformed(ms, fy, a):
    try:
        client(ms).post('/accounting/import', data={
            'file': (io.BytesIO(payload([row(), row(amount='abc', ref='AUDIT-2')])), 'audit.csv')},
            content_type='multipart/form-data')
        error = None
    except Exception as exc:
        error = type(exc).__name__
    return {'error': error, 'transactions': BankTransaction.query.count(),
            'bookings': Booking.query.count()}
run('invalid_amount_in_csv', malformed)

(OUT / 'BANK_CHECKS.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(results, indent=2, ensure_ascii=False))
