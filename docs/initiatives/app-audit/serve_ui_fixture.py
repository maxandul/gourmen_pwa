"""Loopback-only UI fixture: original app, synthetic SQLite data, no outbound TCP.

Run with bundled Python. No production secrets/config/database; no app code edits.
Audit-only login/frame endpoints exist only in this process, never in the app.
"""
from pathlib import Path
import runpy
from datetime import date, datetime, timedelta
from types import SimpleNamespace

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from flask import request, redirect, session, abort
from flask_login import login_user, logout_user
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member, Role, Funktion
from backend.models.event import Event, EventType
from backend.models.participation import Participation, Esstyp
from backend.models.accounting import FiscalYear, Account, AccountKind
from backend.models.merch_article import MerchArticle
from backend.models.merch_variant import MerchVariant
from backend.services.drive_storage import DriveStorageService, FolderListing
from werkzeug.security import generate_password_hash
from markupsafe import escape

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
app.config.update(DRIVE_FEATURE_ENABLED=True, GOOGLE_DRIVE_ID='audit-drive',
                  DRIVE_ARCHIVE_FOLDER_ID='audit-archive', DEBUG=False)
# Deterministic Drive metadata; every real network connection remains blocked.
DriveStorageService.list_folder = staticmethod(lambda folder_id, **kw: FolderListing(
    folder_id=folder_id, subfolders=[], files=[]))
DriveStorageService.search_files = staticmethod(lambda *args, **kw: [])
DriveStorageService.get_folder_breadcrumb = staticmethod(lambda *args, **kw: [
    SimpleNamespace(id='audit-drive', name='Audit-Dokumente')])

with app.app_context():
    db.create_all()
    for idx, (name, role, function) in enumerate([
        ('Admin', Role.ADMIN, Funktion.SCHATZMEISTER),
        ('Mitglied', Role.MEMBER, Funktion.MEMBER),
        ('Revisor', Role.MEMBER, Funktion.RECHNUNGSPRUEFER),
        ('Schatzmeister', Role.MEMBER, Funktion.SCHATZMEISTER),
    ], 1):
        db.session.add(Member(id=idx, vorname='Audit', nachname=name,
            email=f'audit-{idx}@example.test', role=role, funktion=function,
            vorstandsmitglied=idx in (1, 3, 4), beitritt=date(2020, 1, 1),
            passwort_hash=generate_password_hash('SyntheticAuditOnly')))
    db.session.flush()
    for idx, offset in enumerate([-60, -20, 5, 35], 1):
        db.session.add(Event(id=idx, organisator_id=1,
            datum=datetime.now().replace(hour=19, minute=0, second=0, microsecond=0) + timedelta(days=offset),
            event_typ=EventType.MONATSESSEN, season=2026,
            restaurant=f'Audit-Restaurant {idx}', kueche='Mediterran',
            notizen='Erfundene Daten fuer die lokale Oberflaechenpruefung.',
            published=True, allow_ratings=True))
        for uid in range(1, 5):
            db.session.add(Participation(member_id=uid, event_id=idx,
                teilnahme=True, esstyp=Esstyp.NORMAL, guess_bill_amount_rappen=30000 + uid * 1000))
    db.session.add(FiscalYear(id=1, year=2026, start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31), membership_fee_rappen=84000))
    db.session.add(Account(code='3000', name='Audit-Mitgliederbeitraege', kind=AccountKind.INCOME, group_name='Einnahmen'))
    db.session.add(Account(code='6100', name='Audit-Monatsessen', kind=AccountKind.EXPENSE, group_name='Ausgaben'))
    db.session.add(MerchArticle(id=1, name='Audit-Shirt', description='Beispielartikel',
        base_supplier_price_rappen=2000, base_member_price_rappen=3000))
    db.session.flush()
    for size in ('M', 'L'):
        db.session.add(MerchVariant(article_id=1, color='Navy', size=size,
            supplier_price_rappen=2000, member_price_rappen=3000))
    db.session.commit()


@app.route('/__audit/login/<int:uid>')
def audit_login(uid):
    if uid == 0:
        logout_user()
    else:
        user = db.session.get(Member, uid)
        if user is None:
            abort(404)
        login_user(user)
    target = request.args.get('next', '/dashboard/')
    if not target.startswith('/') or target.startswith('//'):
        abort(400)
    return redirect(target)


@app.route('/__audit/frame')
def audit_frame():
    width = min(1600, max(320, request.args.get('width', 390, type=int)))
    target = request.args.get('path', '/events/3')
    if not target.startswith('/') or target.startswith('//'):
        abort(400)
    return f'''<!doctype html><html lang="de"><title>Lokale Audit-Viewport-Simulation</title>
    <body style="margin:0;background:#ddd"><p style="margin:8px">Audit – {width} CSS-px, synthetische Daten; kein echtes Mobilgeraet</p>
    <iframe title="Audit-App" src="{escape(target)}" style="display:block;width:{width}px;height:820px;border:0"></iframe></body></html>'''


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5087, debug=False, use_reloader=False, threaded=False)
