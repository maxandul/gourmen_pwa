"""Synthetic version/role/history and original-route regression."""
from unittest.mock import Mock
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from backend.extensions import db
from backend.models.accounting import Booking, FiscalYear, FiscalYearStatus, RevisionApproval, RevisionComment
from backend.models.accounting_revision import AccountingRevision
from backend.models.member import Member, Role, Funktion
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.accounting_revision import AccountingRevisionService as Service
from tests.routes.test_booking_values import setup, create
from tests.services.test_accounting_year_guards import csrf
from tests.conftest import auth_id


def actor(setup):
    return db.session.get(Member, setup[0])


def role(setup, function, admin=False):
    member = actor(setup)
    member.role = Role.ADMIN if admin else Role.MEMBER
    member.funktion = getattr(Funktion, function)
    db.session.commit()
    return member


def test_retained_versions_approval_and_delayed_report(app, setup):
    with app.app_context():
        booking = create(setup)
        fy = Service.submit(setup[1], actor(setup), expected_version=0)
        first = AccountingRevision.query.one()
        assert first.snapshot['bookings'][0]['amount_rappen'] == 1999
        Service.approve(fy.id, actor(setup), expected_version=1)
        assert first.admin_substitute and fy.revision_approval.id == first.id
        Service.withdraw(fy.id, actor(setup), expected_version=1, reason='Synthetic correction', closed=True)
        assert fy.is_open and fy.revision_approval is None
        AccountingService.update_booking(booking.id, amount_rappen=2001)
        Service.submit(fy.id, actor(setup), expected_version=1)
        assert first.snapshot['bookings'][0]['amount_rappen'] == 1999
        assert first.approved_at and first.withdrawn_at and first.withdrawal_reason == 'Synthetic correction'
        assert AccountingRevision.query.filter_by(version=2).one().snapshot['bookings'][0]['amount_rappen'] == 2001
        Service.set_report(fy.id, 'synthetic-old-report', expected_version=1)
        assert first.report_drive_id == 'synthetic-old-report'
        assert AccountingRevision.query.filter_by(version=2).one().report_drive_id is None
        with pytest.raises(AccountingValidationError):
            Service.approve(fy.id, actor(setup), expected_version=1)
        Service.approve(fy.id, actor(setup), expected_version=2)
        assert fy.revision_approval.version == 2 and AccountingRevision.query.count() == 2


@pytest.mark.parametrize('function,admin,allowed', [
    ('MEMBER',False,False),('SCHATZMEISTER',False,False),
    ('RECHNUNGSPRUEFER',False,True),('SCHATZMEISTER',True,True)])
def test_approval_roles(app,setup,function,admin,allowed):
    with app.app_context():
        Service.submit(setup[1], actor(setup), expected_version=0)
        member = role(setup,function,admin)
        if allowed:
            Service.approve(setup[1], member, expected_version=1)
            assert AccountingRevision.query.one().admin_substitute == admin
        else:
            with pytest.raises(AccountingValidationError):
                Service.approve(setup[1], member, expected_version=1)
            assert db.session.get(FiscalYear,setup[1]).is_in_review


@pytest.mark.parametrize('function,allowed', [('MEMBER',False),('RECHNUNGSPRUEFER',False),('SCHATZMEISTER',True)])
def test_withdraw_roles_and_required_reason(app,setup,function,allowed):
    with app.app_context():
        Service.submit(setup[1],actor(setup),expected_version=0)
        member=role(setup,function)
        with pytest.raises(AccountingValidationError):
            Service.withdraw(setup[1],member,expected_version=1,reason=' ')
        if allowed:
            Service.withdraw(setup[1],member,expected_version=1,reason='Synthetic correction')
            assert db.session.get(FiscalYear,setup[1]).is_open
        else:
            with pytest.raises(AccountingValidationError):
                Service.withdraw(setup[1],member,expected_version=1,reason='Synthetic correction')


