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


class FiscalYear(db.Model):
    """Geschäftsjahr mit Status-Lifecycle: open → in_review → closed."""

    __tablename__ = 'fiscal_years'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(FiscalYearStatus), default=FiscalYearStatus.OPEN, nullable=False)
    closed_at = db.Column(db.DateTime)

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
