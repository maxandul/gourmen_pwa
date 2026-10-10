"""Original reset requests and administrator password reset, with mail intercepted."""
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from datetime import datetime, timezone
import json
import logging
import re
import runpy

OUT = Path(__file__).resolve().parent
ns = runpy.run_path(str(OUT / 'check_onboarding_failures.py'), run_name='audit_helper')
app, db, Member, Role = (ns[key] for key in ('app', 'db', 'Member', 'Role'))
from backend.models.auth_token import AuthToken
from backend.routes.auth import MailService
logging.disable(logging.CRITICAL)
INITIAL = 'Synthetic-Initial-Password-471!'
CHANGED = 'Synthetic-Changed-Password-582!'
FINAL = 'Synthetic-Final-Password-693!'


def set_password(path, password):
    response = app.test_client().post(path, data=dict(new_password=password, confirm_password=password))
    assert response.status_code == 302 and response.location == '/auth/login'
    with app.app_context():
        assert db.session.get(Member, 2).check_password(password)


def probe(mode):
    with app.app_context():
        db.create_all()
        for uid, role in ((1, Role.ADMIN), (2, Role.MEMBER)):
            member = Member(id=uid, vorname='Audit', nachname='Resetfolge',
                            email=f'reset-sequence-{uid}@example.com', role=role, is_active=True)
            member.set_password(INITIAL)
            db.session.add(member)
        db.session.commit()
    paths = []
    def capture(**kwargs):
        paths.append(urlsplit(re.search(r'https?://\S+', kwargs['text']).group(0)).path)
    with patch.object(MailService, 'send_async', side_effect=capture):
        for _ in range(2 if mode == 'two_requests' else 1):
            response = app.test_client().post('/auth/forgot-password', data={'email':'reset-sequence-2@example.com'})
            assert response.status_code == 302
    with app.app_context():
        assert AuthToken.query.count() == len(paths)
    if mode == 'two_requests':
        assert len(paths) == 2 and paths[0] != paths[1]
        set_password(paths[1], CHANGED)
        admin_step_up = None
    else:
        admin = app.test_client()
        login = admin.post('/auth/login', data={'email':'reset-sequence-1@example.com', 'password':INITIAL})
        assert login.status_code == 302
        with admin.session_transaction() as session:
            assert session.get('_user_id') == '1'
        step = admin.post('/auth/step-up', data={'password':INITIAL,'next':'/admin/members/2/reset-password'})
        assert step.status_code == 302
        response = admin.post('/admin/members/2/reset-password', data={'confirm':'RESET'})
        assert response.status_code == 302 and response.location == '/admin/temp-password'
        with admin.session_transaction() as session:
            temporary = session['temp_password']['password']
        with app.app_context():
            assert db.session.get(Member, 2).check_password(temporary)
        admin_step_up = True
    with app.app_context():
        outstanding = AuthToken.query.filter_by(used_at=None).count()
    assert outstanding == 1
    set_password(paths[0], FINAL)
    with app.app_context():
        assert AuthToken.query.filter_by(used_at=None).count() == 0
        member = db.session.get(Member, 2)
        previous_rejected = not member.check_password(CHANGED if mode == 'two_requests' else temporary)
        assert previous_rejected
        db.session.remove()
        db.drop_all()
    return dict(case=mode, intercepted_mail_requests=len(paths),
                original_admin_login_and_step_up=admin_step_up,
                outstanding_old_links_after_password_change=outstanding,
                old_link_overwrites_password=True, previous_password_rejected=previous_rejected)


results = [probe(mode) for mode in ('two_requests', 'admin_reset')]
output = dict(date=datetime.now(timezone.utc).date().isoformat(), groups=len(results), results=results,
              limits='Original forgot-password requests, reset routes and admin login/step-up/reset. Only send_async intercepted. SQLite memory, synthetic members/passwords; no mail, network, browser, MFA, production or concurrency. Testing CSRF/rate limits disabled. No token, cookie or password values reported.')
(OUT / 'RESET_REQUEST_SEQUENCE_CHECKS.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
print(json.dumps(output, indent=2))
