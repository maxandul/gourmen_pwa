"""Accounting-Forms (Phase 4) – alle Buchhaltungs-Formulare.

Spezifikation: docs/capabilities/accounting.md Sektion 3.7.
Reine State-Mutations (Jahresfreigabe, Genehmigen, Budget-Zeile) laufen
als einfache HTML-Forms mit csrf_token – nicht hier.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from decimal import Decimal, InvalidOperation

from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

MAX_BOOKING_RAPPEN = 2_147_483_647  # Existing database Integer column.


def chf_to_rappen(amount_chf) -> int:
    """Exact CHF to positive integer cents; never silently round input."""
    try:
        dec = Decimal(str(amount_chf))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('Ungültiger Betrag') from exc
    if not dec.is_finite() or dec <= 0:
        raise ValueError('Betrag muss eine endliche Zahl grösser als 0 sein')
    if dec > Decimal(MAX_BOOKING_RAPPEN) / 100:
        raise ValueError('Betrag überschreitet den unterstützten Höchstwert')
    rappen = int(dec * 100)
    if Decimal(rappen) / 100 != dec:
        raise ValueError('Bitte einen Betrag in ganzen Rappen angeben')
    return rappen


class BookingForm(FlaskForm):
    """Buchung anlegen/bearbeiten (Schatzmeister/Admin)."""

    booking_date = DateField('Datum', validators=[
        DataRequired(message='Bitte Datum angeben')
    ])
    description = StringField('Beschreibung', validators=[
        DataRequired(message='Bitte Beschreibung angeben'),
        Length(max=255),
    ])
    amount_chf = DecimalField('Betrag (CHF)', places=2, validators=[
        DataRequired(message='Bitte Betrag angeben'),
    ])
    direction = SelectField('Richtung', choices=[
        ('in', 'Einnahme'),
        ('out', 'Ausgabe'),
    ], validators=[DataRequired()])
    account_id = SelectField('Konto', coerce=int, validators=[DataRequired()])
    event_id = SelectField('Event (optional)', coerce=int, validators=[Optional()])
    member_id = SelectField('Mitglied (optional)', coerce=int, validators=[Optional()])
    submit = SubmitField('Speichern')

    fiscal_year = None

    def validate_amount_chf(self, field):
        try:
            chf_to_rappen(field.data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def validate_booking_date(self, field):
        if self.fiscal_year is not None:
            from backend.services.accounting import AccountingService, AccountingValidationError
            try:
                AccountingService.validate_booking_date(self.fiscal_year, field.data)
            except AccountingValidationError as exc:
                raise ValidationError(str(exc)) from exc

    @property
    def amount_rappen(self):
        """Betrag als Integer-Rappen (niemals Float speichern)."""
        return chf_to_rappen(self.amount_chf.data)


class ReceiptUploadForm(FlaskForm):
    """Beleg einreichen (alle aktiven Mitglieder)."""

    file = FileField('Beleg (Foto oder PDF)', validators=[
        FileRequired(message='Bitte Datei auswählen')
    ])
    display_name = StringField('Anzeige-Name (optional)', validators=[
        Optional(), Length(max=120),
    ])
    suggested_account_id = SelectField(
        'Kategorie-Vorschlag (optional)', coerce=int, validators=[Optional()]
    )
    suggested_event_id = SelectField(
        'Event (optional)', coerce=int, validators=[Optional()]
    )
    booking_id = SelectField(
        'Bestehende Buchung (optional)', coerce=int, validators=[Optional()]
    )
    comment = TextAreaField('Kommentar (optional)', validators=[
        Optional(), Length(max=500),
    ])
    submit = SubmitField('Weiter')


class BankImportForm(FlaskForm):
    """ZKB-Kontoauszug (CSV) hochladen (Schatzmeister/Admin)."""

    file = FileField('ZKB-Kontoauszug (CSV)', validators=[
        FileRequired(message='Bitte CSV-Datei auswählen')
    ])
    submit = SubmitField('Importieren')


class RevisionCommentForm(FlaskForm):
    """Revisionskommentar zum Jahr oder zu einer Buchung."""

    text = TextAreaField('Kommentar', validators=[
        DataRequired(message='Kommentar darf nicht leer sein'),
        Length(max=2000),
    ])
    submit = SubmitField('Kommentar speichern')


class AccountForm(FlaskForm):
    """Konto anlegen/bearbeiten (Admin)."""

    code = StringField('Konto-Nummer', validators=[
        DataRequired(message='Bitte Konto-Nummer angeben'),
        Length(max=10),
    ])
    name = StringField('Name', validators=[
        DataRequired(message='Bitte Namen angeben'),
        Length(max=100),
    ])
    kind = SelectField('Art', choices=[
        ('income', 'Einnahme'),
        ('expense', 'Ausgabe'),
    ], validators=[DataRequired()])
    group_name = StringField('Kontengruppe', validators=[
        Optional(), Length(max=100),
    ])
    is_active = BooleanField('Aktiv', default=True)
    submit = SubmitField('Speichern')
