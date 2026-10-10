"""Original search and breadcrumb logic; synthetic API transport, no network."""
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import runpy

OUT = Path(__file__).resolve().parent
runpy.run_path(str(OUT / 'run_existing_tests.py'), run_name='audit_setup')
from backend.services.drive_storage import DriveStorageService as D
from googleapiclient.errors import HttpError
from httplib2 import Response

results = []
metadata = {
    'target': {'id':'target', 'name':'Target', 'parents':['root']},
    'deep': {'id':'deep', 'name':'Deep', 'parents':['target']},
    'sibling': {'id':'sibling', 'name':'Sibling', 'parents':['root']},
}
def item(uid, parent):
    return {'id':uid, 'name':uid + '.pdf', 'mimeType':'application/pdf',
            'parents':[parent] if parent else []}

def execute(name, pages, *, query='Audit', scope=None, meta_error=False):
    drive = MagicMock()
    drive.files.return_value.list.return_value.execute.side_effect = pages
    def get(**kwargs):
        call = MagicMock()
        if meta_error:
            call.execute.side_effect = HttpError(Response({'status':'403'}), b'{}')
        else:
            call.execute.return_value = metadata[kwargs['fileId']]
        return call
    drive.files.return_value.get.side_effect = get
    with patch.object(D, '_build_drive', return_value=drive), \
         patch.object(D, '_get_drive_id', return_value='root'):
        try:
            hits = D.search_files(query, scope_folder_id=scope)
            result = {'ids':[h.drive_file_id for h in hits],
                      'paths':[[s.id for s in h.breadcrumb] for h in hits]}
        except HttpError as exc:
            result = {'exception':type(exc).__name__, 'status':int(exc.resp.status)}
    result.update(case=name, list_calls=drive.files.return_value.list.call_count,
                  metadata_calls=drive.files.return_value.get.call_count,
                  queries=[c.kwargs['q'] for c in drive.files.return_value.list.call_args_list])
    results.append(result)
    return result

scope = execute('direct_nested_sibling_parentless_scope', [{'files':[
    item('direct','target'), item('nested','deep'), item('outside','sibling'), item('parentless',None)]}], scope='target')
assert scope['ids'] == ['direct','nested'] and scope['paths'] == [['target'],['target','deep']]

escaped = execute('apostrophe_backslash_unicode', [{'files':[]}], query="  Menü O'Brien\\2026  ")
assert escaped['queries'] == ["fullText contains 'Menü O\\'Brien\\\\2026' and trashed = false and mimeType != 'application/vnd.google-apps.folder'"]

empty = execute('empty_page_with_continuation', [{'files':[], 'nextPageToken':'next'},
                                              {'files':[item('found','target')]}], scope='target')
assert empty['ids'] == ['found'] and empty['list_calls'] == 2

page_error = execute('second_page_http_error', [{'files':[item('first','target')], 'nextPageToken':'next'},
                    HttpError(Response({'status':'403'}), b'{}')])
assert page_error['exception'] == 'HttpError' and page_error['list_calls'] == 2

path_error = execute('breadcrumb_http_error', [{'files':[item('first','target')]}], meta_error=True)
assert path_error['exception'] == 'HttpError' and path_error['metadata_calls'] == 1

repeated = execute('fifty_hits_same_two_level_parent', [{'files':[item(str(i),'deep') for i in range(50)]}])
assert len(repeated['ids']) == 50 and repeated['list_calls'] == 1 and repeated['metadata_calls'] == 100

output = {'date':'2026-09-21', 'groups':6, 'results':results,
          'limits':'Original search and breadcrumb methods, synthetic Google transport. No browser, route error response, real Google query validation or elapsed-time benchmark. 403 exceptions are preserved as observations; no actual account access.'}
(OUT / 'DOCS_SEARCH_BOUNDARY_CHECKS.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'groups':6, 'cases':[{k:v for k,v in r.items() if k not in ('ids','paths','queries')} for r in results]}, indent=2))
