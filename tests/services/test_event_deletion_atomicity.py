"""A-046: future event deletion never commits participation loss separately."""
from datetime import datetime, timedelta, date
from unittest.mock import Mock
import pytest
from sqlalchemy import event as sa_event
from sqlalchemy.exc import OperationalError
from backend.extensions import db
from backend.models.event import Event
from backend.models.member import Member, Role
from backend.models.participation import Participation
from backend.models.rating import EventRating
from backend.models.document import Document
from backend.models.accounting import Booking, MemberClaim, ClaimType, Receipt, Account, AccountKind, FiscalYear, BookingDirection
from backend.models.audit_event import AuditEvent, AuditAction
from backend.services.event_deletion import EventDeletionService as Service, EventDeletionError
from tests.services.test_audit_failure_boundary import seed, failed_audit
from tests.conftest import auth_id


def unchanged(seed):
    assert db.session.get(Event,seed[1]) is not None
    assert Participation.query.filter_by(event_id=seed[1]).count()==1
    assert AuditEvent.query.filter_by(action=AuditAction.EVENT_DELETE).count()==0


@pytest.mark.parametrize('failure',['audit','event_flush','commit'])
def test_actual_delete_failure_preserves_event_and_participation(app,seed,monkeypatch,failure):
    with app.app_context():
        def fail(*args):raise OperationalError('synthetic delete',{},Exception('synthetic'))
        with monkeypatch.context() as patch:
            if failure=='commit':patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            target=AuditEvent if failure=='audit' else Event
            action='before_insert' if failure=='audit' else 'before_delete'
            if failure!='commit':sa_event.listen(target,action,fail)
            try:
                with pytest.raises(EventDeletionError):Service.delete(seed[1],db.session.get(Member,seed[0]))
            finally:
                if failure!='commit':sa_event.remove(target,action,fail)
        unchanged(seed)
        db.session.remove();unchanged(seed)


@pytest.mark.parametrize('relation',['rating','document','receipt','claim','booking','billbro','ggl'])
def test_referenced_history_is_not_deleted_or_detached(app,seed,relation):
    with app.app_context():
        if relation=='rating':db.session.add(EventRating(event_id=seed[1],participant_id=seed[0],food_rating=3,drinks_rating=4,service_rating=5))
        if relation=='document':db.session.add(Document(event_id=seed[1],drive_file_id='synthetic',drive_parent_id='synthetic'))
        if relation=='receipt':db.session.add(Receipt(suggested_event_id=seed[1],drive_file_id='synthetic',drive_file_name='synthetic.pdf',drive_folder_id='synthetic',uploader_id=seed[0]))
        if relation=='claim':db.session.add(MemberClaim(event_id=seed[1],member_id=seed[0],claim_type=ClaimType.ESSENSANTEIL,expected_rappen=1000))
        if relation=='booking':
            fy=FiscalYear(year=2026,start_date=date(2026,1,1),end_date=date(2026,12,31));account=Account(code='3620',name='Synthetic',kind=AccountKind.INCOME)
            db.session.add_all([fy,account]);db.session.flush()
            db.session.add(Booking(event_id=seed[1],fiscal_year_id=fy.id,account_id=account.id,booking_date=date(2026,1,1),description='Synthetic',amount_rappen=1000,direction=BookingDirection.IN,created_by=seed[0]))
        if relation=='billbro':db.session.get(Event,seed[1]).rechnungsbetrag_rappen=0
        if relation=='ggl':Participation.query.one().guess_bill_amount_rappen=1000
        db.session.commit()
        with pytest.raises(EventDeletionError,match='bleibt erhalten'):Service.delete(seed[1],db.session.get(Member,seed[0]))
        unchanged(seed)


@pytest.mark.parametrize('guard',['role','past'])
def test_original_role_and_date_guards(app,seed,guard):
    with app.app_context():
        if guard=='role':db.session.get(Member,seed[0]).role=Role.MEMBER
        else:db.session.get(Event,seed[1]).datum=datetime.now()-timedelta(days=2)
        db.session.commit()
        with pytest.raises(EventDeletionError):Service.delete(seed[1],db.session.get(Member,seed[0]))
        unchanged(seed)


def test_original_route_success_has_one_atomic_audit(app,client,seed):
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    page=client.post(f'/events/{seed[1]}/delete');assert page.status_code==302
    with app.app_context():
        assert db.session.get(Event,seed[1]) is None and Participation.query.count()==0
        row=AuditEvent.query.one();assert row.action==AuditAction.EVENT_DELETE and row.entity_id==seed[1]
        assert row.extra_json['participation_count']==1


def test_original_route_audit_failure_does_not_claim_success(app,client,seed):
    with client.session_transaction() as state:state['_user_id']=auth_id(client,seed[0]);state['_fresh']=True
    with failed_audit():page=client.post(f'/events/{seed[1]}/delete')
    assert page.status_code==302 and f'/events/{seed[1]}' in page.location
    with client.session_transaction() as state:assert any('nicht gelöscht' in message for category,message in state.get('_flashes',[]))
    with app.app_context():unchanged(seed)
