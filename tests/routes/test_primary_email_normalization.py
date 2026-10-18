"""Primary email normalization with legacy spellings, conflict and login tests."""
from datetime import datetime
from unittest.mock import Mock
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from wtforms.validators import ValidationError
from backend.extensions import db
from backend.models.member import Member
from backend.services.primary_email import PrimaryEmailService as Emails
from backend.services.mail import MailService
from tests.conftest import auth_id

PASSWORD='Synthetic-normalization-password'


@pytest.fixture
def legacy_member(app):
    with app.app_context():
        member=Member(vorname='Legacy',nachname='Synthetic',email=' Legacy@Example.com ')
        member.set_password(PASSWORD);db.session.add(member);db.session.commit();return member.id


@pytest.mark.parametrize('email',['legacy@example.com','LEGACY@EXAMPLE.COM',' Legacy@example.com ','\tLegacy@example.com\n'])
def test_login_accepts_normalized_legacy_address(app,client,legacy_member,email):
    response=client.post('/auth/login',data={'email':email,'password':PASSWORD})
    assert response.status_code==302
    with client.session_transaction() as state:assert state['_user_id']==auth_id(client,legacy_member)
    with app.app_context():assert db.session.get(Member,legacy_member).email==' Legacy@Example.com '


def test_reset_uses_canonical_recipient(app,client,legacy_member,monkeypatch):
    send=Mock();monkeypatch.setattr(MailService,'send_async',send)
    assert client.post('/auth/forgot-password',data={'email':' LEGACY@example.com '}).status_code==302
    assert send.call_args.kwargs['to']=='legacy@example.com'


def test_profile_and_admin_reject_normalized_conflict(app,client,legacy_member):
    with app.app_context():
        other=Member(vorname='Other',nachname='Synthetic',email='other@example.com',passwort_hash='unused',password_changed_at=datetime(2026,1,1))
        db.session.add(other);db.session.commit();oid=other.id
    with client.session_transaction() as state:state['_user_id']=auth_id(client,oid);state['_fresh']=True
    response=client.post('/member/profile',data={'active_tab':'profile','profile-vorname':'Changed',
        'profile-nachname':'Synthetic','profile-email':' LEGACY@EXAMPLE.COM '})
    assert response.status_code==200 and 'bereits verwendet' in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(Member,oid).email=='other@example.com'
        from backend.routes.admin import MemberForm
        form=MemberForm(data={'email':' LEGACY@EXAMPLE.COM '})
        with pytest.raises(ValidationError):form.validate_email(form.email)
        assert form.email.data=='legacy@example.com'


def test_database_catches_race_and_ambiguous_legacy_lookup_fails_closed(app,legacy_member):
    with app.app_context():
        other=Member(vorname='Other',nachname='Synthetic',email='legacy@example.com',passwort_hash='unused')
        db.session.add(other)
        with pytest.raises(IntegrityError):db.session.flush()
        db.session.rollback()
        # Model a database before the new migration; never alter a real schema.
        db.session.execute(text('DROP INDEX uq_members_primary_email_normalized'))
        db.session.add(Member(vorname='Other',nachname='Synthetic',email='legacy@example.com',passwort_hash='unused'))
        db.session.commit()
        assert Emails.find_active('LEGACY@example.com') is None
