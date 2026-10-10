"""Audit-only original route/service search probes; no network or real documents."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch, MagicMock
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from backend.app import create_app
from backend.extensions import db
from backend.models.member import Member
from backend.services.drive_storage import DriveStorageService as D, DriveError, FolderListing

app = create_app('testing')
assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
app.config['DRIVE_FEATURE_ENABLED'] = True
with app.app_context():
    db.create_all()
    db.session.add(Member(id=1, vorname='Audit', nachname='Suche',
                         email='audit-search@example.test', passwort_hash='unused'))
    db.session.commit()
results = []

def request_case(name, url, *, error=False, hits=None):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    listing = FolderListing(folder_id='audit-folder', files=[], subfolders=[
        NS(id='audit-child', name='Audit-Unterordner', direct_child_count=1)])
    with patch.object(D, 'get_root_id', return_value='audit-root'), \
         patch.object(D, 'search_files', side_effect=DriveError('Synthetic search error') if error else None,
                      return_value=hits or []) as search, \
         patch.object(D, 'list_folder', return_value=listing) as folders, \
         patch.object(D, 'get_folder_breadcrumb', return_value=[NS(id='audit-folder', name='Audit-Ordner')]), \
         patch.object(D, 'get_web_view_link_for_folder_id', return_value=None):
        response = client.get(url)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    result = dict(case=name, status=response.status_code, search_calls=search.call_count,
                  folder_calls=folders.call_count,
                  error_message='Suche konnte gerade nicht ausgeführt werden.' in html,
                  no_hits='Keine Treffer' in html,
                  no_root_folders='Keine Ordner unter der Drive-Wurzel.' in html,
                  query_preserved='value="Audit"' in html,
                  plain_folder_link='href="/docs/folder/audit-folder"' in html)
    results.append(result)
    return result

for scope, url in [('root', '/docs/?q=Audit'), ('folder', '/docs/folder/audit-folder?q=Audit')]:
    empty = request_case(scope + '_empty', url)
    assert empty['no_hits'] and not empty['error_message'] and empty['query_preserved']
    failed = request_case(scope + '_error', url, error=True)
    assert failed['no_hits'] and failed['error_message'] and failed['query_preserved']

short = request_case('root_short_query', '/docs/?q=A')
assert short['search_calls'] == short['folder_calls'] == 0 and short['no_root_folders']
hit = NS(name='Audit-Datei', icon_name='file', web_view_link=None,
         parent_id='audit-folder', breadcrumb=[NS(name='Audit-Ordner')])
linked = request_case('root_hit_folder_link', '/docs/?q=Audit', hits=[hit])
assert linked['plain_folder_link'] and not linked['no_hits']

def pagination_case(name, first_count):
    drive = MagicMock()
    outside = [dict(id=f'outside-{i}', name=f'Audit-{i}', parents=['elsewhere'],
                    mimeType='application/pdf') for i in range(first_count)]
    inside = dict(id='inside', name='Audit-Target', parents=['audit-folder'], mimeType='application/pdf')
    drive.files.return_value.list.return_value.execute.side_effect = [
        {'files':outside, 'nextPageToken':'next-page'}, {'files':[inside]}]
    with app.app_context(), patch.object(D, '_build_drive', return_value=drive), \
         patch.object(D, '_get_drive_id', return_value='audit-root'), \
         patch.object(D, 'get_folder_breadcrumb', side_effect=lambda parent: [NS(id=parent, name=parent)]):
        hits = D.search_files('Audit', scope_folder_id='audit-folder')
    result = dict(case=name, first_page_outside_scope=first_count,
                  api_pages=drive.files.return_value.list.call_count,
                  returned_ids=[h.drive_file_id for h in hits], second_page_contains_target=True)
    results.append(result)
    return result

truncated = pagination_case('scope_target_after_50_global_hits', 50)
assert truncated['api_pages'] == 1 and truncated['returned_ids'] == []
control = pagination_case('scope_target_after_49_global_hits', 49)
assert control['api_pages'] == 2 and control['returned_ids'] == ['inside']
output = dict(date='2026-09-21', results=results,
              limits='Eight isolated groups. Original routes/templates; search/listing stubbed for rendering. Original search service with synthetic paginated API for last two cases. No browser, real Drive, uploads or production data. SQLite memory; testing CSRF/rate limiting disabled.')
(OUT / 'DOCS_SEARCH_CHECKS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, ensure_ascii=True, indent=2))
