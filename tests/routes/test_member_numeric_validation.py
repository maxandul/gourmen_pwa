"""A-085: identical numeric meanings in profile, admin edit and member creation."""

from datetime import datetime
from unittest.mock import Mock

from tests.conftest import auth_id
import pytest

from backend.extensions import db
from backend.models.member import Member, Role
from backend.services.mail import MailService


@pytest.fixture
def numeric_case(app, client, monkeypatch):
    mail = Mock(return_value={'success': True})
    monkeypatch.setattr(MailService, 'send', mail)
    with app.app_context():
        user = Member(funktion='MEMBER', password_changed_at=datetime(2026, 1, 1),
                      vorname='Original', nachname='Test', email='numeric@example.com',
                      passwort_hash='unused', role=Role.ADMIN,
                      koerpergroesse=180, koerpergewicht=80, schuhgroesse=42.5)
        db.session.add(user)
        db.session.commit()
        uid = user.id
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, uid)
        state['_fresh'] = True
    return uid, mail


@pytest.mark.parametrize('entry', ['profile', 'edit', 'create'])
@pytest.mark.parametrize('values,expected', [
    (('-5', '80', '42'), None), (('180', '-2', '42'), None),
    (('180', '80', '-1'), None), (('abc', '80', '42'), None),
    (('180', 'abc', '42'), None), (('180', '80', 'abc'), None),
    (('180.5', '80', '42'), None), (('180', '80.5', '42'), None),
    (('180', '80', 'nan'), None), (('180', '80', 'inf'), None),
    (('2147483648', '80', '42'), None),
    (('', '', ''), (None, None, None)), ((' ', ' ', ' '), (None, None, None)),
    (('0', '0', '0'), (0, 0, 0)), (('185', '85', '43.5'), (185, 85, 43.5)),
])
def test_numeric_values(app, client, numeric_case, entry, values, expected):
    uid, mail = numeric_case
    prefix = 'profile-' if entry == 'profile' else ''
    email = 'new@example.com' if entry == 'create' else 'numeric@example.com'
    data = {prefix + key: value for key, value in {
        'vorname': 'Edited', 'nachname': 'Test', 'email': email,
        'geburtsdatum': '1990-01-01', 'beitritt': '2020-01-01',
        'funktion': 'MEMBER', 'role': 'ADMIN', 'is_active': 'y',
        'password': 'Synthetic-password-123',
        'koerpergroesse': values[0], 'koerpergewicht': values[1], 'schuhgroesse': values[2],
    }.items()}
    path = {'profile': '/member/profile', 'edit': f'/admin/members/{uid}/edit',
            'create': '/admin/members/new'}[entry]
    response = client.post(path, data=data)
    assert response.status_code == (200 if expected is None else 302)
    with app.app_context():
        if expected is None:
            assert Member.query.count() == 1
            row = db.session.get(Member, uid)
            assert (row.vorname, row.koerpergroesse, row.koerpergewicht,
                    row.schuhgroesse) == ('Original', 180, 80, 42.5)
            assert b'value="Edited"' in response.data
            mail.assert_not_called()
        else:
            row = Member.query.filter_by(email=email).one()
            assert (row.koerpergroesse, row.koerpergewicht, row.schuhgroesse) == expected
            assert row.vorname == 'Edited'
