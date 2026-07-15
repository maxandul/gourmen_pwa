"""Accounting models – Buchhaltungsmodul (Phase 4).

Spezifikation: docs/capabilities/accounting.md Sektion 4.
Beträge immer in Rappen als Integer, niemals Float.
"""

from datetime import datetime
from enum import Enum

from backend.extensions import db


class FiscalYearStatus(Enum):
    OPEN = 'open'
    IN_REVIEW = 'in_review'
    CLOSED = 'closed'


class AccountKind(Enum):
    INCOME = 'income'
    EXPENSE = 'expense'


class BookingDirection(Enum):
    IN = 'in'
    OUT = 'out'


class BankTransactionStatus(Enum):
    PENDING = 'pending'
    BOOKED = 'booked'
    IGNORED = 'ignored'


class ClaimType(Enum):
    MITGLIEDERBEITRAG = 'MITGLIEDERBEITRAG'
    ESSENSANTEIL = 'ESSENSANTEIL'
    MERCH = 'MERCH'
    REISE = 'REISE'
    SONSTIGES = 'SONSTIGES'


class ClaimStatus(Enum):
    OFFEN = 'offen'
    TEILWEISE = 'teilweise'
    BEGLICHEN = 'beglichen'
    ERLASSEN = 'erlassen'


class FiscalYear(db.Model):
    """Geschäftsjahr mit Status-Lifecycle: open → in_review → closed."""

    __tablename__ = 'fiscal_years'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(FiscalYearStatus), default=FiscalYearStatus.OPEN, nullable=False)
    closed_at = db.Column(db.DateTime)
    # Jahresbeitrag pro Mitglied in Rappen (2026: 84000) – Basis für
    # Beitrags-Claims und Budget-Vorschlag (Spec Sektion 11.7 / 11.11).
    membership_fee_rappen = db.Column(db.Integer)

    budget_entries = db.relationship(
        'BudgetEntry', backref='fiscal_year', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<FiscalYear {self.year}: {self.status.value}>'

    @property
    def is_open(self):
        return self.status == FiscalYearStatus.OPEN

    @property
    def is_in_review(self):
        return self.status == FiscalYearStatus.IN_REVIEW

    @property
    def is_closed(self):
        return self.status == FiscalYearStatus.CLOSED

    @property
    def status_display(self):
        names = {
            FiscalYearStatus.OPEN: 'Offen',
            FiscalYearStatus.IN_REVIEW: 'In Prüfung',
            FiscalYearStatus.CLOSED: 'Abgeschlossen',
        }
        return names.get(self.status, self.status.value)

    @property
    def abschluss_phase(self):
        """Workflow-Phase für den Abschluss-Tab: 1 = open, 2 = in_review, 3 = closed."""
        phases = {
            FiscalYearStatus.OPEN: 1,
            FiscalYearStatus.IN_REVIEW: 2,
            FiscalYearStatus.CLOSED: 3,
        }
        return phases[self.status]


class Account(db.Model):
    """Konto aus dem Kontenplan (E/A-Rechnung)."""

    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.Enum(AccountKind), nullable=False)
    group_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    budget_entries = db.relationship('BudgetEntry', backref='account')

    def __repr__(self):
        return f'<Account {self.code}: {self.name}>'

    @property
    def kind_display(self):
        names = {
            AccountKind.INCOME: 'Einnahme',
            AccountKind.EXPENSE: 'Ausgabe',
        }
        return names.get(self.kind, self.kind.value)


class BudgetEntry(db.Model):
    """Budget-Wert pro Konto und Geschäftsjahr."""

    __tablename__ = 'budget_entries'
    __table_args__ = (
        db.UniqueConstraint('fiscal_year_id', 'account_id', name='uq_budget_year_account'),
    )

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('accounts.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    amount_rappen = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='SET NULL'),
        nullable=True,
    )
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BudgetEntry fy={self.fiscal_year_id} acc={self.account_id}: {self.amount_rappen}>'

    @property
    def amount_chf(self):
        return self.amount_rappen / 100