def test_objections_survive_resubmission_and_resolution_has_actor_time(app,setup):
    with app.app_context():
        Service.submit(setup[1],actor(setup),expected_version=0)
        comment=Service.comment(setup[1],actor(setup),'Synthetic objection',expected_version=1,blocking=True)
        with pytest.raises(AccountingValidationError,match='Beanstandungen'):
            Service.approve(setup[1],actor(setup),expected_version=1)
        Service.withdraw(setup[1],actor(setup),expected_version=1,reason='Fix')
        Service.submit(setup[1],actor(setup),expected_version=1)
        with pytest.raises(AccountingValidationError,match='Beanstandungen'):
            Service.approve(setup[1],actor(setup),expected_version=2)
        with pytest.raises(AccountingValidationError):
            Service.resolve(comment.id,actor(setup),expected_version=1)
        Service.resolve(comment.id,actor(setup),expected_version=2)
        assert comment.revision.version==1 and comment.resolved_by==setup[0] and comment.resolved_at
        Service.comment(setup[1],actor(setup),'Nonblocking hint',expected_version=2)
        Service.approve(setup[1],actor(setup),expected_version=2)
        with pytest.raises(AccountingValidationError):
            Service.comment(setup[1],actor(setup),'Late mutation',expected_version=2)


def test_legacy_approval_is_not_deleted_or_given_invented_snapshot(app,setup):
    with app.app_context():
        fy=db.session.get(FiscalYear,setup[1]);fy.status=FiscalYearStatus.CLOSED
        old=RevisionApproval(fiscal_year_id=fy.id,reviewer_id=setup[0],report_drive_id='synthetic-legacy')
        db.session.add(old);db.session.commit()
        assert fy.revision_approval==old
        Service.withdraw(fy.id,actor(setup),expected_version=0,reason='Legacy correction',closed=True)
        assert RevisionApproval.query.one().report_drive_id=='synthetic-legacy'
        assert AccountingRevision.query.one().snapshot is None
        assert fy.revision_approval is None
        Service.submit(fy.id,actor(setup),expected_version=1)
        Service.approve(fy.id,actor(setup),expected_version=2)
        assert RevisionApproval.query.count()==1 and fy.revision_approval.version==2


def test_legacy_review_requires_new_submission(app,setup):
    with app.app_context():
        fy=db.session.get(FiscalYear,setup[1]);fy.status=FiscalYearStatus.IN_REVIEW;db.session.commit()
        with pytest.raises(AccountingValidationError,match='Altstand'):
            Service.approve(fy.id,actor(setup),expected_version=0)
        Service.withdraw(fy.id,actor(setup),expected_version=0,reason='New snapshot')
        Service.submit(fy.id,actor(setup),expected_version=1)
        Service.approve(fy.id,actor(setup),expected_version=2)


@pytest.mark.parametrize('operation',['submit','approve','withdraw','comment'])
def test_commit_failure_rolls_back_all_changes(app,setup,monkeypatch,operation):
    with app.app_context():
        if operation!='submit':Service.submit(setup[1],actor(setup),expected_version=0)
        member=actor(setup)
        with monkeypatch.context() as patch:
            patch.setattr(db.session,'commit',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError,match='nicht bestätigt'):
                if operation=='submit':Service.submit(setup[1],member,expected_version=0)
                if operation=='approve':Service.approve(setup[1],member,expected_version=1)
                if operation=='withdraw':Service.withdraw(setup[1],member,expected_version=1,reason='Synthetic')
                if operation=='comment':Service.comment(setup[1],member,'Synthetic',expected_version=1)
        fy=db.session.get(FiscalYear,setup[1])
        assert fy.review_version==(0 if operation=='submit' else 1)
        assert fy.status==(FiscalYearStatus.OPEN if operation=='submit' else FiscalYearStatus.IN_REVIEW)
        assert RevisionComment.query.count()==0
        if operation!='submit':
            row=AccountingRevision.query.one();assert row.approved_at is None and row.withdrawn_at is None


