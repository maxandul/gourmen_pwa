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
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from wtforms.validators import DataRequired, Length, NumberRange, Optional

RAPPEN_STEP = 5  # 0.05 CHF


def chf_to_rappen(amount_chf) -> int:
    """CHF → Rappen (Integer), auf 5 Rappen gerundet."""
    if amount_chf is None:
        raise ValueError('Betrag fehlt')
    try:
        dec = Decimal(str(amount_chf)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('Ungültiger Betrag') from exc
    rappen = int(dec * 100)
    snapped = int(round(rappen / RAPPEN_STEP) * RAPPEN_STEP)
    if snapped < RAPPEN_STEP:
        raise ValueError('Betrag muss mindestens 0.05 CHF sein')
    return snapped


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
        NumberRange(min=0.01, message='Betrag muss grösser als 0 sein'),
    ])
    direction = SelectField('Richtung', choices=[
        ('in', 'Einnahme'),
        ('out', 'Ausgabe'),
    ], validators=[DataRequired()])
    account_id = SelectField('Konto', coerce=int, validators=[DataRequired()])
    event_id = SelectField('Event (optional)', coerce=int, validators=[Optional()])
    member_id = SelectField('Mitglied (optional)', coerce=int, validators=[Optional()])
    submit = SubmitField('Speichern')

    @property
    def amount_rappen(self):
        """Betrag als Integer-Rappen (niemals Float speichern)."""
        return chf_to_rappen(self.amount_chf.data)


class ReceiptUploadForm(FlaskForm):
    """Beleg einreichen (alle aktiven Mitglieder)."""

    file = FileField('Beleg (Foto oder PDF)', validators=[
        FileRequired(message='Bitte Datei auswählen')
    ])
    suggested_account_id = SelectField(
        'Kategorie-Vorschlag (optional)', coerce=int, validators=[Optional()]
    )
    suggested_event_id = SelectField(
        'Event (optional)', coerce=int, validators=[Optional()]
    )
    comment = TextAreaField('Kommentar (optional)', validators=[
        Optional(), Length(max=500),
    ])
    submit = SubmitField('Weiter')


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
