"""Original service calls with replaced transports; no credentials or network."""
from pathlib import Path
import runpy,json
OUT=Path(__file__).resolve().parent
runpy.run_path(str(OUT/'run_existing_tests.py'),run_name='audit_setup')
from unittest.mock import patch,Mock
from flask import Flask
import requests
from backend.services.places import PlacesService
from backend.services.mail import MailService
app=Flask('audit_contracts')
results=[]
with app.app_context():
    app.config['GOOGLE_MAPS_API_KEY']='synthetic-audit-marker'
    for name,method in [('autocomplete',PlacesService.autocomplete),('details',PlacesService.get_place_details)]:
        response=Mock(status_code=200)
        response.json.return_value={'status':'OK','predictions':[],'result':{}}
        with patch('backend.services.places.requests.get',return_value=response) as transport,patch.object(app.logger,'info') as logger:
            method('audit-input')
            record={'id':'INT-01' if name=='autocomplete' else 'INT-02','scenario':name,
                    'timeout_supplied':'timeout' in transport.call_args.kwargs,
                    'synthetic_key_in_info_log':any('synthetic-audit-marker' in str(c) for c in logger.call_args_list)}
            assert not record['timeout_supplied']
            results.append(record)
    with patch('backend.services.places.requests.get',side_effect=requests.Timeout('synthetic timeout')),patch.object(app.logger,'info'),patch.object(app.logger,'error'):
        value=PlacesService.autocomplete('audit-input')
        assert value==[]
        results.append({'id':'INT-03','scenario':'places_timeout','result':value})
    app.config.update(RESEND_API_KEY='',MAIL_SMTP_HOST=None)
    with patch('backend.services.mail.logger'):
        value=MailService.send('audit@example.test','Audit','Audit')
    assert value['success'] is True and value['message_id'] is None
    results.append({'id':'INT-04','scenario':'mail_missing_host','result':value})
    app.config.update(MAIL_SMTP_HOST='smtp.example.test',MAIL_SMTP_USERNAME='',MAIL_SMTP_PASSWORD='')
    with patch('backend.services.mail.logger'):
        value=MailService.send('audit@example.test','Audit','Audit')
    assert value['success'] is True and value['error'] is None
    results.append({'id':'INT-05','scenario':'mail_missing_credentials','result':value})
    app.config.update(RESEND_API_KEY='synthetic-unused',MAIL_HTTP_TIMEOUT_SECONDS=15)
    with patch('backend.services.mail.requests.post',side_effect=requests.Timeout('synthetic timeout')) as transport,patch('backend.services.mail.logger'):
        value=MailService.send('audit@example.test','Audit','Audit')
    assert value['success'] is False and transport.call_args.kwargs['timeout']==15
    results.append({'id':'INT-06','scenario':'resend_timeout','timeout':transport.call_args.kwargs['timeout'],'result':value})
(OUT/'INTEGRATION_CONTRACT_CHECKS.json').write_text(json.dumps({'method':'6 isolated original-service probes, mocked transports/logs, no real configuration/network/DB','results':results},indent=2),encoding='utf-8')
print('6 integration-contract probes verified')