class Booking(db.Model):
    """Buchung im Journal (E/A-Rechnung). Beträge in Rappen, niemals Float."""

    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    booking_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount_rappen = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.Enum(BookingDirection), nullable=False)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('accounts.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id', ondelete='SET NULL'),
        nullable=True, index=True,
    )
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='SET NULL'),
        nullable=True, index=True,
    )
    payment_ref = db.Column(db.String(255))
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fiscal_year = db.relationship('FiscalYear', backref='bookings')
    account = db.relationship('Account', backref='bookings')
    event = db.relationship('Event', backref='bookings')
    member = db.relationship('Member', foreign_keys=[member_id], backref='bookings_assigned')
    creator = db.relationship('Member', foreign_keys=[created_by])
    receipts = db.relationship('Receipt', backref='booking')

    def __repr__(self):
        return f'<Booking {self.id}: {self.description} ({self.amount_rappen} Rp)>'

    @property
    def amount_chf(self):
        return self.amount_rappen / 100

    @property
    def is_income(self):
        return self.direction == BookingDirection.IN

    @property
    def signed_amount_rappen(self):
        """Einnahmen positiv, Ausgaben negativ – für Saldo-Berechnungen."""
        return self.amount_rappen if self.is_income else -self.amount_rappen

    @property
    def direction_display(self):
        names = {
            BookingDirection.IN: 'Einnahme',
            BookingDirection.OUT: 'Ausgabe',
        }
        return names.get(self.direction, self.direction.value)


class Receipt(db.Model):
    """Beleg in Google Drive. booking_id NULL = ungebucht (Inbox)."""

    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey('bookings.id', ondelete='SET NULL'),
        nullable=True, index=True,
    )
    drive_file_id = db.Column(db.String(255), nullable=False)
    drive_file_name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120))
    drive_folder_id = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    uploader_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    suggested_account_id = db.Column(
        db.Integer,
        db.ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
    )
    suggested_event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id', ondelete='SET NULL'),
        nullable=True,
    )
    comment = db.Column(db.Text)
    ocr_data = db.Column(db.JSON)

    uploader = db.relationship('Member', backref='receipts_uploaded')
    suggested_account = db.relationship('Account', foreign_keys=[suggested_account_id])
    suggested_event = db.relationship('Event', foreign_keys=[suggested_event_id])

    def __repr__(self):
        return f'<Receipt {self.id}: {self.drive_file_name}>'

    @property
    def is_booked(self):
        return self.booking_id is not None

    @property
    def status_display(self):
        return 'Verbucht' if self.is_booked else 'Ausstehend'

    @property
    def label(self):
        """Kurzer Anzeige-Name fuer Listen: display_name > Kommentar > Dateiname."""
        return self.display_name or self.comment or self.drive_file_name


class RevisionComment(db.Model):
    """Revisionskommentar – zu einer Buchung oder allgemein zum Jahr."""

    __tablename__ = 'revision_comments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey('bookings.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    author_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
    )
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved = db.Column(db.Boolean, default=False, nullable=False)

    booking = db.relationship('Booking', backref='revision_comments')
    fiscal_year = db.relationship('FiscalYear', backref='revision_comments')
    author = db.relationship('Member')

    def __repr__(self):
        return f'<RevisionComment {self.id} by {self.author_id}>'


class RevisionApproval(db.Model):
    """Formale Revisionsbestätigung eines Geschäftsjahres."""

    __tablename__ = 'revision_approvals'

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='CASCADE'),
        unique=True, nullable=False,
    )
    reviewer_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
    )
    approved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_drive_id = db.Column(db.String(255))

    fiscal_year = db.relationship('FiscalYear', backref=db.backref('revision_approval', uselist=False))
    reviewer = db.relationship('Member')

    def __repr__(self):
        return f'<RevisionApproval fy={self.fiscal_year_id} by {self.reviewer_id}>'


