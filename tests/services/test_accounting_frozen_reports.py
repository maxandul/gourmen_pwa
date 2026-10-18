"""Closed-year figures and old-version PDF input remain independent of live data."""
from datetime import date
from unittest.mock import Mock
from backend.extensions import db
from backend.models.accounting import Account, FiscalYear
from backend.models.member import Member
from backend.services.accounting import AccountingService as Accounting
from backend.services.accounting_revision import AccountingRevisionService as Revisions
from backend.services.accounting_pdf import AccountingPdfService
from backend.services.accounting import AccountingValidationError
from tests.routes.test_booking_values import setup, create
import pytest


def previous_year(setup):
    fy=FiscalYear(year=2025,start_date=date(2025,1,1),end_date=date(2025,12,31))
    db.session.add(fy);db.session.commit()
    return create(setup,fiscal_year_id=fy.id,booking_date=date(2025,1,1),amount_rappen=2000)


def test_prior_correction_does_not_change_closed_year_and_warns(app,client,setup):
    with app.app_context():
        prior=previous_year(setup);create(setup)
        member=db.session.get(Member,setup[0])
        fy=Revisions.submit(setup[1],member,expected_version=0)
        Revisions.approve(fy.id,member,expected_version=1)
        summary=Accounting.get_year_summary(fy.id)
        assert Accounting.get_opening_balance(fy.id)==-2000
        Accounting.update_booking(prior.id,amount_rappen=5000)
        assert Accounting.get_opening_balance(fy.id)==-2000
        assert Accounting.get_year_summary(fy.id)==summary
        assert Revisions.opening_difference(fy)==-3000
        Revisions.withdraw(fy.id,member,expected_version=1,reason='Carry correction',closed=True)
        Revisions.submit(fy.id,member,expected_version=1)
        assert Accounting.get_opening_balance(fy.id)==-5000
    page=client.get(f'/accounting/?year={setup[1]}&tab=abschluss')
    assert page.status_code==200


def test_changed_opening_blocks_approval_and_is_visible(app,client,setup):
    with app.app_context():
        prior=previous_year(setup)
        member=db.session.get(Member,setup[0]);fy=Revisions.submit(setup[1],member,expected_version=0)
        Accounting.update_booking(prior.id,amount_rappen=3000)
        with pytest.raises(AccountingValidationError,match='Vorjahressaldo'):
            Revisions.approve(fy.id,member,expected_version=1)
        assert fy.is_in_review
    page=client.get(f'/accounting/?year={setup[1]}&tab=abschluss')
    assert 'Vorjahreskorrektur' in page.text and '-1000 Rp' in page.text


def test_old_report_uses_frozen_accounts_amounts_and_approval(app,setup,monkeypatch):
    with app.app_context():
        booking=create(setup);member=db.session.get(Member,setup[0])
        fy=Revisions.submit(setup[1],member,expected_version=0)
        Revisions.approve(fy.id,member,expected_version=1)
        approval=fy.revision_approval
        Revisions.withdraw(fy.id,member,expected_version=1,reason='Synthetic',closed=True)
        Accounting.update_booking(booking.id,amount_rappen=9000)
        account=db.session.get(Account,setup[2]);account.name='Changed account';account.is_active=False;db.session.commit()
        original=AccountingPdfService._groups_table
        captured=[]
        def capture(groups,summary):
            captured.append((groups,summary));return original(groups,summary)
        monkeypatch.setattr(AccountingPdfService,'_groups_table',capture)
        payload=AccountingPdfService.generate_report(fy,approval=approval)
        assert payload.startswith(b'%PDF')
        assert captured[0][1]['expense_rappen']==1999
        assert captured[0][0][0]['rows'][0]['account'].name=='Synthetic expense'
        assert 'Fassung 1' in AccountingPdfService._title(fy,approval)
