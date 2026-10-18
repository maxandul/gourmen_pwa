"""No real Drive: retry before/after remote success, stale workers and migration."""
from datetime import datetime, timedelta
import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import Mock
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from googleapiclient.errors import HttpError
from httplib2 import Response

from backend.extensions import db
from backend.models.accounting import FiscalYear
from backend.models.accounting_revision import AccountingRevision
from backend.models.member import Member
from backend.services.accounting import AccountingService, AccountingValidationError
from backend.services.accounting_revision import AccountingRevisionService
from backend.services.accounting_report import AccountingReportService as Reports
from backend.services.accounting_pdf import AccountingPdfService
from backend.services.drive_storage import DriveStorageService, DriveValidationError
from tests.routes.test_booking_values import setup,create
from tests.services.test_accounting_year_guards import csrf


@pytest.fixture
def approved(app,setup):
    with app.app_context():
        create(setup);member=db.session.get(Member,setup[0])
        fy=AccountingRevisionService.submit(setup[1],member,expected_version=0)
        AccountingRevisionService.approve(fy.id,member,expected_version=1)
        return fy.revision_approval.id


@pytest.fixture
def transport(monkeypatch):
    state={'files':{},'creates':0,'timeout':False}
    drive=Mock();files=drive.files.return_value
    def get(**kwargs):
        file_id=kwargs['fileId']
        request=Mock()
        if file_id in state['files']:request.execute.return_value=state['files'][file_id]
        else:request.execute.side_effect=HttpError(Response({'status':404}),b'{}')
        return request
    def create_file(drive,body,media):
        file_id=body['id']
        if file_id in state['files']:raise HttpError(Response({'status':409}),b'{}')
        payload=media.getbytes(0,media.size())
        state['files'][file_id]=dict(id=file_id,mimeType='application/pdf',parents=body['parents'],
                                    md5Checksum=hashlib.md5(payload).hexdigest(),trashed=False)
        state['creates']+=1
        if state['timeout']:raise TimeoutError('synthetic response lost after creation')
        return state['files'][file_id]
    files.get.side_effect=get
    files.generateIds.return_value.execute.return_value={'ids':['synthetic-reserved']}
    monkeypatch.setattr(DriveStorageService,'_build_drive',Mock(return_value=drive))
    monkeypatch.setattr(DriveStorageService,'_drive_create_file',create_file)
    monkeypatch.setattr(AccountingService,'get_receipt_folder_id',Mock(return_value='synthetic-folder'))
    return state


def test_render_failure_retry_and_double_click(app,setup,approved,transport,monkeypatch):
    with app.app_context():
        member=db.session.get(Member,setup[0]);original=AccountingPdfService.generate_report
        with monkeypatch.context() as patch:
            patch.setattr(AccountingPdfService,'generate_report',Mock(side_effect=RuntimeError('synthetic')))
            with pytest.raises(AccountingValidationError):Reports.run(approved,member)
        row=db.session.get(AccountingRevision,approved)
        assert row.report_state=='failed' and row.report_payload is None and row.fiscal_year.is_closed
        assert Reports.run(approved,member)=='synthetic-reserved'
        payload=row.report_payload
        assert payload.startswith(b'%PDF') and row.report_state=='complete'
        assert Reports.run(approved,member)=='synthetic-reserved'
        assert transport['creates']==1 and row.report_payload==payload


def test_unknown_upload_result_reuses_same_file_and_bytes(app,setup,approved,transport,monkeypatch):
    with app.app_context():
        member=db.session.get(Member,setup[0]);transport['timeout']=True
        with pytest.raises(AccountingValidationError):Reports.run(approved,member)
        row=db.session.get(AccountingRevision,approved)
        assert row.report_reserved_id=='synthetic-reserved' and row.report_drive_id is None
        payload=row.report_payload
        monkeypatch.setattr(AccountingPdfService,'generate_report',Mock(side_effect=AssertionError('must reuse bytes')))
        assert Reports.run(approved,member)=='synthetic-reserved'
        assert transport['creates']==1 and row.report_payload==payload


