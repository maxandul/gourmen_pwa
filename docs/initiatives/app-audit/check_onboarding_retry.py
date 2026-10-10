"""Replay original member-creation POST after three different first outcomes."""
from pathlib import Path
import runpy
import json
OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT / 'check_onboarding_failures.py'), run_name='audit_helper')
results = []
for mode in ('success','mail_failure','first_audit_failure'):
    result = ns['probe'](mode, retry=True)
    assert result['retry']['response'] == {'exception':'IntegrityError'}
    assert result['retry']['mail_calls'] == 0 and result['retry']['matching_members'] == 1
    assert result['retry']['token_count'] == (0 if mode == 'first_audit_failure' else 1)
    results.append(result)
output = dict(date='2026-09-28',groups=3,results=results,
              limits='Two original POST requests per group, fresh request contexts, SQLite memory, all mail intercepted. No production accounts, real mail, browser or PostgreSQL test. Identical email only; normalization and concurrent requests not tested.')
(OUT / 'ONBOARDING_RETRY_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'groups':3,'results':[{'first_case':r['case'],'retry':r['retry']} for r in results]},indent=2))
