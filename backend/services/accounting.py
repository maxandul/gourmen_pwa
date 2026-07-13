"""AccountingService – Buchhaltungsmodul (Phase 4).

Authoritative Spezifikation: docs/capabilities/accounting.md.

Beträge immer in Rappen als Integer. Belege landen via DriveStorageService
in `Buchhaltung/{Jahr}/` im Shared Drive; Strukturdaten in Postgres.
Routes rufen Services, Services rufen Models und externe APIs.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from backend.extensions import db
from backend.models.accounting import (
    Account,
    AccountKind,
    Booking,
    BookingDirection,
    BudgetEntry,
    ClaimStatus,
    ClaimType,
    FiscalYear,
    FiscalYearStatus,
    MemberClaim,
    Receipt,
    RevisionApproval,
    RevisionComment,
)
from backend.models.member import Member
from backend.services.drive_storage import DriveStorageService

logger = logging.getLogger(__name__)

ACCOUNTING_FOLDER_NAME = "Buchhaltung"
COMMENT_PREFIX_MAX_LENGTH = 30


class AccountingError(Exception):
    """Generischer Buchhaltungs-Fehler (Route mappt auf Flash-Meldung)."""


class AccountingValidationError(AccountingError):
    """Validierungs- oder Guard-Fehler (z.B. Jahr nicht offen)."""


def _as_direction(direction) -> BookingDirection:
    if isinstance(direction, BookingDirection):
        return direction
    try:
        return BookingDirection(direction)
    except ValueError as exc:
        raise AccountingValidationError(f"Ungültige Richtung «{direction}».") from exc


def _as_kind(kind) -> AccountKind:
    if isinstance(kind, AccountKind):
        return kind
    try:
        return AccountKind(kind)
    except ValueError as exc:
        raise AccountingValidationError(f"Ungültige Konto-Art «{kind}».") from exc


class AccountingService:
    """Business-Logik für Journal, Budget, Belege und Revisions-Workflow."""

    # -- Konten ---------------------------------------------------------

    @staticmethod
    def get_active_accounts(kind=None) -> list[Account]:
        query = Account.query.filter_by(is_active=True)
        if kind is not None:
            query = query.filter_by(kind=_as_kind(kind))
        return query.order_by(Account.sort_order, Account.code).all()

    @staticmethod
    def create_account(code: str, name: str, kind, group_name: str | None) -> Account:
        code = (code or '').strip()
        name = (name or '').strip()
        if not code or not name:
            raise AccountingValidationError("Code und Name sind erforderlich.")
        if Account.query.filter_by(code=code).first():
            raise AccountingValidationError(f"Konto {code} existiert bereits.")
        max_sort = db.session.query(db.func.max(Account.sort_order)).scalar() or 0
        account = Account(
            code=code, name=name, kind=_as_kind(kind),
            group_name=(group_name or '').strip() or None,
            is_active=True, sort_order=max_sort + 1,
        )
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def update_account(account_id: int, **kwargs) -> Account:
        account = db.session.get(Account, account_id)
        if account is None:
            raise AccountingValidationError("Konto nicht gefunden.")
        if 'code' in kwargs:
            new_code = (kwargs['code'] or '').strip()
            if not new_code:
                raise AccountingValidationError("Code ist erforderlich.")
            clash = Account.query.filter(
                Account.code == new_code, Account.id != account.id
            ).first()
            if clash:
                raise AccountingValidationError(f"Konto {new_code} existiert bereits.")
            account.code = new_code
        if 'name' in kwargs:
            new_name = (kwargs['name'] or '').strip()
            if not new_name:
                raise AccountingValidationError("Name ist erforderlich.")
            account.name = new_name
        if 'kind' in kwargs:
            account.kind = _as_kind(kwargs['kind'])
        if 'group_name' in kwargs:
            account.group_name = (kwargs['group_name'] or '').strip() or None
        if 'is_active' in kwargs:
            account.is_active = bool(kwargs['is_active'])
        if 'sort_order' in kwargs:
            account.sort_order = int(kwargs['sort_order'])
        db.session.commit()
        return account

    # -- Geschäftsjahre ---------------------------------------------------

    @staticmethod
    def get_fiscal_year(fiscal_year_id: int) -> FiscalYear:
        fy = db.session.get(FiscalYear, fiscal_year_id)
        if fy is None:
            raise AccountingValidationError("Geschäftsjahr nicht gefunden.")
        return fy

    @staticmethod
    def get_or_create_fiscal_year(year: int) -> FiscalYear:
        fy = FiscalYear.query.filter_by(year=year).first()
        if fy is None:
            fy = FiscalYear(
                year=year,
                start_date=date(year, 1, 1),
                end_date=date(year, 12, 31),
                status=FiscalYearStatus.OPEN,
            )
            db.session.add(fy)
            db.session.commit()
        return fy

    @staticmethod
    def get_all_fiscal_years() -> list[FiscalYear]:
        return FiscalYear.query.order_by(FiscalYear.year.desc()).all()

    @classmethod
    def submit_for_review(cls, fiscal_year_id: int, by_member: Member) -> FiscalYear:
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status != FiscalYearStatus.OPEN:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist nicht offen und kann nicht freigegeben werden."
            )
        fy.status = FiscalYearStatus.IN_REVIEW
        db.session.commit()
        logger.info("Geschäftsjahr %s zur Revision freigegeben von Member %s",
                    fy.year, by_member.id)
        return fy

    @classmethod
    def withdraw_from_review(cls, fiscal_year_id: int, by_member: Member) -> FiscalYear:
        """Freigabe zurückziehen: in_review → open (Schatzmeister/Admin)."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status != FiscalYearStatus.IN_REVIEW:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist nicht in Prüfung und kann nicht zurückgezogen werden."
            )
        fy.status = FiscalYearStatus.OPEN
        db.session.commit()
        logger.info(
            "Geschäftsjahr %s Freigabe zurückgezogen von Member %s",
            fy.year, by_member.id,
        )
        return fy

    @classmethod
    def revoke_approval(cls, fiscal_year_id: int, by_member: Member) -> FiscalYear:
        """Abschluss rückgängig: closed → in_review (Revisor/Admin)."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status != FiscalYearStatus.CLOSED:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist nicht abgeschlossen und kann nicht geöffnet werden."
            )
        if fy.revision_approval is None:
            raise AccountingValidationError(
                f"Jahr {fy.year} hat keine Revisionsbestätigung."
            )
        db.session.delete(fy.revision_approval)
        fy.status = FiscalYearStatus.IN_REVIEW
        fy.closed_at = None
        db.session.commit()
        logger.info(
            "Geschäftsjahr %s Abschluss rückgängig von Member %s",
            fy.year, by_member.id,
        )
        return fy

    @classmethod
    def create_fiscal_year(cls, year: int, by_member: Member) -> FiscalYear:
        """Neues Geschäftsjahr anlegen; Budget vom Vorjahr übernehmen falls vorhanden."""
        if FiscalYear.query.filter_by(year=year).first():
            raise AccountingValidationError(f"Geschäftsjahr {year} existiert bereits.")
        prev = FiscalYear.query.filter_by(year=year - 1).first()
        fy = FiscalYear(
            year=year,
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            status=FiscalYearStatus.OPEN,
        )
        db.session.add(fy)
        db.session.flush()
        if prev is not None:
            for entry in prev.budget_entries:
                db.session.add(BudgetEntry(
                    fiscal_year_id=fy.id,
                    account_id=entry.account_id,
                    amount_rappen=entry.amount_rappen,
                    created_by=by_member.id,
                ))
        db.session.commit()
        logger.info("Geschäftsjahr %s angelegt von Member %s", year, by_member.id)
        return fy

    @classmethod
    def approve_year(cls, fiscal_year_id: int, reviewer: Member) -> FiscalYear:
        """Jahr bestätigen: RevisionApproval anlegen, Status auf closed.

        PDF-Bericht und Drive-Ablage werden vom Revisions-Workflow
        (Route) via AccountingPdfService angestossen und via
        `set_approval_report` nachgetragen.
        """
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status != FiscalYearStatus.IN_REVIEW:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist nicht in Prüfung und kann nicht bestätigt werden."
            )
        if fy.revision_approval is not None:
            raise AccountingValidationError(
                f"Jahr {fy.year} wurde bereits bestätigt."
            )
        approval = RevisionApproval(
            fiscal_year_id=fy.id,
            reviewer_id=reviewer.id,
            approved_at=datetime.utcnow(),
        )
        fy.status = FiscalYearStatus.CLOSED
        fy.closed_at = datetime.utcnow()
        db.session.add(approval)
        db.session.commit()
        logger.info("Geschäftsjahr %s bestätigt von Revisor %s", fy.year, reviewer.id)
        return fy

    @classmethod
    def set_approval_report(cls, fiscal_year_id: int, report_drive_id: str) -> None:
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.revision_approval is None:
            raise AccountingValidationError("Keine Revisionsbestätigung vorhanden.")
        fy.revision_approval.report_drive_id = report_drive_id
        db.session.commit()

    # -- Budget -----------------------------------------------------------

    @classmethod
    def set_budget(cls, fiscal_year_id: int, account_id: int,
                   amount_rappen: int, by_member: Member) -> BudgetEntry:
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status == FiscalYearStatus.CLOSED:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist abgeschlossen, Budget nicht mehr änderbar."
            )
        account = db.session.get(Account, account_id)
        if account is None:
            raise AccountingValidationError("Konto nicht gefunden.")
        if amount_rappen < 0:
            raise AccountingValidationError("Budget darf nicht negativ sein.")
        entry = BudgetEntry.query.filter_by(
            fiscal_year_id=fy.id, account_id=account.id
        ).first()
        if entry is None:
            entry = BudgetEntry(
                fiscal_year_id=fy.id, account_id=account.id,
                amount_rappen=amount_rappen, created_by=by_member.id,
            )
            db.session.add(entry)
        else:
            entry.amount_rappen = amount_rappen
        db.session.commit()
        return entry

    @classmethod
    def get_budget_vs_actual(cls, fiscal_year_id: int) -> list[dict]:
        """Pro aktivem Konto: Budget (Soll), Ist und Abweichung in Rappen."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        accounts = cls.get_active_accounts()

        budget_by_account = {
            e.account_id: e.amount_rappen
            for e in BudgetEntry.query.filter_by(fiscal_year_id=fy.id).all()
        }
        actual_rows = (
            db.session.query(Booking.account_id, db.func.sum(Booking.amount_rappen))
            .filter(Booking.fiscal_year_id == fy.id)
            .group_by(Booking.account_id)
            .all()
        )
        actual_by_account = {account_id: total for account_id, total in actual_rows}

        rows = []
        for account in accounts:
            budget = budget_by_account.get(account.id, 0)
            actual = actual_by_account.get(account.id, 0) or 0
            rows.append({
                'account': account,
                'budget_rappen': budget,
                'actual_rappen': actual,
                'deviation_rappen': actual - budget,
            })
        return rows

    @classmethod
    def get_budget_grouped(cls, fiscal_year_id: int) -> list[dict]:
        """Budget-vs-Ist-Zeilen nach Kontengruppe gruppiert (Reihenfolge erhalten)."""
        groups: list[dict] = []
        by_name: dict[str, dict] = {}
        for row in cls.get_budget_vs_actual(fiscal_year_id):
            group_name = row['account'].group_name or 'Ohne Gruppe'
            group = by_name.get(group_name)
            if group is None:
                group = {
                    'name': group_name,
                    'kind': row['account'].kind,
                    'rows': [],
                    'budget_rappen': 0,
                    'actual_rappen': 0,
                }
                by_name[group_name] = group
                groups.append(group)
            group['rows'].append(row)
            group['budget_rappen'] += row['budget_rappen']
            group['actual_rappen'] += row['actual_rappen']
        for group in groups:
            group['deviation_rappen'] = group['actual_rappen'] - group['budget_rappen']
        return groups

    @classmethod
    def get_opening_balance(cls, fiscal_year_id: int) -> int:
        """Sparkapital zu Jahresbeginn: kumuliertes Ergebnis aller Vorjahre (Rappen)."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        rows = (
            db.session.query(Booking.direction, db.func.sum(Booking.amount_rappen))
            .join(FiscalYear, FiscalYear.id == Booking.fiscal_year_id)
            .filter(FiscalYear.year < fy.year)
            .group_by(Booking.direction)
            .all()
        )
        sums = dict(rows)
        income = sums.get(BookingDirection.IN, 0) or 0
        expense = sums.get(BookingDirection.OUT, 0) or 0
        return income - expense

    # -- Buchungen ----------------------------------------------------------

    @classmethod
    def create_booking(cls, fiscal_year_id: int, booking_date: date,
                       description: str, amount_rappen: int, direction,
                       account_id: int, event_id: int | None,
                       member_id: int | None, created_by: Member,
                       payment_ref: str | None = None) -> Booking:
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status != FiscalYearStatus.OPEN:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist nicht offen – keine Buchungen möglich."
            )
        description = (description or '').strip()
        if not description:
            raise AccountingValidationError("Beschreibung ist erforderlich.")
        if not isinstance(amount_rappen, int) or amount_rappen <= 0:
            raise AccountingValidationError("Betrag muss grösser als 0 sein.")
        account = db.session.get(Account, account_id)
        if account is None:
            raise AccountingValidationError("Konto nicht gefunden.")

        booking = Booking(
            fiscal_year_id=fy.id,
            booking_date=booking_date,
            description=description,
            amount_rappen=amount_rappen,
            direction=_as_direction(direction),
            account_id=account.id,
            event_id=event_id,
            member_id=member_id,
            payment_ref=(payment_ref or '').strip() or None,
            created_by=created_by.id,
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    @classmethod
    def update_booking(cls, booking_id: int, **kwargs) -> Booking:
        booking = db.session.get(Booking, booking_id)
        if booking is None:
            raise AccountingValidationError("Buchung nicht gefunden.")
        if booking.fiscal_year.status != FiscalYearStatus.OPEN:
            raise AccountingValidationError(
                "Jahr ist nicht offen – Buchung nicht mehr änderbar."
            )
        if 'booking_date' in kwargs:
            booking.booking_date = kwargs['booking_date']
        if 'description' in kwargs:
            description = (kwargs['description'] or '').strip()
            if not description:
                raise AccountingValidationError("Beschreibung ist erforderlich.")
            booking.description = description
        if 'amount_rappen' in kwargs:
            amount = kwargs['amount_rappen']
            if not isinstance(amount, int) or amount <= 0:
                raise AccountingValidationError("Betrag muss grösser als 0 sein.")
            booking.amount_rappen = amount
        if 'direction' in kwargs:
            booking.direction = _as_direction(kwargs['direction'])
        if 'account_id' in kwargs:
            account = db.session.get(Account, kwargs['account_id'])
            if account is None:
                raise AccountingValidationError("Konto nicht gefunden.")
            booking.account_id = account.id
        if 'event_id' in kwargs:
            booking.event_id = kwargs['event_id']
        if 'member_id' in kwargs:
            booking.member_id = kwargs['member_id']
        if 'payment_ref' in kwargs:
            booking.payment_ref = (kwargs['payment_ref'] or '').strip() or None
        db.session.commit()
        return booking

    @classmethod
    def get_journal(cls, fiscal_year_id: int, account_id: int | None = None,
                    direction=None) -> list[Booking]:
        query = Booking.query.filter_by(fiscal_year_id=fiscal_year_id)
        if account_id:
            query = query.filter_by(account_id=account_id)
        if direction:
            query = query.filter_by(direction=_as_direction(direction))
        return query.order_by(Booking.booking_date.desc(), Booking.id.desc()).all()

    @classmethod
    def get_year_summary(cls, fiscal_year_id: int) -> dict:
        """Einnahmen, Ausgaben, Jahresergebnis und KPI-Werte in Rappen."""
        fy = cls.get_fiscal_year(fiscal_year_id)

        sums = dict(
            db.session.query(Booking.direction, db.func.sum(Booking.amount_rappen))
            .filter(Booking.fiscal_year_id == fy.id)
            .group_by(Booking.direction)
            .all()
        )
        income = sums.get(BookingDirection.IN, 0) or 0
        expense = sums.get(BookingDirection.OUT, 0) or 0

        open_receipts = (
            Receipt.query.filter(Receipt.booking_id.is_(None)).count()
        )

        budget_total = (
            db.session.query(db.func.sum(BudgetEntry.amount_rappen))
            .join(Account, Account.id == BudgetEntry.account_id)
            .filter(
                BudgetEntry.fiscal_year_id == fy.id,
                Account.kind == AccountKind.EXPENSE,
            )
            .scalar()
        ) or 0
        budget_used_pct = round(expense / budget_total * 100) if budget_total else None

        return {
            'income_rappen': income,
            'expense_rappen': expense,
            'result_rappen': income - expense,
            'open_receipts': open_receipts,
            'budget_total_rappen': budget_total,
            'budget_used_pct': budget_used_pct,
            'booking_count': Booking.query.filter_by(fiscal_year_id=fy.id).count(),
        }

    # -- Offene Posten (MemberClaim, Spec Sektion 11.5) ---------------------

    @classmethod
    def create_claims_for_fiscal_year(cls, fiscal_year_id: int,
                                      by_member: Member) -> list[MemberClaim]:
        """Beitrags-Claims pro aktivem Mitglied anlegen (idempotent).

        Betrag = FiscalYear.membership_fee_rappen; pro Mitglied nachträglich
        überschreibbar (Sonderfälle).
        """
        fy = cls.get_fiscal_year(fiscal_year_id)
        if not fy.membership_fee_rappen:
            raise AccountingValidationError(
                f"Jahr {fy.year} hat keinen Jahresbeitrag hinterlegt."
            )
        existing_member_ids = {
            c.member_id
            for c in MemberClaim.query.filter_by(
                fiscal_year_id=fy.id, claim_type=ClaimType.MITGLIEDERBEITRAG,
            ).all()
        }
        created = []
        for member in Member.query.filter_by(is_active=True).all():
            if member.id in existing_member_ids:
                continue
            claim = MemberClaim(
                member_id=member.id,
                claim_type=ClaimType.MITGLIEDERBEITRAG,
                fiscal_year_id=fy.id,
                expected_rappen=fy.membership_fee_rappen,
                note=f'Mitgliederbeitrag {fy.year}',
            )
            db.session.add(claim)
            created.append(claim)
        db.session.commit()
        logger.info(
            "Beitrags-Claims %s: %s angelegt von Member %s",
            fy.year, len(created), by_member.id,
        )
        return created

    @staticmethod
    def get_claim(claim_id: int) -> MemberClaim:
        claim = db.session.get(MemberClaim, claim_id)
        if claim is None:
            raise AccountingValidationError("Offener Posten nicht gefunden.")
        return claim

    @staticmethod
    def get_claims(claim_type=None, status=None, member_id: int | None = None,
                   fiscal_year_id: int | None = None,
                   only_club: bool = False) -> list[MemberClaim]:
        query = MemberClaim.query
        if claim_type:
            query = query.filter_by(claim_type=ClaimType(claim_type)
                                    if not isinstance(claim_type, ClaimType)
                                    else claim_type)
        if status:
            query = query.filter_by(status=ClaimStatus(status)
                                    if not isinstance(status, ClaimStatus)
                                    else status)
        if member_id:
            query = query.filter_by(member_id=member_id)
        if fiscal_year_id:
            query = query.filter_by(fiscal_year_id=fiscal_year_id)
        if only_club:
            query = query.filter(MemberClaim.creditor_member_id.is_(None))
        return query.order_by(MemberClaim.created_at.desc()).all()

    @staticmethod
    def get_open_claims_for_member(member: Member) -> list[MemberClaim]:
        """Eigene offene/teilbezahlte Posten (Dashboard)."""
        return (
            MemberClaim.query.filter(
                MemberClaim.member_id == member.id,
                MemberClaim.status.in_((ClaimStatus.OFFEN, ClaimStatus.TEILWEISE)),
            )
            .order_by(MemberClaim.created_at)
            .all()
        )

    @staticmethod
    def get_claims_to_confirm(member: Member) -> list[MemberClaim]:
        """Posten, bei denen dieses Mitglied privater Gläubiger ist."""
        return (
            MemberClaim.query.filter(
                MemberClaim.creditor_member_id == member.id,
                MemberClaim.status.in_((ClaimStatus.OFFEN, ClaimStatus.TEILWEISE)),
            )
            .order_by(MemberClaim.created_at)
            .all()
        )

    @classmethod
    def create_claims_for_billbro(cls, event) -> list[MemberClaim]:
        """Essensanteil-Claims nach BillBro-Abschluss anlegen (Spec 11.6).

        Zahlweg Vereinskonto: Gläubiger Verein (creditor NULL).
        Zahlweg Mitglied: Gläubiger = bill_payer_member_id, der Zahler
        selbst bekommt keinen Posten. Idempotent pro Event.
        """
        if event.bill_paid_by is None:
            return []
        creditor_id = None if event.is_paid_by_club else event.bill_payer_member_id
        if not event.is_paid_by_club and creditor_id is None:
            raise AccountingValidationError(
                "Zahlweg «Mitglied» braucht ein zahlendes Mitglied."
            )
        existing_member_ids = {
            c.member_id
            for c in MemberClaim.query.filter_by(
                event_id=event.id, claim_type=ClaimType.ESSENSANTEIL,
            ).all()
        }
        created = []
        for participation in event.participations:
            if not participation.teilnahme:
                continue
            share = participation.calculated_share_rappen
            if not share or share <= 0:
                continue
            if participation.member_id == creditor_id:
                continue
            if participation.member_id in existing_member_ids:
                continue
            claim = MemberClaim(
                member_id=participation.member_id,
                creditor_member_id=creditor_id,
                claim_type=ClaimType.ESSENSANTEIL,
                event_id=event.id,
                expected_rappen=share,
                note=f'Essensanteil {event.display_date}',
            )
            db.session.add(claim)
            created.append(claim)
        db.session.commit()
        return created

    @classmethod
    def reset_claims_for_event(cls, event) -> int:
        """Unbezahlte Essensanteil-Claims eines Events löschen (BillBro-Reset).

        Posten mit Zahlungen bleiben stehen und müssen manuell geklärt werden.
        """
        claims = MemberClaim.query.filter_by(
            event_id=event.id, claim_type=ClaimType.ESSENSANTEIL,
        ).all()
        deleted = 0
        for claim in claims:
            if claim.paid_rappen == 0 and claim.status in (
                ClaimStatus.OFFEN, ClaimStatus.TEILWEISE,
            ):
                db.session.delete(claim)
                deleted += 1
        db.session.commit()
        return deleted

    @classmethod
    def create_claim_for_merch_order(cls, order) -> MemberClaim | None:
        """Merch-Claim über den Mitglieder-Preis anlegen (Spec 11.8, idempotent)."""
        existing = MemberClaim.query.filter_by(
            merch_order_id=order.id, claim_type=ClaimType.MERCH,
        ).first()
        if existing is not None:
            return existing
        if not order.total_member_price_rappen:
            return None
        claim = MemberClaim(
            member_id=order.member_id,
            claim_type=ClaimType.MERCH,
            merch_order_id=order.id,
            expected_rappen=order.total_member_price_rappen,
            note=f'Merch-Bestellung {order.order_number}',
        )
        db.session.add(claim)
        db.session.commit()
        return claim

    @classmethod
    def settle_claim(cls, claim_id: int, *, waive: bool = False) -> MemberClaim:
        """Posten manuell abschliessen: beglichen oder erlassen."""
        claim = cls.get_claim(claim_id)
        if not claim.is_open:
            raise AccountingValidationError("Dieser Posten ist bereits abgeschlossen.")
        claim.status = ClaimStatus.ERLASSEN if waive else ClaimStatus.BEGLICHEN
        claim.settled_at = datetime.utcnow()
        db.session.commit()
        return claim

    @classmethod
    def confirm_private_payment(cls, claim_id: int, creditor: Member) -> MemberClaim:
        """Privatzahler bestätigt den Eingang eines Anteils (Spec 11.6)."""
        claim = cls.get_claim(claim_id)
        if claim.creditor_member_id != creditor.id:
            raise AccountingValidationError(
                "Nur das auslegende Mitglied kann Eingänge bestätigen."
            )
        if not claim.is_open:
            raise AccountingValidationError("Dieser Posten ist bereits beglichen.")
        claim.register_payment(claim.open_rappen)
        db.session.commit()
        return claim

    @classmethod
    def get_claims_overview(cls) -> list[dict]:
        """Pro Mitglied: offene und bezahlte Beträge (Tab «Offene Posten»)."""
        claims = MemberClaim.query.order_by(MemberClaim.created_at).all()
        by_member: dict[int, dict] = {}
        for claim in claims:
            entry = by_member.setdefault(claim.member_id, {
                'member': claim.member,
                'open_rappen': 0,
                'paid_rappen': 0,
                'claims': [],
            })
            if claim.status != ClaimStatus.ERLASSEN:
                entry['open_rappen'] += claim.open_rappen
                entry['paid_rappen'] += min(claim.paid_rappen, claim.expected_rappen)
            entry['claims'].append(claim)
        return sorted(
            by_member.values(),
            key=lambda e: (-e['open_rappen'], e['member'].nachname),
        )

    # -- Budget-Vorschlag (Spec Sektion 11.11) -------------------------------

    @classmethod
    def propose_budget(cls, fiscal_year_id: int) -> dict[int, int]:
        """Budget-Vorschlag pro Konto-ID in Rappen.

        Mitgliederbeiträge: aktive Mitglieder × Jahresbeitrag.
        Übrige Konten: Vorjahres-Ist, gerundet auf CHF 10.
        """
        fy = cls.get_fiscal_year(fiscal_year_id)
        prev = FiscalYear.query.filter_by(year=fy.year - 1).first()

        proposals: dict[int, int] = {}
        if prev is not None:
            actual_rows = (
                db.session.query(Booking.account_id, db.func.sum(Booking.amount_rappen))
                .filter(Booking.fiscal_year_id == prev.id)
                .group_by(Booking.account_id)
                .all()
            )
            for account_id, total in actual_rows:
                proposals[account_id] = round((total or 0) / 1000) * 1000

        contribution_account = Account.query.filter_by(code='3000').first()
        if contribution_account is not None and fy.membership_fee_rappen:
            active_members = Member.query.filter_by(is_active=True).count()
            proposals[contribution_account.id] = (
                active_members * fy.membership_fee_rappen
            )
        return proposals

    # -- Statistik --------------------------------------------------------

    MEMBER_CONTRIBUTION_CODES = ('3000', '3015', '3020')

    @classmethod
    def get_saldo_timeline(cls, fiscal_year_id: int) -> dict:
        """Kumulierter Saldo pro Monat (Rappen) für die Linienkurve."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        bookings = (
            Booking.query.filter_by(fiscal_year_id=fy.id)
            .order_by(Booking.booking_date, Booking.id)
            .all()
        )
        monthly = [0] * 12
        for b in bookings:
            delta = b.amount_rappen if b.direction == BookingDirection.IN else -b.amount_rappen
            monthly[b.booking_date.month - 1] += delta

        cumulative = []
        running = 0
        for value in monthly:
            running += value
            cumulative.append(running)
        return {
            'labels': ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
            'values_rappen': cumulative,
        }

    @classmethod
    def get_year_comparison(cls) -> list[dict]:
        """Einnahmen/Ausgaben/Ergebnis pro Jahr (aufsteigend) für Balken und Tabelle."""
        rows = (
            db.session.query(
                FiscalYear,
                Booking.direction,
                db.func.sum(Booking.amount_rappen),
            )
            .outerjoin(Booking, Booking.fiscal_year_id == FiscalYear.id)
            .group_by(FiscalYear.id, Booking.direction)
            .all()
        )
        by_year: dict[int, dict] = {}
        for fy, direction, total in rows:
            entry = by_year.setdefault(fy.year, {
                'fiscal_year': fy,
                'year': fy.year,
                'income_rappen': 0,
                'expense_rappen': 0,
            })
            if direction == BookingDirection.IN:
                entry['income_rappen'] = total or 0
            elif direction == BookingDirection.OUT:
                entry['expense_rappen'] = total or 0
        result = []
        for year in sorted(by_year):
            entry = by_year[year]
            entry['result_rappen'] = entry['income_rappen'] - entry['expense_rappen']
            result.append(entry)
        return result

    @classmethod
    def get_member_contributions(cls, fiscal_year_id: int) -> list[Booking]:
        """Mitgliederbeitrags-Buchungen (Konten 3000/3015/3020) des Jahres."""
        return (
            Booking.query.join(Account, Account.id == Booking.account_id)
            .filter(
                Booking.fiscal_year_id == fiscal_year_id,
                Booking.direction == BookingDirection.IN,
                Account.code.in_(cls.MEMBER_CONTRIBUTION_CODES),
            )
            .order_by(Booking.booking_date, Booking.id)
            .all()
        )

    # -- Belege ---------------------------------------------------------

    @classmethod
    def get_receipt_folder_id(cls, year: int) -> str:
        """`Buchhaltung/{Jahr}/` im Shared Drive – wird bei Bedarf angelegt."""
        root_id = DriveStorageService.get_root_id()
        accounting_folder = DriveStorageService.ensure_subfolder(
            root_id, ACCOUNTING_FOLDER_NAME
        )
        return DriveStorageService.ensure_subfolder(accounting_folder, str(year))

    @classmethod
    def upload_receipt(cls, file, uploader: Member, fiscal_year_id: int,
                       suggested_account_id: int | None = None,
                       suggested_event_id: int | None = None,
                       comment: str | None = None,
                       display_name: str | None = None,
                       booking_id: int | None = None) -> Receipt:
        """Beleg nach Drive hochladen und Receipt-Datensatz anlegen.

        `file` ist ein werkzeug FileStorage. Dateiname in Drive:
        `{YYYYMMDD}_{Kommentar-Prefix}_{OriginalDateiname}`.
        """
        fy = cls.get_fiscal_year(fiscal_year_id)
        if fy.status == FiscalYearStatus.CLOSED:
            raise AccountingValidationError(
                f"Jahr {fy.year} ist abgeschlossen – keine Belege mehr möglich."
            )

        original_filename = (file.filename or '').strip() or 'Beleg'
        stem, _, extension = original_filename.rpartition('.')
        if not stem:
            stem, extension = original_filename, ''

        comment = (comment or '').strip() or None
        display_name = (display_name or '').strip() or None
        prefix_parts = [datetime.utcnow().strftime('%Y%m%d')]
        name_prefix = display_name or comment
        if name_prefix:
            prefix_parts.append(name_prefix[:COMMENT_PREFIX_MAX_LENGTH])
        prefix_parts.append(stem)
        filename_stem = '_'.join(prefix_parts)

        target_booking = None
        if booking_id:
            target_booking = db.session.get(Booking, booking_id)
            if target_booking is None:
                raise AccountingValidationError("Buchung nicht gefunden.")
            if target_booking.fiscal_year.status != FiscalYearStatus.OPEN:
                raise AccountingValidationError(
                    "Jahr ist nicht offen – Beleg kann nicht direkt verknüpft werden."
                )

        payload = file.read()
        mime_type = file.mimetype or 'application/octet-stream'
        folder_id = cls.get_receipt_folder_id(fy.year)

        drive_meta = DriveStorageService.upload_bytes(
            payload=payload,
            filename_stem=filename_stem,
            drive_folder_id=folder_id,
            mime_type=mime_type,
            extension=extension or None,
            actor=uploader,
        )

        try:
            receipt = Receipt(
                drive_file_id=drive_meta['id'],
                drive_file_name=drive_meta.get('name') or filename_stem,
                display_name=display_name,
                drive_folder_id=folder_id,
                file_type=mime_type,
                uploader_id=uploader.id,
                suggested_account_id=suggested_account_id,
                suggested_event_id=suggested_event_id,
                comment=comment,
                booking_id=target_booking.id if target_booking else None,
            )
            db.session.add(receipt)
            db.session.commit()
        except Exception:
            db.session.rollback()
            DriveStorageService._safe_delete_drive_file(
                DriveStorageService._build_drive(), drive_meta['id']
            )
            raise
        return receipt

    @staticmethod
    def get_receipt(receipt_id: int) -> Receipt:
        receipt = db.session.get(Receipt, receipt_id)
        if receipt is None:
            raise AccountingValidationError("Beleg nicht gefunden.")
        return receipt

    @classmethod
    def attach_receipt_to_booking(cls, receipt_id: int, booking_id: int) -> Receipt:
        receipt = cls.get_receipt(receipt_id)
        booking = db.session.get(Booking, booking_id)
        if booking is None:
            raise AccountingValidationError("Buchung nicht gefunden.")
        if booking.fiscal_year.status != FiscalYearStatus.OPEN:
            raise AccountingValidationError(
                "Jahr ist nicht offen – Beleg kann nicht verknüpft werden."
            )
        receipt.booking_id = booking.id
        db.session.commit()
        return receipt

    @staticmethod
    def get_inbox() -> list[Receipt]:
        """Ungebuchte Belege (Inbox des Schatzmeisters)."""
        return (
            Receipt.query.filter(Receipt.booking_id.is_(None))
            .order_by(Receipt.uploaded_at.desc())
            .all()
        )

    @staticmethod
    def get_receipts_for_member(member: Member) -> list[Receipt]:
        return (
            Receipt.query.filter_by(uploader_id=member.id)
            .order_by(Receipt.uploaded_at.desc())
            .all()
        )

    @staticmethod
    def get_receipts_with_filters(booked: bool | None = None,
                                  event_id: int | None = None) -> list[Receipt]:
        query = Receipt.query
        if booked is True:
            query = query.filter(Receipt.booking_id.isnot(None))
        elif booked is False:
            query = query.filter(Receipt.booking_id.is_(None))
        if event_id:
            query = query.filter_by(suggested_event_id=event_id)
        return query.order_by(Receipt.uploaded_at.desc()).all()

    @staticmethod
    def download_receipt(receipt: Receipt) -> tuple[bytes, str, str]:
        """Bytes, MIME, Dateiname aus Drive."""
        return DriveStorageService.download_file_by_id(receipt.drive_file_id)

    # -- Export -----------------------------------------------------------

    @classmethod
    def export_csv(cls, fiscal_year_id: int) -> str:
        """CSV (UTF-8 mit BOM, Semikolon) für Excel."""
        fy = cls.get_fiscal_year(fiscal_year_id)
        bookings = (
            Booking.query.filter_by(fiscal_year_id=fy.id)
            .order_by(Booking.booking_date, Booking.id)
            .all()
        )
        lines = ['Datum;Beschreibung;Konto-Code;Konto-Name;Richtung;Betrag CHF']
        for b in bookings:
            description = b.description.replace(';', ',')
            chf = f"{b.amount_rappen // 100}.{b.amount_rappen % 100:02d}"
            lines.append(
                f"{b.booking_date.strftime('%d.%m.%Y')};{description};"
                f"{b.account.code};{b.account.name};{b.direction_display};{chf}"
            )
        return '\ufeff' + '\r\n'.join(lines) + '\r\n'

    # -- Revisions-Kommentare ----------------------------------------------

    @classmethod
    def add_revision_comment(cls, booking_id: int | None,
                             fiscal_year_id: int | None,
                             author: Member, text: str) -> RevisionComment:
        text = (text or '').strip()
        if not text:
            raise AccountingValidationError("Kommentar darf nicht leer sein.")
        if booking_id is None and fiscal_year_id is None:
            raise AccountingValidationError(
                "Kommentar braucht eine Buchung oder ein Geschäftsjahr."
            )
        comment = RevisionComment(
            booking_id=booking_id,
            fiscal_year_id=fiscal_year_id,
            author_id=author.id,
            text=text,
        )
        db.session.add(comment)
        db.session.commit()
        return comment

    @staticmethod
    def resolve_comment(comment_id: int) -> RevisionComment:
        comment = db.session.get(RevisionComment, comment_id)
        if comment is None:
            raise AccountingValidationError("Kommentar nicht gefunden.")
        comment.resolved = True
        db.session.commit()
        return comment

    @staticmethod
    def get_comments_for_year(fiscal_year_id: int) -> list[RevisionComment]:
        """Alle Kommentare des Jahres (direkt am Jahr oder an dessen Buchungen)."""
        return (
            RevisionComment.query.outerjoin(
                Booking, RevisionComment.booking_id == Booking.id
            )
            .filter(
                db.or_(
                    RevisionComment.fiscal_year_id == fiscal_year_id,
                    Booking.fiscal_year_id == fiscal_year_id,
                )
            )
            .order_by(RevisionComment.created_at.desc())
            .all()
        )
