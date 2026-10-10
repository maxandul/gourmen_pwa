"""Local synthetic UI probes; original fixture isolation, no real MFA operations."""
import runpy
import time
from threading import Lock
from pathlib import Path

ns = runpy.run_path(str(Path(__file__).with_name('serve_ui_fixture.py')))
app = ns['app']
from flask import render_template, flash, request
from types import SimpleNamespace
from backend.models.accounting import Booking, BookingDirection, Receipt, BankStatementImport, MemberClaim, ClaimType

# Deterministic folder tree, including one local failure path; no Drive call.
def probe_subfolders(folder_id):
    if folder_id == 'audit-failure':
        raise RuntimeError('Synthetic folder listing failure')
    return {
        'audit-drive': [SimpleNamespace(id='audit-documents', name='Audit-Unterlagen'),
                        SimpleNamespace(id='audit-failure', name='Audit-Ladefehler')],
        'audit-documents': [SimpleNamespace(id='audit-child', name='Audit-Protokolle')],
    }.get(folder_id, [])

ns['DriveStorageService'].list_subfolders_only = staticmethod(probe_subfolders)

root_probe_attempts = 0
root_delay_attempts = 0
root_delay_lock = Lock()

@app.before_request
def probe_root_failure():
    global root_probe_attempts, root_delay_attempts
    if request.path == '/docs/api/root' and 'audit_root_delay=1' in (request.referrer or ''):
        with root_delay_lock:
            root_delay_attempts += 1
            attempt = root_delay_attempts
        # Audit-only timing: first request of each pair finishes before the second.
        time.sleep(2 if attempt % 2 else 12)
    if request.path == '/docs/api/root' and 'audit_root_error_once=1' in (request.referrer or ''):
        root_probe_attempts += 1
        if root_probe_attempts == 1:
            return {'error': 'Synthetic transient root lookup failure'}, 503
    if request.path == '/docs/api/root' and 'audit_root_error=1' in (request.referrer or ''):
        return {'error': 'Synthetic root lookup failure'}, 503

# More than two archive pages, exclusively in the original in-memory fixture.
with app.app_context():
    ns['db'].session.add(Booking(
        id=1, fiscal_year_id=1, booking_date=ns['date'](2026, 9, 1),
        description='Audit-Buchung fuer die Tastaturpruefung', amount_rappen=12345,
        direction=BookingDirection.OUT, account_id=2, created_by=1))
    ns['db'].session.add(Receipt(
        id=1, drive_file_id='audit-nonexistent-file',
        drive_file_name='Audit-Beleg-September.pdf', drive_folder_id='audit-folder',
        file_type='application/pdf', uploader_id=2))
    ns['db'].session.add(BankStatementImport(
        id=1, fiscal_year_id=1, filename='Audit-Kontoauszug-September-2026.csv',
        imported_by=1, row_count=0, new_count=0, duplicate_count=0))
    ns['db'].session.add(MemberClaim(
        member_id=2, fiscal_year_id=1, claim_type=ClaimType.MITGLIEDERBEITRAG,
        expected_rappen=84000, paid_rappen=20000))
    ns['db'].session.add(ns['MerchArticle'](
        id=2, name='Audit-Tasse', description='Zweiter synthetischer Artikel',
        base_supplier_price_rappen=1000, base_member_price_rappen=1500))
    ns['db'].session.flush()
    ns['db'].session.add(ns['MerchVariant'](
        article_id=2, color='Weiss', size='Standard',
        supplier_price_rappen=1000, member_price_rappen=1500))
    for probe_id in range(10, 35):
        ns['db'].session.add(ns['Event'](
            id=probe_id, organisator_id=1,
            datum=ns['datetime'].now() - ns['timedelta'](days=100 + probe_id),
            event_typ=ns['EventType'].MONATSESSEN, season=2026,
            restaurant=f'Audit-Archiv {probe_id}', published=True))
    ns['db'].session.commit()

@app.route('/__audit/security-warning')
def security_warning():
    return render_template('admin/member_security_overview.html',
        member=ns['db'].session.get(ns['Member'], 2),
        mfa_data=SimpleNamespace(is_totp_enabled=True, activated_at=None,
                                 last_verified_at=None),
        unused_backup_codes=[], recent_events=[])

@app.after_request
def add_status_probe(response):
    if request.path == '/member/technical' and response.status_code == 200:
        probe = '''<button type="button" id="audit-status-probe" onclick="gourmenPWA.showUpdateStatus(document.getElementById('sw-status'),document.querySelector('#sw-status .status-text'),'Synthetischer Status','info')">Audit: nur Status rendern</button>'''
        response.set_data(response.get_data(as_text=True).replace('<h1', probe + '<h1', 1))
    return response

@app.route('/__audit/registry-probes')
def registry_probes():
    flash('Synthetischer Audit-Hinweis', 'info')
    return render_template('auth/backup_codes.html', backup_codes=['AUDIT-ONLY-0001', 'AUDIT-ONLY-0002'])

@app.route('/__audit/document-actions')
def document_action_probes():
    # Original list/dialog templates, synthetic display rows; no real file IDs.
    rows = [SimpleNamespace(
        name=name, document_id=901 + index, web_view_link=None, icon_name='file',
        uploader_display='Audit', relative_label='synthetisch',
        document_under_archive=index == 1)
        for index, name in enumerate(['Audit-Protokoll-Alpha.pdf', 'Audit-Protokoll-Beta.pdf'])]
    return render_template('docs/folder.html', root_folder_id='audit-drive',
        drive_folder_id='audit-documents', folder_display_name='Audit-Aktionen',
        listing=SimpleNamespace(files=rows, subfolders=[]), breadcrumbs=[],
        search_query='', search_hits=[], archive_folder_id='audit-archive',
        folder_drive_link=None, max_file_size_mb=100, allowed_mime_types=[],
        events=[], docs_actions_next='/__audit/document-actions')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5087, debug=False, use_reloader=False, threaded=False)