def test_original_forms_stale_replay_and_admin_marker(app,client,setup,monkeypatch):
    from backend.routes.accounting import NotifierService, AccountingPdfService, DriveStorageService
    monkeypatch.setattr(NotifierService,'send_push_notification',Mock(return_value=False))
    monkeypatch.setattr(AccountingPdfService,'generate_report',Mock(return_value=b'synthetic'))
    monkeypatch.setattr(AccountingService,'get_receipt_folder_id',Mock(return_value='synthetic'))
    monkeypatch.setattr(DriveStorageService,'upload_bytes',Mock(return_value={'id':'synthetic-report'}))
    token=csrf(client,app);url=f'/accounting/year/{setup[1]}'
    assert client.post(url+'/submit',data={'csrf_token':token,'review_version':0}).status_code==302
    page=client.get(f'/accounting/?year={setup[1]}&tab=abschluss')
    assert 'Stellvertretend als Systemadmin bestätigen' in page.text
    assert 'name="reason"' in page.text and 'name="review_version" value="1"' in page.text
    client.post(url+'/approve',data={'csrf_token':token,'review_version':0})
    assert not AccountingPdfService.generate_report.called
    client.post(url+'/approve',data={'csrf_token':token,'review_version':1})
    assert AccountingPdfService.generate_report.call_count==1
    client.post(url+'/approve',data={'csrf_token':token,'review_version':1})
    assert AccountingPdfService.generate_report.call_count==1
    client.post(url+'/revoke',data={'csrf_token':token,'review_version':1})
    with app.app_context():assert db.session.get(FiscalYear,setup[1]).is_closed
    client.post(url+'/revoke',data={'csrf_token':token,'review_version':1,'reason':'Synthetic reason'})
    history=client.get(url+'/revisions')
    assert history.status_code==200 and 'Synthetic reason' in history.text and 'synthetic-report' in history.text
    with app.app_context():assert db.session.get(FiscalYear,setup[1]).is_open
    assert client.post(url+'/submit',data={'review_version':1}).status_code in (400,403)


@pytest.mark.parametrize('function,action,status,allowed', [
    ('SCHATZMEISTER','revoke','CLOSED',True),
    ('RECHNUNGSPRUEFER','revoke','CLOSED',False),
    ('SCHATZMEISTER','approve','IN_REVIEW',False),
    ('MEMBER','withdraw','IN_REVIEW',False)])
def test_original_route_roles(app,client,setup,function,action,status,allowed):
    with app.app_context():
        Service.submit(setup[1],actor(setup),expected_version=0)
        if status=='CLOSED':Service.approve(setup[1],actor(setup),expected_version=1)
        role(setup,function)
    with client.session_transaction() as state:state['_user_id']=auth_id(client,setup[0])
    response=client.post(f'/accounting/year/{setup[1]}/{action}',data={
        'csrf_token':csrf(client,app),'review_version':1,'reason':'Synthetic reason'})
    assert response.status_code==(302 if allowed else 403)
    with app.app_context():
        fy=db.session.get(FiscalYear,setup[1])
        assert fy.status==(FiscalYearStatus.OPEN if allowed else getattr(FiscalYearStatus,status))


def test_cross_year_comment_and_unprivileged_objection_rejected(app,setup):
    from datetime import date
    with app.app_context():
        booking=create(setup)
        other=FiscalYear(year=2027,start_date=date(2027,1,1),end_date=date(2027,12,31))
        db.session.add(other);db.session.commit()
        with pytest.raises(AccountingValidationError,match='diesem Jahr'):
            Service.comment(other.id,actor(setup),'Wrong year',expected_version=0,booking_id=booking.id)
        Service.submit(setup[1],actor(setup),expected_version=0)
        member=role(setup,'SCHATZMEISTER')
        with pytest.raises(AccountingValidationError):
            Service.comment(setup[1],member,'Unprivileged objection',expected_version=1,blocking=True)
        assert RevisionComment.query.count()==0


def test_migration_cycle_preserves_old_rows_and_refuses_history_loss():
    path=Path('migrations/versions/u204b20261018_accounting_revisions.py')
    spec=importlib.util.spec_from_file_location('review_migration',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as conn:
        for sql in ['CREATE TABLE members (id INTEGER PRIMARY KEY)',
                    'CREATE TABLE fiscal_years (id INTEGER PRIMARY KEY)',
                    'CREATE TABLE revision_comments (id INTEGER PRIMARY KEY, text TEXT)',
                    'INSERT INTO fiscal_years VALUES (1)',
                    "INSERT INTO revision_comments VALUES (1, 'legacy')"]:conn.execute(sa.text(sql))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade()
            assert conn.execute(sa.text('SELECT review_version FROM fiscal_years')).scalar()==0
            assert conn.execute(sa.text('SELECT blocking FROM revision_comments')).scalar()==0
            module.downgrade();module.upgrade()
            conn.execute(sa.text("INSERT INTO accounting_revisions (fiscal_year_id,version,submitted_by,submitted_at,state) VALUES (1,1,1,CURRENT_TIMESTAMP,'in_review')"))
            with pytest.raises(RuntimeError,match='history'):module.downgrade()
            assert conn.execute(sa.text('SELECT text FROM revision_comments')).scalar()=='legacy'