class BankStatementImport(db.Model):
    """Ein hochgeladener ZKB-Kontoauszug (CSV). Spec Sektion 11.2 / 11.3."""

    __tablename__ = 'bank_statement_imports'

    id = db.Column(db.Integer, primary_key=True)
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    imported_by = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
    )
    imported_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    row_count = db.Column(db.Integer, nullable=False, default=0)
    new_count = db.Column(db.Integer, nullable=False, default=0)
    duplicate_count = db.Column(db.Integer, nullable=False, default=0)

    fiscal_year = db.relationship('FiscalYear', backref='bank_imports')
    importer = db.relationship('Member')
    transactions = db.relationship(
        'BankTransaction', backref='statement_import', cascade='all, delete-orphan',
        foreign_keys='BankTransaction.import_id',
    )

    def __repr__(self):
        return f'<BankStatementImport {self.id}: {self.filename}>'

    @property
    def pending_count(self):
        return sum(1 for tx in self.transactions if tx.is_pending)

    @property
    def booked_count(self):
        return sum(
            1 for tx in self.transactions
            if tx.status == BankTransactionStatus.BOOKED
        )

    @property
    def can_delete(self):
        """Löschbar nur solange keine Zeile verbucht ist."""
        return self.booked_count == 0


class BankTransaction(db.Model):
    """Eine Zeile aus dem ZKB-Kontoauszug (inkl. Detail-Zeilen von Sammelbuchungen).

    Dedup über line_key: zkb_ref bzw. '{parent_ref}#{index}' bei Detail-Zeilen.
    """

    __tablename__ = 'bank_transactions'

    id = db.Column(db.Integer, primary_key=True)
    import_id = db.Column(
        db.Integer,
        db.ForeignKey('bank_statement_imports.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    zkb_ref = db.Column(db.String(50), index=True)  # NULL bei Detail-Zeilen
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('bank_transactions.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    line_key = db.Column(db.String(60), unique=True, nullable=False, index=True)
    booked_date = db.Column(db.Date, nullable=False)
    valuta = db.Column(db.Date)
    amount_rappen = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.Enum(BookingDirection), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='CHF')
    amount_original = db.Column(db.String(30))  # z.B. 'EUR 922.25'
    buchungstext = db.Column(db.String(500), nullable=False)
    zahlungszweck = db.Column(db.String(500))
    details = db.Column(db.String(500))
    status = db.Column(
        db.Enum(BankTransactionStatus),
        default=BankTransactionStatus.PENDING, nullable=False, index=True,
    )
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey('bookings.id', ondelete='SET NULL'),
        nullable=True, index=True,
    )
    suggested_account_id = db.Column(
        db.Integer, db.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True,
    )
    suggested_member_id = db.Column(
        db.Integer, db.ForeignKey('members.id', ondelete='SET NULL'), nullable=True,
    )
    raw_json = db.Column(db.JSON)

    parent = db.relationship('BankTransaction', remote_side=[id], backref='detail_lines')
    booking = db.relationship('Booking', backref=db.backref('bank_transaction', uselist=False))
    suggested_account = db.relationship('Account', foreign_keys=[suggested_account_id])
    suggested_member = db.relationship('Member', foreign_keys=[suggested_member_id])

    def __repr__(self):
        return f'<BankTransaction {self.line_key}: {self.amount_rappen} Rp {self.direction.value}>'

    @property
    def amount_chf(self):
        return self.amount_rappen / 100

    @property
    def is_pending(self):
        return self.status == BankTransactionStatus.PENDING

    @property
    def is_income(self):
        return self.direction == BookingDirection.IN

    @property
    def is_collective(self):
        """Sammelbuchungs-Parent mit Detail-Zeilen — wird nicht selbst verbucht."""
        return bool(self.detail_lines)

    @property
    def status_display(self):
        names = {
            BankTransactionStatus.PENDING: 'Offen',
            BankTransactionStatus.BOOKED: 'Verbucht',
            BankTransactionStatus.IGNORED: 'Ignoriert',
        }
        return names.get(self.status, self.status.value)


class MemberBankAlias(db.Model):
    """Gelernte Zuordnung Auftraggeber-Text → Mitglied.

    CSV-Namen stimmen nicht 1:1 mit der Mitglieder-DB überein
    (Zweitnamen, Grossschreibung, Mueller/Müller, Adress-Wechsel).
    """

    __tablename__ = 'member_bank_aliases'
    __table_args__ = (
        db.UniqueConstraint('member_id', 'alias_text', name='uq_member_alias'),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    alias_text = db.Column(db.String(255), nullable=False, index=True)  # normalisiert
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    member = db.relationship('Member', backref='bank_aliases')

    def __repr__(self):
        return f'<MemberBankAlias {self.member_id}: {self.alias_text}>'


class MemberClaim(db.Model):
    """Offener Posten: Forderung gegenüber einem Mitglied.

    creditor_member_id NULL = Gläubiger ist der Verein (läuft über Buchhaltung).
    creditor_member_id gesetzt = privates Auslegen (läuft NICHT über Buchhaltung).
    """

    __tablename__ = 'member_claims'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    creditor_member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    claim_type = db.Column(db.Enum(ClaimType), nullable=False, index=True)
    fiscal_year_id = db.Column(
        db.Integer,
        db.ForeignKey('fiscal_years.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    merch_order_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_orders.id', ondelete='CASCADE'),
        nullable=True, index=True,
    )
    expected_rappen = db.Column(db.Integer, nullable=False)
    paid_rappen = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(
        db.Enum(ClaimStatus), default=ClaimStatus.OFFEN, nullable=False, index=True,
    )
    settled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    note = db.Column(db.String(255))

    member = db.relationship('Member', foreign_keys=[member_id], backref='claims')
    creditor = db.relationship('Member', foreign_keys=[creditor_member_id])
    fiscal_year = db.relationship('FiscalYear', backref='claims')
    event = db.relationship('Event', backref='claims')
    merch_order = db.relationship('MerchOrder', backref='claims')

    def __repr__(self):
        return f'<MemberClaim {self.id}: {self.claim_type.value} {self.member_id} {self.status.value}>'

    @property
    def open_rappen(self):
        return max(self.expected_rappen - self.paid_rappen, 0)

    @property
    def expected_chf(self):
        return self.expected_rappen / 100

    @property
    def paid_chf(self):
        return self.paid_rappen / 100

    @property
    def open_chf(self):
        return self.open_rappen / 100

    @property
    def is_open(self):
        return self.status in (ClaimStatus.OFFEN, ClaimStatus.TEILWEISE)

    @property
    def is_club_claim(self):
        """True = Gläubiger ist der Verein (Verbuchung über die Buchhaltung)."""
        return self.creditor_member_id is None

    @property
    def type_display(self):
        names = {
            ClaimType.MITGLIEDERBEITRAG: 'Mitgliederbeitrag',
            ClaimType.ESSENSANTEIL: 'Essensanteil',
            ClaimType.MERCH: 'Merch-Bestellung',
            ClaimType.REISE: 'Reise',
            ClaimType.SONSTIGES: 'Sonstiges',
        }
        return names.get(self.claim_type, self.claim_type.value)

    @property
    def status_display(self):
        names = {
            ClaimStatus.OFFEN: 'Offen',
            ClaimStatus.TEILWEISE: 'Teilweise bezahlt',
            ClaimStatus.BEGLICHEN: 'Beglichen',
            ClaimStatus.ERLASSEN: 'Erlassen',
        }
        return names.get(self.status, self.status.value)

    def register_payment(self, amount_rappen, settled=None):
        """Zahlungseingang fortschreiben; Status-Übergang offen → teilweise → beglichen."""
        self.paid_rappen += amount_rappen
        if self.paid_rappen >= self.expected_rappen:
            self.status = ClaimStatus.BEGLICHEN
            self.settled_at = settled or datetime.utcnow()
        elif self.paid_rappen > 0:
            self.status = ClaimStatus.TEILWEISE
