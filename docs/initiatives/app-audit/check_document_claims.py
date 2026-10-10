"""Local code checks for dated Hamburg/SEO documentation; no live-site claims."""
from pathlib import Path
import runpy,json
from datetime import datetime
import xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from backend.app import create_app
from backend.routes.events import hamburg2026_is_visible
results=[]
for stamp,expected in [(datetime(2026,6,1,5,59,59),True),(datetime(2026,6,1,6),False)]:
    value=hamburg2026_is_visible(stamp);assert value is expected
    results.append({'scenario':'hamburg_cutoff','time':stamp.isoformat(),'visible':value})
app=create_app('testing');client=app.test_client()
response=client.get('/restaurants?sort=rating',base_url='https://gourmen.ch')
assert response.status_code==301 and response.location=='https://www.gourmen.ch/restaurants?sort=rating'
results.append({'scenario':'local_apex_redirect','http':response.status_code,'location':response.location})
response=client.get('/robots.txt',base_url='https://www.gourmen.ch')
body=response.get_data(as_text=True)
assert response.status_code==200 and 'Disallow: /member/' in body and 'Sitemap:' in body
results.append({'scenario':'robots','http':response.status_code,'private_member_disallow':True})
response=client.get('/sitemap.xml',base_url='https://www.gourmen.ch')
locations=[e.text for e in ET.fromstring(response.data).findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert response.status_code==200 and len(locations)==3
results.append({'scenario':'sitemap','http':response.status_code,'locations':locations})
(OUT/'DOCUMENT_CLAIM_CHECKS.json').write_text(json.dumps({'method':'5 local helper/HTTP probes; no live DNS, search engine, network or real DB','results':results},indent=2),encoding='utf-8')
print('5 local documentation claims verified')
