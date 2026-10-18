"""A-137: genuine failed ORM audit flush leaves the caller transaction usable."""
from datetime import datetime, timedelta
from contextlib import contextmanager
from unittest.mock import Mock
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError, IntegrityError
from backend.extensions import db
from backend.models.audit_event import AuditEvent, AuditAction
from backend.models.member import Member, Role
from backend.models.event import Event, EventType
from backend.models.participation import Participation
from backend.services.security import SecurityService
from tests.conftest import auth_id


@pytest.fixture
def seed(app):
    with app.app_context():
        member=Member(vorname='Synthetic',nachname='Original',email='audit-boundary@example.com',role=Role.ADMIN)
        member.set_password('SyntheticAuditBoundary-472!')
        db.session.add(member);db.session.flush()
        ev=Event(organisator_id=member.id,datum=datetime.now()+timedelta(days=10),event_typ=EventType.MONATSESSEN,season=2026,restaurant='Synthetic',published=True)
        db.session.add(ev);db.session.flush()
        db.session.add(Participation(member_id=member.id,event_id=ev.id,teilnahme=False));db.session.commit()
        return member.id,ev.id


@contextmanager
def failed_audit():
    def fail(*args):raise OperationalError('synthetic',{},Exception('SYNTHETIC-PRIVATE-MARKER'))
    sa_event.listen(AuditEvent,'before_insert',fail)
    try:yield
    finally:sa_event.remove(AuditEvent,'before_insert',fail)


@pytest.mark.parametrize('pending',[False,True])
def test_failed_insert_preserves_business_and_usable_session(app,seed,caplog,pending):
    with app.test_request_context('/synthetic'):
        member=db.session.get(Member,seed[0])
        if pending:member.nachname='Pending'
        with failed_audit():
            assert SecurityService.log_audit_event(AuditAction.LOGIN,'member',member.id,actor_id=member.id) is False
        assert AuditEvent.query.count()==0 and member.nachname==('Pending' if pending else 'Original')
        assert 'audit entry not recorded' in caplog.text and 'SYNTHETIC-PRIVATE-MARKER' not in caplog.text
        db.session.rollback()
        assert member.nachname=='Original'
        assert SecurityService.log_audit_event(AuditAction.LOGIN,'member',member.id,actor_id=member.id) is True
        assert AuditEvent.query.count()==1


def test_success_preserves_legacy_commit_boundary(app,seed):
    with app.test_request_context('/synthetic'):
        member=db.session.get(Member,seed[0]);member.nachname='Committed'
        assert SecurityService.log_audit_event(AuditAction.LOGIN,'member',member.id,actor_id=member.id)
        db.session.rollback()
        assert member.nachname=='Committed' and AuditEvent.query.count()==1


def test_business_flush_failure_is_not_swallowed(app,seed):
    with app.test_request_context('/synthetic'):
        member=db.session.get(Member,seed[0]);member.nachname=None
        with pytest.raises(IntegrityError):SecurityService.log_audit_event(AuditAction.LOGIN,'member',seed[0],actor_id=seed[0])
        db.session.rollback()
        assert member.nachname=='Original' and AuditEvent.query.count()==0


def test_outer_commit_error_is_propagated_and_session_recovered(app,seed,monkeypatch):
    with app.test_request_context('/synthetic'):
        member=db.session.get(Member,seed[0]);member.nachname='Pending'
        with monkeypatch.context() as patch:
            patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic commit')))
            with pytest.raises(RuntimeError,match='synthetic commit'):
                SecurityService.log_audit_event(AuditAction.LOGIN,'member',seed[0],actor_id=seed[0])
        assert member.nachname=='Original' and AuditEvent.query.count()==0


@pytest.mark.parametrize('flow',['login','rsvp','calendar','delete'])
def test_original_routes_survive_missing_optional_audit(app,client,seed,flow):
    if flow!='login':
        with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    url={'login':'/auth/login','rsvp':f'/events/{seed[1]}/rsvp','calendar':'/member/settings/calendar/enable','delete':f'/events/{seed[1]}/delete'}[flow]
    data={'email':'audit-boundary@example.com','password':'SyntheticAuditBoundary-472!'} if flow=='login' else {}
    with failed_audit():response=client.post(url,data=data)
    assert response.status_code==(201 if flow=='calendar' else 302)
    with app.app_context():
        assert AuditEvent.query.count()==0
        if flow=='rsvp':assert Participation.query.one().teilnahme
        if flow=='calendar':assert db.session.get(Member,seed[0]).ical_token
        if flow=='delete':assert db.session.get(Event,seed[1]) is None and Participation.query.count()==0
    if flow=='login':
        with client.session_transaction() as state:assert state.get('_user_id')


from tests.routes.test_member_creation_confirmation import creation
from tests.routes.test_onboarding_delivery import invited, raw_from_mail


def test_activation_keeps_password_token_and_login_after_optional_audit_failure(app,client,creation):
    from backend.models.auth_token import AuthToken
    uid=invited(app,client,creation);raw=raw_from_mail(creation[1]);anonymous=app.test_client()
    with failed_audit():
        response=anonymous.post('/auth/activate/'+raw,data={'new_password':'Synthetic-New-password-234!','confirm_password':'Synthetic-New-password-234!'})
    assert response.status_code==302
    with anonymous.session_transaction() as state:assert state.get('_user_id')
    with app.app_context():
        assert db.session.get(Member,uid).check_password('Synthetic-New-password-234!')
        assert AuthToken.query.filter_by(member_id=uid).one().used_at is not None
