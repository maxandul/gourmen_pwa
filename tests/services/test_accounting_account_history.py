"""A-067/A-068: historical details retain inactive accounts and correct signs."""
from copy import deepcopy
from datetime import date
import pytest
from backend.extensions import db
from backend.models.accounting import Account, AccountKind, Booking, BookingDirection, BudgetEntry, FiscalYear
from backend.models.member import Member
from backend.services.accounting import AccountingService as Service, AccountingValidationError
from backend.services.accounting_revision import AccountingRevisionService as Revisions
from tests.routes.test_booking_values import setup, create, form


def test_inactive_used_and_budget_only_accounts_remain_and_groups_net(app,client,setup):
    with app.app_context():
        booking=create(setup,amount_rappen=2000)
        # Synthetic historical counterflow bypasses today's write validation.
        old=Booking(fiscal_year_id=setup[1],booking_date=booking.booking_date,description='Historical counterflow',
            amount_rappen=500,direction=BookingDirection.IN,account_id=setup[2],created_by=setup[0])
        account=booking.account;account.is_active=False;account.group_name='Shared group'
        income=Account(code='3620',name='Synthetic income',kind=AccountKind.INCOME,group_name='Shared group')
        budget_only=Account(code='6789',name='Old budget',kind=AccountKind.EXPENSE,is_active=False)
        db.session.add_all([old,income,budget_only]);db.session.flush()
        db.session.add(BudgetEntry(fiscal_year_id=setup[1],account_id=budget_only.id,amount_rappen=700,created_by=setup[0]));db.session.commit()
        create(setup,account_id=income.id,direction='in',amount_rappen=300)
        rows={r['account'].id:r for r in Service.get_budget_vs_actual(setup[1])}
        assert rows[account.id]['actual_rappen']==1500 and rows[budget_only.id]['budget_rappen']==700
        assert account not in Service.get_active_accounts()
        groups=Service.get_budget_grouped(setup[1]);shared=[g for g in groups if g['name']=='Shared group']
        assert len(shared)==2 and {g['kind'] for g in shared}=={AccountKind.EXPENSE,AccountKind.INCOME}
        result=sum(g['actual_rappen']*(1 if g['kind']==AccountKind.INCOME else -1) for g in groups)
        assert result==Service.get_year_summary(setup[1])['result_rappen']==-1200
        following=FiscalYear(year=2027,start_date=date(2027,1,1),end_date=date(2027,12,31))
        db.session.add(following);db.session.commit()
        assert Service.propose_budget(following.id)[account.id]==2000
        fy=Revisions.submit(setup[1],db.session.get(Member,setup[0]),expected_version=0)
        snapshot=Revisions.current(fy).snapshot
        assert {r['account'].id:r for r in Revisions.budget_rows(snapshot)}[account.id]['actual_rappen']==1500
        legacy=deepcopy(snapshot);legacy.pop('account_actual_mode')
        assert {r['account'].id:r for r in Revisions.budget_rows(legacy)}[account.id]['actual_rappen']==2500
        account.name='Changed';account.kind=AccountKind.INCOME;db.session.commit()
        assert {r['account'].id:r for r in Service.get_budget_vs_actual(setup[1])}[account.id]['actual_rappen']==1500


@pytest.mark.parametrize('mode',['inactive','opposite'])
def test_create_and_edit_reject_account_direction_without_partial_changes(app,client,setup,mode):
    with app.app_context():
        booking=create(setup);original=booking.description
        if mode=='inactive':booking.account.is_active=False;db.session.commit()
        changes={} if mode=='inactive' else {'direction':'in'}
        with pytest.raises(AccountingValidationError):create(setup,**changes)
        with pytest.raises(AccountingValidationError):Service.update_booking(booking.id,description='Must not persist',**changes)
        db.session.commit()
        assert booking.description==original and Booking.query.count()==1


def test_original_manual_form_retains_invalid_direction(app,client,setup):
    page=client.post(f'/accounting/booking/new?year={setup[1]}',data=form(setup,direction='in'))
    assert page.status_code==200 and 'Richtung passt nicht' in page.text and 'Synthetic retained text' in page.text
    with app.app_context():assert Booking.query.count()==0
