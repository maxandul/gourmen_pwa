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