def test_database_failure_after_remote_success_recovers_without_second_upload(app,setup,approved,transport,monkeypatch):
    with app.app_context():
        member=db.session.get(Member,setup[0]);original=Reports.checkpoint
        def fail_finish(revision_id,attempt,**values):
            if values.get('report_state')=='complete':raise RuntimeError('synthetic db failure')
            return original(revision_id,attempt,**values)
        with monkeypatch.context() as patch:
            patch.setattr(Reports,'checkpoint',fail_finish)
            with pytest.raises(AccountingValidationError):Reports.run(approved,member)
        assert transport['creates']==1
        Reports.run(approved,member)
        assert transport['creates']==1
        assert db.session.get(AccountingRevision,approved).report_state=='complete'


def test_running_attempt_and_expired_attempt_fencing(app,setup,approved,transport):
    with app.app_context():
        member=db.session.get(Member,setup[0]);row=db.session.get(AccountingRevision,approved)
        row.report_state='working';row.report_attempt=1;row.report_attempted_at=datetime.utcnow();db.session.commit()
        with pytest.raises(AccountingValidationError,match='fünf Minuten'):Reports.run(approved,member)
        assert transport['creates']==0
        row.report_attempted_at=datetime.utcnow()-timedelta(minutes=6);db.session.commit()
        Reports.run(approved,member)
        assert row.report_attempt==2
        with pytest.raises(AccountingValidationError):Reports.checkpoint(approved,1,report_state='failed')
        db.session.rollback()
        assert row.report_state=='complete'


@pytest.mark.parametrize('change',[{'trashed':True},{'parents':['wrong']},{'md5Checksum':'wrong'}])
def test_different_existing_file_is_never_overwritten(transport,change):
    payload=b'synthetic pdf'
    transport['files']['synthetic-reserved']=dict(id='synthetic-reserved',mimeType='application/pdf',
        parents=['synthetic-folder'],trashed=False,md5Checksum=hashlib.md5(payload).hexdigest(),**{})
    transport['files']['synthetic-reserved'].update(change)
    with pytest.raises(DriveValidationError):DriveStorageService.upload_reserved_pdf(payload,'synthetic-reserved','synthetic-folder','Synthetic')
    assert transport['creates']==0


def test_original_retry_route_after_failure_and_reopening(app,client,setup,approved,transport):
    with app.app_context():
        member=db.session.get(Member,setup[0]);transport['timeout']=True
        with pytest.raises(AccountingValidationError):Reports.run(approved,member)
        AccountingRevisionService.withdraw(setup[1],member,expected_version=1,reason='Synthetic',closed=True)
        AccountingRevisionService.submit(setup[1],member,expected_version=1)
    page=client.get(f'/accounting/year/{setup[1]}/revisions')
    assert 'Nicht bestätigt; erneut versuchen' in page.text
    assert client.post(f'/accounting/revision/{approved}/report',data={'csrf_token':csrf(client,app)}).status_code==302
    with app.app_context():
        assert db.session.get(AccountingRevision,approved).report_state=='complete'
        assert AccountingRevision.query.filter_by(version=2).one().report_drive_id is None
        assert db.session.get(FiscalYear,setup[1]).is_in_review
    assert transport['creates']==1
    assert client.post(f'/accounting/revision/{approved}/report').status_code in (400,403)


def test_report_migration_cycle_preserves_existing_report_and_blocks_loss():
    spec=importlib.util.spec_from_file_location('report_migration',Path('migrations/versions/u204c220261018_report_retries.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    engine=sa.create_engine('sqlite://')
    with engine.begin() as conn:
        conn.execute(sa.text('CREATE TABLE accounting_revisions (id INTEGER PRIMARY KEY, report_drive_id TEXT)'))
        conn.execute(sa.text("INSERT INTO accounting_revisions VALUES (1, 'legacy')"))
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade()
            assert conn.execute(sa.text('SELECT report_state FROM accounting_revisions')).scalar()=='complete'
            module.downgrade();module.upgrade()
            conn.execute(sa.text('UPDATE accounting_revisions SET report_attempt=1'))
            with pytest.raises(RuntimeError,match='recovery'):module.downgrade()
            assert conn.execute(sa.text('SELECT report_drive_id FROM accounting_revisions')).scalar()=='legacy'
