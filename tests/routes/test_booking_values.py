"""A-057/A-058: real form submissions and service boundaries, synthetic values."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.extensions import db
from backend.forms.accounting import chf_to_rappen
from backend.models.accounting import Account, AccountKind, Booking, FiscalYear, FiscalYearStatus
from backend.models.member import Member, Role
from backend.services.accounting import AccountingService, AccountingValidationError
from tests.conftest import auth_id


@pytest.fixture
def setup(app, client):
    with app.app_context():
        member = Member(vorname='Synthetic', nachname='Booker', email='booker@example.com', role=Role.ADMIN)
        member.set_password('Synthetic-booking-password1!')
        fy = FiscalYear(year=2026, start_date=date(2026,1,1), end_date=date(2026,12,31))
        account = Account(code='6700', name='Synthetic expense', kind=AccountKind.EXPENSE)
        db.session.add_all([member, fy, account]); db.session.commit()
        ids = member.id, fy.id, account.id
    with client.session_transaction() as state:
        state['_user_id'] = auth_id(client, ids[0]); state['_fresh'] = True
    return ids


def form(setup, **changes):
    data = dict(booking_date='2026-06-01', description='Synthetic retained text', amount_chf='19.99',
                direction='out', account_id=str(setup[2]), event_id='0', member_id='0')
    data.update(changes)
    return data


def create(setup, **changes):
    data = dict(fiscal_year_id=setup[1], booking_date=date(2026,6,1), description='Original',
                amount_rappen=1999, direction='out', account_id=setup[2], event_id=None,
                member_id=None, created_by=db.session.get(Member, setup[0]))
    data.update(changes)
    return AccountingService.create_booking(**data)


@pytest.mark.parametrize('amount,expected', [('19.99',1999),('0.01',1),('0.04',4),('300',30000),('1.230',123)])
def test_manual_form_keeps_exact_cents(app, client, setup, amount, expected):
    response = client.post(f'/accounting/booking/new?year={setup[1]}', data=form(setup, amount_chf=amount))
    assert response.status_code == 302
    with app.app_context():
        booking = Booking.query.one()
        assert booking.amount_rappen == expected
        assert booking.fiscal_year_id == setup[1]


@pytest.mark.parametrize('value', ['19.999', 'NaN', 'sNaN', 'Infinity', '-Infinity', '-1', '0',
                                   '1e1000', '0.0001', '21474836.48', 'garbage'])
def test_invalid_money_has_field_error_and_no_booking(app, client, setup, value):
    response = client.post(f'/accounting/booking/new?year={setup[1]}', data=form(setup, amount_chf=value))
    assert response.status_code == 200
    assert 'Synthetic retained text' in response.text
    assert 'form-field__error' in response.text
    with app.app_context():
        assert Booking.query.count() == 0


@pytest.mark.parametrize('day,valid', [('2025-12-31',False),('2026-01-01',True),('2026-12-31',True),('2027-01-01',False)])
def test_date_boundaries_create_and_edit(app, client, setup, day, valid):
    response = client.post(f'/accounting/booking/new?year={setup[1]}', data=form(setup, booking_date=day))
    assert response.status_code == (302 if valid else 200)
    with app.app_context():
        assert Booking.query.count() == int(valid)
        booking = Booking.query.first() if valid else create(setup)
        bid = booking.id
    response = client.post(f'/accounting/booking/{bid}/edit', data=form(setup, booking_date=day, amount_chf='2.01'))
    assert response.status_code == (302 if valid else 400)
    if not valid:
        assert 'Buchungsdatum muss im Geschäftsjahr 2026 liegen.' in response.text
        assert 'Synthetic retained text' in response.text and f'value="{day}"' in response.text
    with app.app_context():
        assert db.session.get(Booking,bid).amount_rappen == (201 if valid else 1999)


@pytest.mark.parametrize('value', [None, '2026-01-01', datetime(2026,1,1), date(2025,12,31), date(2027,1,1)])
def test_service_date_cannot_bypass_form(app, setup, value):
    with app.app_context():
        with pytest.raises(AccountingValidationError):
            create(setup, booking_date=value)
        db.session.commit()
        assert Booking.query.count() == 0


@pytest.mark.parametrize('value', [True, 0, -1, 1.5, Decimal('2'), 2_147_483_648])
def test_service_rejects_non_integer_or_overflow_amount(app, setup, value):
    with app.app_context():
        with pytest.raises(AccountingValidationError):
            create(setup, amount_rappen=value)
        assert Booking.query.count() == 0


def test_failed_later_validation_does_not_flush_partial_edit(app, setup):
    with app.app_context():
        booking = create(setup)
        with pytest.raises(AccountingValidationError):
            AccountingService.update_booking(booking.id, booking_date=date(2026,12,31),
                description='Changed', amount_rappen=123, account_id=9999)
        db.session.commit()  # No rollback can conceal an accidental staged mutation.
        db.session.refresh(booking)
        assert booking.booking_date == date(2026,6,1)
        assert booking.description == 'Original' and booking.amount_rappen == 1999


def test_edit_invalid_amount_retains_input_and_original(app, client, setup):
    with app.app_context():
        bid = create(setup).id
    response = client.post(f'/accounting/booking/{bid}/edit', data=form(setup, amount_chf='1.999'))
    assert response.status_code == 400
    assert 'ganzen Rappen' in response.text and 'value="1.999"' in response.text
    with app.app_context():
        assert db.session.get(Booking,bid).amount_rappen == 1999


def test_database_amount_boundary_exact():
    assert chf_to_rappen('21474836.47') == 2_147_483_647
    with pytest.raises(ValueError):
        chf_to_rappen('1.000000000000000000000000000001')


@pytest.mark.parametrize('status',[FiscalYearStatus.IN_REVIEW,FiscalYearStatus.CLOSED])
def test_year_lock_still_prevents_create_and_edit(app, client, setup, status):
    with app.app_context():
        bid = create(setup).id
        db.session.get(FiscalYear,setup[1]).status = status; db.session.commit()
    assert client.post(f'/accounting/booking/new?year={setup[1]}',data=form(setup)).status_code == 200
    assert client.post(f'/accounting/booking/{bid}/edit',data=form(setup)).status_code == 400
    with app.app_context():
        assert Booking.query.count() == 1 and Booking.query.one().description == 'Original'


@pytest.mark.parametrize('day', [date(2026,12,31), date(2027,1,1)])
def test_bank_booking_uses_payment_year_and_preserves_cents(app, setup, day):
    from backend.models.accounting import BankStatementImport, BankTransaction, BookingDirection
    from backend.services.bank_import import BankImportService
    with app.app_context():
        statement = BankStatementImport(fiscal_year_id=setup[1], filename='synthetic.csv', imported_by=setup[0])
        db.session.add(statement); db.session.flush()
        tx = BankTransaction(import_id=statement.id, line_key='synthetic-year', booked_date=day,
            amount_rappen=1999, direction=BookingDirection.OUT, buchungstext='Synthetic payment')
        db.session.add(tx); db.session.commit()
        booking = BankImportService.book_transaction(tx.id, account_id=setup[2],
            booked_by=db.session.get(Member,setup[0]))
        assert booking.fiscal_year.year == day.year
        assert booking.booking_date == day and booking.amount_rappen == 1999


def test_import_cannot_bypass_year_service_guard(app, setup, monkeypatch):
    from backend.models.accounting import BankStatementImport, BankTransaction, BookingDirection
    from backend.services.bank_import import BankImportService
    with app.app_context():
        fy = db.session.get(FiscalYear, setup[1])
        statement = BankStatementImport(fiscal_year_id=fy.id, filename='synthetic.csv', imported_by=setup[0])
        db.session.add(statement); db.session.flush()
        tx = BankTransaction(import_id=statement.id, line_key='synthetic-invalid-year', booked_date=date(2027,1,1),
            amount_rappen=1999, direction=BookingDirection.OUT, buchungstext='Synthetic payment')
        db.session.add(tx); db.session.commit()
        monkeypatch.setattr(AccountingService,'get_or_create_fiscal_year',lambda year, **kwargs: fy)
        with pytest.raises(AccountingValidationError, match='Geschäftsjahr'):
            BankImportService.book_transaction(tx.id, account_id=setup[2],
                booked_by=db.session.get(Member,setup[0]))
        db.session.commit()
        assert Booking.query.count() == 0 and tx.is_pending
