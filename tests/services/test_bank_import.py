"""Tests für BankImportService (ZKB-CSV-Import, Phase 4b).

Fixture: tests/fixtures/zkb_kontoauszug_sample.csv — anonymisierte Struktur
des echten ZKB-App-Exports (inkl. Sammelbuchung mit EUR-Detail-Zeilen).
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

import backend.models  # noqa: F401
from backend.extensions import db
from backend.models.accounting import (
    Account,
    AccountKind,
    BankTransaction,
    BankTransactionStatus,
    Booking,
    BookingDirection,
    ClaimStatus,
    ClaimType,
    FiscalYear,
    FiscalYearStatus,
    MemberBankAlias,
    MemberClaim,
)
from backend.models.member import Member
from backend.services.accounting import AccountingService
from backend.services.bank_import import (
    BankImportService,
    normalize_bank_text,
    parse_chf_to_rappen,
)

FIXTURE = Path(__file__).parent.parent / 'fixtures' / 'zkb_kontoauszug_sample.csv'


class FakeUpload:
    def __init__(self, payload: bytes, filename: str = 'kontoauszug.csv'):
        self.filename = filename
        self._stream = io.BytesIO(payload)

    def read(self):
        return self._stream.read()


def _fixture_upload() -> FakeUpload:
    return FakeUpload(FIXTURE.read_bytes())


def _seed_base():
    """Schatzmeister, zwei Mitglieder, offenes Jahr 2026, Kern-Konten."""
    treasurer = Member(
        vorname='Tina', nachname='Treasurer', email='tina@example.test',
        passwort_hash=generate_password_hash('TestPasswortMind12'),
    )
    max_muster = Member(
        vorname='Max', nachname='Muster', email='max@example.test',
        passwort_hash=generate_password_hash('TestPasswortMind12'),
    )
    roman = Member(
        vorname='Roman', nachname='Müller', email='roman@example.test',
        passwort_hash=generate_password_hash('TestPasswortMind12'),
    )
    db.session.add_all([treasurer, max_muster, roman])

    from datetime import date
    fy = FiscalYear(
        year=2026, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        status=FiscalYearStatus.OPEN, membership_fee_rappen=84000,
    )
    db.session.add(fy)

    accounts = [
        Account(code='3000', name='Mitgliederbeiträge', kind=AccountKind.INCOME),
        Account(code='3310', name='Essensanteile von Mitgliedern', kind=AccountKind.INCOME),
        Account(code='3315', name='Aufgerundete Essensanteile', kind=AccountKind.INCOME),
        Account(code='4500', name='Reisen und Ausflüge', kind=AccountKind.EXPENSE),
        Account(code='6100', name='Essen mit Vereinskonto', kind=AccountKind.EXPENSE),
        Account(code='6710', name='Rückzahlungen an Mitglieder', kind=AccountKind.EXPENSE),
        Account(code='6940', name='Kontoführung und Kartengebühren', kind=AccountKind.EXPENSE),
    ]
    db.session.add_all(accounts)
    db.session.commit()
    return treasurer, max_muster, roman, fy


# -- Hilfsfunktionen ---------------------------------------------------------

def test_parse_chf_to_rappen():
    assert parse_chf_to_rappen('3.50') == 350
    assert parse_chf_to_rappen('1626.01') == 162601
    assert parse_chf_to_rappen('840') == 84000
    assert parse_chf_to_rappen("1'150.00") == 115000


def test_normalize_bank_text_folds_umlauts_and_case():
    assert normalize_bank_text('Roman Müller') == normalize_bank_text('Roman Mueller')
    assert normalize_bank_text('MAX MUSTER, TESTSTRASSE') .startswith('max muster')


# -- Parsing / Import ---------------------------------------------------------

def test_import_parses_all_rows_and_splits_collective(app):
    with app.app_context():
        treasurer, *_ = _seed_base()
        statement = BankImportService.import_statement(_fixture_upload(), treasurer)

        assert statement.duplicate_count == 0
        transactions = BankTransaction.query.order_by(BankTransaction.id).all()
        # 6 Hauptzeilen + 2 Detail-Zeilen
        assert len(transactions) == 8

        parent = BankTransaction.query.filter_by(zkb_ref='TESTREF00000005').one()
        assert parent.is_collective
        assert parent.status == BankTransactionStatus.IGNORED
        details = sorted(parent.detail_lines, key=lambda d: d.id)
        assert len(details) == 2
        # EUR proportional auf CHF 1626.01 verteilt, Summe exakt erhalten
        assert sum(d.amount_rappen for d in details) == 162601
        assert details[0].amount_original == 'EUR 922.25'
        assert details[0].line_key == 'TESTREF00000005#1'
        assert details[0].direction == BookingDirection.OUT


def test_import_is_idempotent(app):
    with app.app_context():
        treasurer, *_ = _seed_base()
        first = BankImportService.import_statement(_fixture_upload(), treasurer)
        assert first.new_count == 8

        second = BankImportService.import_statement(_fixture_upload(), treasurer)
        assert second.new_count == 0
        assert second.duplicate_count == 8
        assert BankTransaction.query.count() == 8


def test_import_suggests_fee_account_and_members(app):
    with app.app_context():
        treasurer, max_muster, roman, _fy = _seed_base()
        BankImportService.import_statement(_fixture_upload(), treasurer)

        fee_tx = BankTransaction.query.filter_by(zkb_ref='TESTREF00000001').one()
        fee_account = Account.query.filter_by(code='6940').one()
        assert fee_tx.suggested_account_id == fee_account.id

        # «Roman Mueller» im CSV matcht Mitglied «Roman Müller» via DB-Namen
        roman_tx = BankTransaction.query.filter_by(zkb_ref='TESTREF00000003').one()
        assert roman_tx.suggested_member_id == roman.id

        # Belastung an Mitglied → Rückzahlungs-Konto
        refund_tx = BankTransaction.query.filter_by(zkb_ref='TESTREF00000006').one()
        assert refund_tx.suggested_member_id == max_muster.id
        refund_account = Account.query.filter_by(code='6710').one()
        assert refund_tx.suggested_account_id == refund_account.id


# -- Verbuchen und Claims ------------------------------------------------------

def test_book_transaction_applies_claim_and_learns_alias(app):
    with app.app_context():
        treasurer, max_muster, _roman, fy = _seed_base()
        claim = MemberClaim(
            member_id=max_muster.id, claim_type=ClaimType.MITGLIEDERBEITRAG,
            fiscal_year_id=fy.id, expected_rappen=84000,
        )
        db.session.add(claim)
        db.session.commit()

        BankImportService.import_statement(_fixture_upload(), treasurer)
        tx = BankTransaction.query.filter_by(zkb_ref='TESTREF00000002').one()
        account = Account.query.filter_by(code='3000').one()

        booking = BankImportService.book_transaction(
            tx.id, account_id=account.id, member_id=max_muster.id,
            claim_id=claim.id, booked_by=treasurer,
        )
        assert booking.amount_rappen == 7000
        assert booking.payment_ref == 'TESTREF00000002'
        assert tx.status == BankTransactionStatus.BOOKED

        db.session.refresh(claim)
        assert claim.paid_rappen == 7000
        assert claim.status == ClaimStatus.TEILWEISE

        # Alias gelernt → künftige Importe matchen automatisch
        aliases = MemberBankAlias.query.filter_by(member_id=max_muster.id).all()
        assert any('max muster' in a.alias_text for a in aliases)


def test_book_transaction_overpay_creates_rounding_booking(app):
    with app.app_context():
        treasurer, _max, roman, _fy = _seed_base()
        from datetime import datetime
        event = _make_event(roman, datetime(2026, 6, 27, 19, 0))
        claim = MemberClaim(
            member_id=roman.id, claim_type=ClaimType.ESSENSANTEIL,
            event_id=event.id, expected_rappen=11000,  # Anteil CHF 110
        )
        db.session.add(claim)
        db.session.commit()

        BankImportService.import_statement(_fixture_upload(), treasurer)
        tx = BankTransaction.query.filter_by(zkb_ref='TESTREF00000003').one()  # CHF 112
        share_account = Account.query.filter_by(code='3310').one()

        BankImportService.book_transaction(
            tx.id, account_id=share_account.id, member_id=roman.id,
            claim_id=claim.id, booked_by=treasurer,
        )

        bookings = Booking.query.order_by(Booking.id).all()
        assert len(bookings) == 2
        assert bookings[0].amount_rappen == 11000
        rounding_account = Account.query.filter_by(code='3315').one()
        assert bookings[1].account_id == rounding_account.id
        assert bookings[1].amount_rappen == 200  # CHF 2 Aufrundung

        db.session.refresh(claim)
        assert claim.status == ClaimStatus.BEGLICHEN
        assert claim.paid_rappen == 11200


def _make_event(organizer: Member, when):
    from backend.models.event import Event, EventType

    event = Event(
        organisator_id=organizer.id,
        datum=when,
        event_typ=EventType.MONATSESSEN,
        season=when.year,
        restaurant='Testo',
    )
    db.session.add(event)
    db.session.commit()
    return event


# -- Claims-Service -------------------------------------------------------------

def test_create_claims_for_fiscal_year_is_idempotent(app):
    with app.app_context():
        treasurer, _max, _roman, fy = _seed_base()
        created = AccountingService.create_claims_for_fiscal_year(fy.id, treasurer)
        assert len(created) == 3  # alle aktiven Mitglieder
        assert all(c.expected_rappen == 84000 for c in created)

        again = AccountingService.create_claims_for_fiscal_year(fy.id, treasurer)
        assert again == []


def test_billbro_claims_club_vs_private(app):
    with app.app_context():
        _treasurer, max_muster, roman, _fy = _seed_base()
        from datetime import datetime
        from backend.models.event import BillPaidBy
        from backend.models.participation import Participation

        event = _make_event(roman, datetime(2026, 6, 27, 19, 0))
        db.session.add_all([
            Participation(member_id=max_muster.id, event_id=event.id,
                          teilnahme=True, calculated_share_rappen=8000),
            Participation(member_id=roman.id, event_id=event.id,
                          teilnahme=True, calculated_share_rappen=9000),
        ])
        event.bill_paid_by = BillPaidBy.MITGLIED
        event.bill_payer_member_id = roman.id
        db.session.commit()

        claims = AccountingService.create_claims_for_billbro(event)
        # Zahler Roman bekommt keinen Posten; Max schuldet Roman privat
        assert len(claims) == 1
        assert claims[0].member_id == max_muster.id
        assert claims[0].creditor_member_id == roman.id
        assert not claims[0].is_club_claim

        confirmed = AccountingService.confirm_private_payment(claims[0].id, roman)
        assert confirmed.status == ClaimStatus.BEGLICHEN


def test_create_fiscal_year_seeds_budget_proposal(app):
    with app.app_context():
        treasurer, _max, _roman, fy = _seed_base()
        from datetime import date
        from backend.models.accounting import BudgetEntry

        travel = Account.query.filter_by(code='4500').one()
        AccountingService.create_booking(
            fiscal_year_id=fy.id, booking_date=date(2026, 5, 1),
            description='Hotel Testreise', amount_rappen=412345,
            direction=BookingDirection.OUT, account_id=travel.id,
            event_id=None, member_id=None, created_by=treasurer,
        )
        fy_next = AccountingService.create_fiscal_year(2027, treasurer)
        assert fy_next.membership_fee_rappen == 84000  # vom Vorjahr übernommen

        entries = {
            e.account_id: e.amount_rappen
            for e in BudgetEntry.query.filter_by(fiscal_year_id=fy_next.id).all()
        }
        contribution = Account.query.filter_by(code='3000').one()
        assert entries[contribution.id] == 3 * 84000
        assert entries[travel.id] == 412000


def test_propose_budget_uses_member_count_and_previous_actuals(app):
    with app.app_context():
        treasurer, _max, _roman, fy = _seed_base()
        from datetime import date
        travel = Account.query.filter_by(code='4500').one()
        AccountingService.create_booking(
            fiscal_year_id=fy.id, booking_date=date(2026, 5, 1),
            description='Hotel Testreise', amount_rappen=412345,
            direction=BookingDirection.OUT, account_id=travel.id,
            event_id=None, member_id=None, created_by=treasurer,
        )
        fy_next = FiscalYear(
            year=2027, start_date=date(2027, 1, 1), end_date=date(2027, 12, 31),
            status=FiscalYearStatus.OPEN, membership_fee_rappen=84000,
        )
        db.session.add(fy_next)
        db.session.commit()

        proposals = AccountingService.propose_budget(fy_next.id)
        contribution = Account.query.filter_by(code='3000').one()
        assert proposals[contribution.id] == 3 * 84000
        # Vorjahres-Ist auf CHF 10 gerundet: 4123.45 → 4120.00
        assert proposals[travel.id] == 412000
