"""BankImportService – ZKB-Kontoauszug-Import (Phase 4b).

Authoritative Spezifikation: docs/capabilities/accounting.md Sektion 11.

Parst den CSV-Export der ZKB-App, dedupliziert über die ZKB-Referenz,
splittet Sammelbuchungen in Detail-Zeilen, erzeugt Konto-/Mitglied-
Vorschläge und verbucht bestätigte Transaktionen als Bookings
(inkl. Fortschreiben der offenen Posten).
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import re
from datetime import date, datetime, timedelta

from backend.extensions import db
from backend.models.accounting import (
    Account,
    BankStatementImport,
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
from backend.models.event import BillPaidBy, Event
from backend.models.member import Member
from backend.services.accounting import (
    AccountingService,
    AccountingValidationError,
)

logger = logging.getLogger(__name__)

EXPECTED_HEADER_START = ('Datum', 'Buchungstext')

# Konto-Codes für Auto-Vorschläge (Spec Sektion 11.4) und Aufrundungen (11.5)
FEE_ACCOUNT_CODE = '6940'
MEAL_EXPENSE_ACCOUNT_CODE = '6100'
MEMBER_REFUND_ACCOUNT_CODE = '6710'
CLAIM_ACCOUNT_CODES = {
    ClaimType.MITGLIEDERBEITRAG: '3000',
    ClaimType.ESSENSANTEIL: '3310',
    ClaimType.MERCH: '3400',
    ClaimType.REISE: '3500',
    ClaimType.SONSTIGES: '3620',
}
ROUNDING_ACCOUNT_CODES = {
    ClaimType.ESSENSANTEIL: '3315',
    ClaimType.MERCH: '3410',
}

FEE_PATTERNS = (
    'kontoführung',
    'kontofuehrung',
    'gebühr zkb visa debit card',
    'gebuehr zkb visa debit card',
    'jahresgebühr',
    'jahresgebuehr',
)
CREDIT_PREFIX = 'Gutschrift Auftraggeber:'
DEBIT_PREFIXES = (
    'Belastung eBanking:',
    'Belastung Mobile Banking:',
    'Belastung:',
)
COLLECTIVE_PATTERN = re.compile(
    r'^(Belastungen|Gutschriften) eBanking \((\d+)\)', re.IGNORECASE
)
CARD_PURCHASE_PATTERN = re.compile(
    r'^(Online-)?Einkauf ZKB Visa Debit Card', re.IGNORECASE
)

_UMLAUT_MAP = str.maketrans({'ä': 'a', 'ö': 'o', 'ü': 'u', 'é': 'e', 'è': 'e', 'à': 'a'})


def normalize_bank_text(text: str) -> str:
    """Namen aus dem CSV vergleichbar machen: lowercase, Umlaut-Folding.

    Deckt «Müller» vs. «Mueller» und GROSSSCHREIBUNG ab. Nicht-Buchstaben
    werden zu Einzel-Spaces reduziert.
    """
    lowered = (text or '').lower().translate(_UMLAUT_MAP)
    lowered = lowered.replace('ae', 'a').replace('oe', 'o').replace('ue', 'u')
    return re.sub(r'[^a-z]+', ' ', lowered).strip()


def parse_chf_to_rappen(raw: str) -> int:
    """'1626.01' → 162601. Toleriert Tausender-Apostrophe."""
    cleaned = (raw or '').replace("'", '').replace('’', '').strip()
    if not cleaned:
        raise ValueError('Leerer Betrag')
    sign = -1 if cleaned.startswith('-') else 1
    cleaned = cleaned.lstrip('+-')
    whole, _, fraction = cleaned.partition('.')
    fraction = (fraction + '00')[:2]
    return sign * (int(whole or 0) * 100 + int(fraction))


class BankImportError(AccountingValidationError):
    """Fehler beim Parsen oder Verbuchen eines Kontoauszugs."""


class ParsedRow:
    """Eine geparste CSV-Zeile (Haupt- oder Detail-Zeile)."""

    def __init__(self, *, zkb_ref, booked_date, valuta, amount_rappen, direction,
                 currency, amount_original, buchungstext, zahlungszweck, details, raw):
        self.zkb_ref = zkb_ref
        self.booked_date = booked_date
        self.valuta = valuta
        self.amount_rappen = amount_rappen
        self.direction = direction
        self.currency = currency
        self.amount_original = amount_original
        self.buchungstext = buchungstext
        self.zahlungszweck = zahlungszweck
        self.details = details
        self.raw = raw
        self.detail_rows: list['ParsedRow'] = []


class BankImportService:
    """CSV-Import, Auto-Vorschläge und Verbuchung von ZKB-Transaktionen."""

    # -- Parsing ----------------------------------------------------------

    @staticmethod
    def _decode(payload: bytes) -> str:
        for encoding in ('utf-8-sig', 'cp1252'):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise BankImportError('Datei-Encoding nicht erkennbar (UTF-8 oder cp1252 erwartet).')

    @staticmethod
    def _parse_date(raw: str) -> date | None:
        raw = (raw or '').strip()
        if not raw:
            return None
        try:
            return datetime.strptime(raw, '%d.%m.%Y').date()
        except ValueError as exc:
            raise BankImportError(f'Ungültiges Datum «{raw}».') from exc

    @classmethod
    def parse_csv(cls, payload: bytes) -> list[ParsedRow]:
        """CSV in Haupt-Zeilen mit zugeordneten Detail-Zeilen parsen.

        Detail-Zeilen von Sammelbuchungen haben ein leeres Datum und keine
        eigene ZKB-Referenz; sie folgen direkt auf ihre Parent-Zeile.
        EUR-Detail-Beträge werden proportional auf den CHF-Parent verteilt.
        """
        text = cls._decode(payload)
        reader = csv.reader(io.StringIO(text), delimiter=';', quotechar='"')
        rows = [row for row in reader if any((cell or '').strip() for cell in row)]
        if not rows:
            raise BankImportError('Die Datei enthält keine Daten.')

        header = [cell.strip() for cell in rows[0]]
        if tuple(header[:2]) != EXPECTED_HEADER_START:
            raise BankImportError(
                'Unerwartetes CSV-Format – ZKB-Export mit Header '
                '«Datum;Buchungstext;…» erwartet.'
            )
        col = {name: idx for idx, name in enumerate(header)}

        def cell(row, name):
            idx = col.get(name)
            if idx is None or idx >= len(row):
                return ''
            return (row[idx] or '').strip()

        parsed: list[ParsedRow] = []
        current_parent: ParsedRow | None = None

        for row in rows[1:]:
            datum = cell(row, 'Datum')
            buchungstext = cell(row, 'Buchungstext')
            belastung = cell(row, 'Belastung CHF')
            gutschrift = cell(row, 'Gutschrift CHF')

            if not datum:
                # Detail-Zeile einer Sammelbuchung
                if current_parent is None:
                    logger.warning('Detail-Zeile ohne Parent übersprungen: %s', buchungstext)
                    continue
                betrag_detail = cell(row, 'Betrag Detail')
                if not betrag_detail:
                    continue
                whg = cell(row, 'Whg') or 'CHF'
                detail = ParsedRow(
                    zkb_ref=None,
                    booked_date=current_parent.booked_date,
                    valuta=current_parent.valuta,
                    amount_rappen=parse_chf_to_rappen(betrag_detail),
                    direction=current_parent.direction,
                    currency=whg,
                    amount_original=f'{whg} {betrag_detail}' if whg != 'CHF' else None,
                    buchungstext=buchungstext,
                    zahlungszweck=cell(row, 'Zahlungszweck'),
                    details=cell(row, 'Details'),
                    raw=row,
                )
                current_parent.detail_rows.append(detail)
                continue

            if not belastung and not gutschrift:
                # Fusszeilen / Summenzeilen ohne Betrag überspringen
                continue

            direction = BookingDirection.IN if gutschrift else BookingDirection.OUT
            main = ParsedRow(
                zkb_ref=cell(row, 'ZKB-Referenz') or None,
                booked_date=cls._parse_date(datum),
                valuta=cls._parse_date(cell(row, 'Valuta')),
                amount_rappen=parse_chf_to_rappen(gutschrift or belastung),
                direction=direction,
                currency='CHF',
                amount_original=None,
                buchungstext=buchungstext,
                zahlungszweck=cell(row, 'Zahlungszweck'),
                details=cell(row, 'Details'),
                raw=row,
            )
            parsed.append(main)
            current_parent = main if COLLECTIVE_PATTERN.match(buchungstext) else None

        for parent in parsed:
            if parent.detail_rows:
                cls._distribute_parent_amount(parent)
        return parsed

    @staticmethod
    def _distribute_parent_amount(parent: ParsedRow) -> None:
        """Detail-Beträge proportional auf den CHF-Parent-Betrag verteilen.

        Bei CHF-Details, deren Summe dem Parent entspricht, bleibt alles wie
        erfasst. Bei Fremdwährung (oder Rundungs-Differenzen) wird der
        CHF-Betrag anteilig verteilt; die letzte Zeile erhält den Rest.
        """
        detail_sum = sum(d.amount_rappen for d in parent.detail_rows)
        if detail_sum == parent.amount_rappen:
            return
        if detail_sum <= 0:
            return
        remaining = parent.amount_rappen
        for detail in parent.detail_rows[:-1]:
            share = round(parent.amount_rappen * detail.amount_rappen / detail_sum)
            if detail.currency == 'CHF':
                detail.amount_original = f'CHF {detail.amount_rappen / 100:.2f}'
            detail.amount_rappen = share
            remaining -= share
        last = parent.detail_rows[-1]
        if last.currency == 'CHF':
            last.amount_original = f'CHF {last.amount_rappen / 100:.2f}'
        last.amount_rappen = remaining

    # -- Import -----------------------------------------------------------

    @classmethod
    def import_statement(cls, file, imported_by: Member) -> BankStatementImport:
        """CSV importieren: parsen, deduplizieren, Vorschläge berechnen.

        Idempotent: bereits importierte line_keys werden gezählt und
        übersprungen. Das Geschäftsjahr wird pro Zeile aus dem Buchungsdatum
        bestimmt; der Import hängt am Jahr der neuesten Zeile.
        """
        filename = (file.filename or '').strip() or 'kontoauszug.csv'
        parsed = cls.parse_csv(file.read())
        if not parsed:
            raise BankImportError('Keine Transaktionen in der Datei gefunden.')

        newest = max(p.booked_date for p in parsed)
        fiscal_year = AccountingService.get_or_create_fiscal_year(newest.year)

        statement = BankStatementImport(
            fiscal_year_id=fiscal_year.id,
            filename=filename,
            imported_by=imported_by.id,
        )
        db.session.add(statement)
        db.session.flush()

        row_count, new_count, duplicate_count = 0, 0, 0
        for parent_row in parsed:
            row_count += 1 + len(parent_row.detail_rows)
            line_key = parent_row.zkb_ref or cls._content_key(parent_row)
            if BankTransaction.query.filter_by(line_key=line_key).first():
                duplicate_count += 1 + len(parent_row.detail_rows)
                continue

            parent_tx = cls._create_transaction(
                statement, parent_row, line_key=line_key, parent=None,
            )
            new_count += 1
            if parent_row.detail_rows:
                # Parent wird durch seine Detail-Zeilen repräsentiert
                parent_tx.status = BankTransactionStatus.IGNORED
                db.session.flush()
                for index, detail_row in enumerate(parent_row.detail_rows, start=1):
                    cls._create_transaction(
                        statement, detail_row,
                        line_key=f'{line_key}#{index}', parent=parent_tx,
                    )
                    new_count += 1

        statement.row_count = row_count
        statement.new_count = new_count
        statement.duplicate_count = duplicate_count
        db.session.commit()
        logger.info(
            'Kontoauszug %s importiert: %s Zeilen, %s neu, %s Duplikate',
            filename, row_count, new_count, duplicate_count,
        )
        return statement

    @staticmethod
    def _content_key(row: ParsedRow) -> str:
        """Deterministischer Dedup-Schlüssel für Zeilen ohne ZKB-Referenz."""
        basis = f'{row.booked_date}|{row.amount_rappen}|{row.direction.value}|{row.buchungstext}'
        return 'H' + hashlib.sha1(basis.encode('utf-8')).hexdigest()[:32]

    @classmethod
    def _create_transaction(cls, statement: BankStatementImport, row: ParsedRow,
                            *, line_key: str, parent: BankTransaction | None) -> BankTransaction:
        tx = BankTransaction(
            import_id=statement.id,
            zkb_ref=row.zkb_ref,
            parent_id=parent.id if parent else None,
            line_key=line_key,
            booked_date=row.booked_date,
            valuta=row.valuta,
            amount_rappen=row.amount_rappen,
            direction=row.direction,
            currency='CHF',
            amount_original=row.amount_original,
            buchungstext=row.buchungstext[:500],
            zahlungszweck=(row.zahlungszweck or None) and row.zahlungszweck[:500],
            details=(row.details or None) and row.details[:500],
            raw_json=row.raw,
        )
        db.session.add(tx)
        db.session.flush()
        if not (parent is None and row.detail_rows):
            cls.apply_suggestions(tx)
        return tx

    # -- Auto-Vorschläge ---------------------------------------------------

    @classmethod
    def apply_suggestions(cls, tx: BankTransaction) -> None:
        """Konto-/Mitglied-Vorschlag gemäss Spec Sektion 11.4 setzen."""
        text_lower = tx.buchungstext.lower()

        if any(pattern in text_lower for pattern in FEE_PATTERNS):
            tx.suggested_account_id = cls._account_id_by_code(FEE_ACCOUNT_CODE)
            return

        member = cls.match_member(tx)
        if member is not None:
            tx.suggested_member_id = member.id

        if tx.direction == BookingDirection.IN and member is not None:
            claim = cls.match_open_claim(member, tx.amount_rappen)
            if claim is not None:
                tx.suggested_account_id = cls._account_id_by_code(
                    CLAIM_ACCOUNT_CODES[claim.claim_type]
                )
                return
            # Mitglied erkannt, kein passender Posten: wahrscheinlich Beitrag
            tx.suggested_account_id = cls._account_id_by_code(
                CLAIM_ACCOUNT_CODES[ClaimType.MITGLIEDERBEITRAG]
            )
            return

        if tx.direction == BookingDirection.OUT:
            if member is not None:
                tx.suggested_account_id = cls._account_id_by_code(MEMBER_REFUND_ACCOUNT_CODE)
                return
            if CARD_PURCHASE_PATTERN.match(tx.buchungstext):
                event = cls._find_club_paid_event(tx.booked_date)
                if event is not None:
                    tx.suggested_account_id = cls._account_id_by_code(MEAL_EXPENSE_ACCOUNT_CODE)

    @staticmethod
    def _account_id_by_code(code: str) -> int | None:
        account = Account.query.filter_by(code=code, is_active=True).first()
        return account.id if account else None

    @staticmethod
    def _find_club_paid_event(booked_date: date) -> Event | None:
        """Event mit Zahlweg Vereinskonto in ±3 Tagen um das Buchungsdatum."""
        window_start = datetime(booked_date.year, booked_date.month, booked_date.day)
        candidates = (
            Event.query.filter(
                Event.bill_paid_by == BillPaidBy.VEREINSKONTO,
                Event.datum >= window_start - timedelta(days=3),
                Event.datum <= window_start + timedelta(days=4),
            )
            .order_by(Event.datum.desc())
            .all()
        )
        return candidates[0] if candidates else None

    # -- Mitglied-Matching ---------------------------------------------------

    @classmethod
    def extract_counterparty(cls, tx: BankTransaction) -> str | None:
        """Auftraggeber/Empfänger aus dem Buchungstext extrahieren."""
        text = tx.buchungstext
        if text.startswith(CREDIT_PREFIX):
            return text[len(CREDIT_PREFIX):].strip()
        for prefix in DEBIT_PREFIXES:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
        if tx.parent_id is not None:
            # Detail-Zeile: Buchungstext ist direkt die Gegenpartei
            return text
        return None

    @classmethod
    def match_member(cls, tx: BankTransaction) -> Member | None:
        """Mitglied über gelernte Aliase, sonst über DB-Namen matchen."""
        counterparty = cls.extract_counterparty(tx)
        if not counterparty:
            return None
        haystack = normalize_bank_text(f'{counterparty} {tx.details or ""}')
        if not haystack:
            return None

        for alias in MemberBankAlias.query.all():
            if alias.alias_text and alias.alias_text in haystack:
                return alias.member

        for member in Member.query.filter_by(is_active=True).all():
            vorname = normalize_bank_text(member.vorname)
            nachname = normalize_bank_text(member.nachname)
            if vorname and nachname and vorname in haystack and nachname in haystack:
                return member
        return None

    @staticmethod
    def learn_alias(member_id: int, counterparty_text: str) -> None:
        """Alias aus bestätigter Zuordnung lernen (idempotent)."""
        normalized = normalize_bank_text(counterparty_text)
        if not normalized:
            return
        exists = MemberBankAlias.query.filter_by(
            member_id=member_id, alias_text=normalized
        ).first()
        if exists is None:
            db.session.add(MemberBankAlias(member_id=member_id, alias_text=normalized))

    @staticmethod
    def match_open_claim(member: Member, amount_rappen: int) -> MemberClaim | None:
        """Offenen Vereins-Posten des Mitglieds finden (Betrag exakt vor Teilzahlung)."""
        open_claims = (
            MemberClaim.query.filter(
                MemberClaim.member_id == member.id,
                MemberClaim.creditor_member_id.is_(None),
                MemberClaim.status.in_((ClaimStatus.OFFEN, ClaimStatus.TEILWEISE)),
            )
            .order_by(MemberClaim.created_at)
            .all()
        )
        # Exakter offener Betrag zuerst (z.B. Essensanteil), sonst ältester Posten
        for claim in open_claims:
            if claim.open_rappen == amount_rappen:
                return claim
        for claim in open_claims:
            if claim.claim_type == ClaimType.MITGLIEDERBEITRAG:
                return claim
        return open_claims[0] if open_claims else None

    # -- Verbuchen -----------------------------------------------------------

    @classmethod
    def get_transaction(cls, tx_id: int) -> BankTransaction:
        tx = db.session.get(BankTransaction, tx_id)
        if tx is None:
            raise BankImportError('Transaktion nicht gefunden.')
        return tx

    @classmethod
    def book_transaction(cls, tx_id: int, *, account_id: int,
                         member_id: int | None = None,
                         event_id: int | None = None,
                         claim_id: int | None = None,
                         booked_by: Member) -> Booking:
        """Bestätigte Transaktion verbuchen.

        Erzeugt eine Booking (payment_ref = line_key), schreibt eine
        zugeordnete Claim fort und verbucht Überzahlungen als
        ausserordentliche Einnahme (Spec 11.5).
        """
        tx = cls.get_transaction(tx_id)
        if not tx.is_pending:
            raise BankImportError('Transaktion ist bereits verarbeitet.')
        if tx.is_collective:
            raise BankImportError(
                'Sammelbuchung wird über ihre Detail-Zeilen verbucht.'
            )

        fiscal_year = AccountingService.get_or_create_fiscal_year(tx.booked_date.year)
        if fiscal_year.status != FiscalYearStatus.OPEN:
            raise BankImportError(
                f'Jahr {fiscal_year.year} ist nicht offen – keine Buchungen möglich.'
            )

        claim = None
        if claim_id:
            claim = db.session.get(MemberClaim, claim_id)
            if claim is None:
                raise BankImportError('Offener Posten nicht gefunden.')
            if not claim.is_club_claim:
                raise BankImportError(
                    'Private Posten laufen nicht über die Vereinsbuchhaltung.'
                )
            if not claim.is_open:
                raise BankImportError('Dieser Posten ist bereits beglichen.')
            if member_id is None:
                member_id = claim.member_id

        description = cls._booking_description(tx)
        main_amount = tx.amount_rappen
        rounding_amount = 0
        if claim is not None and tx.direction == BookingDirection.IN:
            overpay = tx.amount_rappen - claim.open_rappen
            rounding_code = ROUNDING_ACCOUNT_CODES.get(claim.claim_type)
            if overpay > 0 and rounding_code:
                main_amount = claim.open_rappen
                rounding_amount = overpay

        booking = AccountingService.create_booking(
            fiscal_year_id=fiscal_year.id,
            booking_date=tx.booked_date,
            description=description,
            amount_rappen=main_amount,
            direction=tx.direction,
            account_id=account_id,
            event_id=event_id or (claim.event_id if claim else None),
            member_id=member_id,
            created_by=booked_by,
            payment_ref=tx.line_key,
        )

        if rounding_amount > 0:
            rounding_account_id = cls._account_id_by_code(
                ROUNDING_ACCOUNT_CODES[claim.claim_type]
            )
            if rounding_account_id is None:
                raise BankImportError('Aufrundungs-Konto fehlt im Kontenplan.')
            AccountingService.create_booking(
                fiscal_year_id=fiscal_year.id,
                booking_date=tx.booked_date,
                description=f'{description} (Aufrundung)',
                amount_rappen=rounding_amount,
                direction=BookingDirection.IN,
                account_id=rounding_account_id,
                event_id=event_id or (claim.event_id if claim else None),
                member_id=member_id,
                created_by=booked_by,
                payment_ref=tx.line_key,
            )

        if claim is not None:
            claim.register_payment(tx.amount_rappen)

        if member_id and tx.direction == BookingDirection.IN:
            counterparty = cls.extract_counterparty(tx)
            if counterparty:
                cls.learn_alias(member_id, counterparty)

        tx.status = BankTransactionStatus.BOOKED
        tx.booking_id = booking.id
        db.session.commit()
        return booking

    @classmethod
    def ignore_transaction(cls, tx_id: int) -> BankTransaction:
        tx = cls.get_transaction(tx_id)
        if not tx.is_pending:
            raise BankImportError('Transaktion ist bereits verarbeitet.')
        tx.status = BankTransactionStatus.IGNORED
        db.session.commit()
        return tx

    @classmethod
    def reopen_transaction(cls, tx_id: int) -> BankTransaction:
        """Ignorierte Transaktion zurück auf pending (kein Booking-Undo)."""
        tx = cls.get_transaction(tx_id)
        if tx.status != BankTransactionStatus.IGNORED or tx.is_collective:
            raise BankImportError('Nur ignorierte Zeilen können zurückgeholt werden.')
        tx.status = BankTransactionStatus.PENDING
        db.session.commit()
        return tx

    @staticmethod
    def _booking_description(tx: BankTransaction) -> str:
        parts = [tx.zahlungszweck or tx.buchungstext]
        if tx.amount_original:
            parts.append(f'({tx.amount_original})')
        return ' '.join(part for part in parts if part)[:255]

    # -- Abfragen -------------------------------------------------------------

    @staticmethod
    def get_imports() -> list[BankStatementImport]:
        return (
            BankStatementImport.query
            .order_by(BankStatementImport.imported_at.desc())
            .all()
        )

    @staticmethod
    def get_statement(import_id: int) -> BankStatementImport:
        statement = db.session.get(BankStatementImport, import_id)
        if statement is None:
            raise BankImportError('Import nicht gefunden.')
        return statement

    @staticmethod
    def get_pending_transactions(import_id: int | None = None) -> list[BankTransaction]:
        query = BankTransaction.query.filter_by(status=BankTransactionStatus.PENDING)
        if import_id:
            query = query.filter_by(import_id=import_id)
        return query.order_by(BankTransaction.booked_date, BankTransaction.id).all()
