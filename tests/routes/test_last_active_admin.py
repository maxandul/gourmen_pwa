"""A-090: member edits must preserve an active administrator."""
from unittest.mock import Mock

import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.services.security import SecurityService


@pytest.fixture
def admin_case(app, client, monkeypatch):
    audit = Mock()
    monkeypatch.setattr(SecurityService, 'log_audit_event', audit)
    with app.app_context():
        rows = [Member(vorname='Original', nachname='Test', email=f'admin{i}@example.com',
                       passwort_hash='unused', role=Role.ADMIN if i == 0 else Role.MEMBER)
                for i in range(2)]
        db.session.add_all(rows)
        db.session.commit()
        ids = [row.id for row in rows]
    with client.session_transaction() as state:
        state['_user_id'] = str(ids[0])
        state['_fresh'] = True
    return ids, audit


def payload(role='ADMIN', active=True, index=0):
    data = {'vorname': 'Edited', 'nachname': 'Test', 'email': f'admin{index}@example.com',
            'role': role, 'funktion': 'MEMBER', 'beitritt': '2020-01-01'}
    if active:
        data['is_active'] = 'y'
    return data


@pytest.mark.parametrize('role,active', [('MEMBER', True), ('ADMIN', False), ('MEMBER', False)])
@pytest.mark.parametrize('other', ['member', 'inactive_admin'])
def test_last_admin_rejected_without_partial_changes(app, client, admin_case, role, active, other):
    ids, audit = admin_case
    if other == 'inactive_admin':
        with app.app_context():
            row = db.session.get(Member, ids[1])
            row.role, row.is_active = Role.ADMIN, False
            db.session.commit()
    for _ in range(2):
        response = client.post(f'/admin/members/{ids[0]}/edit', data=payload(role, active))
        assert response.status_code == 200
        assert 'Mindestens ein aktiver Admin muss erhalten bleiben.' in response.get_data(as_text=True)
        assert b'value="Edited"' in response.data
    with app.app_context():
        row = db.session.get(Member, ids[0])
        assert (row.vorname, row.role, row.is_active) == ('Original', Role.ADMIN, True)
    audit.assert_not_called()


@pytest.mark.parametrize('role,active', [('MEMBER', True), ('ADMIN', False), ('MEMBER', False)])
def test_other_active_admin_allows_change(app, client, admin_case, role, active):
    ids, audit = admin_case
    with app.app_context():
        db.session.get(Member, ids[1]).role = Role.ADMIN
        db.session.commit()
    response = client.post(f'/admin/members/{ids[0]}/edit', data=payload(role, active))
    assert response.status_code == 302
    with app.app_context():
        row = db.session.get(Member, ids[0])
        assert (row.vorname, row.role, row.is_active) == ('Edited', Role(role), active)
        assert Member.query.filter_by(role=Role.ADMIN, is_active=True).count() == 1
    audit.assert_called_once()


def test_last_admin_can_edit_ordinary_data(app, client, admin_case):
    ids, audit = admin_case
    assert client.post(f'/admin/members/{ids[0]}/edit', data=payload()).status_code == 302
    with app.app_context():
        row = db.session.get(Member, ids[0])
        assert (row.vorname, row.role, row.is_active) == ('Edited', Role.ADMIN, True)
    audit.assert_called_once()


def test_regular_member_can_be_deactivated(app, client, admin_case):
    ids, audit = admin_case
    assert client.post(f'/admin/members/{ids[1]}/edit', data=payload('MEMBER', False, 1)).status_code == 302
    with app.app_context():
        assert not db.session.get(Member, ids[1]).is_active
        assert Member.query.filter_by(role=Role.ADMIN, is_active=True).count() == 1


def test_promote_then_handover_preserves_admin(app, client, admin_case):
    ids, audit = admin_case
    assert client.post(f'/admin/members/{ids[1]}/edit', data=payload(index=1)).status_code == 302
    assert client.post(f'/admin/members/{ids[0]}/edit', data=payload('MEMBER')).status_code == 302
    with app.app_context():
        assert db.session.get(Member, ids[1]).is_admin()
        assert not db.session.get(Member, ids[0]).is_admin()


@pytest.mark.parametrize('change', ['peer_demotion', 'actor_demotion', 'actor_deactivation'])
def test_intervening_change_is_rechecked(app, client, admin_case, monkeypatch, change):
    from backend.routes.admin import MemberForm
    ids, audit = admin_case
    with app.app_context():
        db.session.get(Member, ids[1]).role = Role.ADMIN
        db.session.commit()
    original = MemberForm.validate_on_submit
    def validate_then_change(form):
        valid = original(form)
        target = ids[1] if change == 'peer_demotion' else ids[0]
        values = {'is_active': False} if change == 'actor_deactivation' else {'role': Role.MEMBER}
        db.session.execute(Member.__table__.update().where(Member.id == target).values(**values))
        db.session.commit()
        return valid
    monkeypatch.setattr(MemberForm, 'validate_on_submit', validate_then_change)
    response = client.post(f'/admin/members/{ids[0]}/edit', data=payload('MEMBER'))
    assert response.status_code == (200 if change == 'peer_demotion' else 403)
    with app.app_context():
        assert db.session.get(Member, ids[0]).vorname == 'Original'
        assert Member.query.filter_by(role=Role.ADMIN, is_active=True).count() == 1
    audit.assert_not_called()


def test_csrf_rejects_member_edit(app, client, admin_case):
    ids, audit = admin_case
    app.config['WTF_CSRF_ENABLED'] = True
    assert client.post(f'/admin/members/{ids[0]}/edit', data=payload('MEMBER')).status_code == 400
    with app.app_context():
        assert db.session.get(Member, ids[0]).is_admin()
    audit.assert_not_called()


def test_non_admin_cannot_edit(app, client, admin_case):
    ids, audit = admin_case
    with client.session_transaction() as state:
        state['_user_id'] = str(ids[1])
    assert client.post(f'/admin/members/{ids[0]}/edit', data=payload('MEMBER')).status_code == 403
    with app.app_context():
        assert db.session.get(Member, ids[0]).is_admin()
    audit.assert_not_called()
