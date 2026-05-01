# Code-Konventionen

Stabile Code-Standards für Gourmen PWA. Bei jeder Änderung mit anderen Pattern: erst hier prüfen, ob es schon existiert.

## Sprache & Lokalisierung

- **UI-Sprache**: Deutsch (kein Schweizer Hochdeutsch mit ß; "ss" verwenden)
- **Code-Identifiers**: Englisch (Variablennamen, Funktionsnamen, Klassennamen)
- **Kommentare im Code**: Deutsch oder Englisch, einheitlich pro Datei
- **Commit-Messages**: Deutsch oder Englisch, einheitlich pro Phase/Initiative
- **Currency**: Beträge intern in **Rappen** als `int` (kein Float für Geld!), Felder enden auf `_rappen`

## Service-Layer-Pattern

Externe Integrationen und komplexe Business-Logik leben in `backend/services/<name>.py` als Klassen mit `@staticmethod` oder `@classmethod`-Methoden.

### Vorlage

```python
# backend/services/<name>.py

import logging
from flask import current_app

logger = logging.getLogger(__name__)


class <Name>Service:
    """Wrapper around <external service> / <business domain>."""

    @staticmethod
    def some_action(param: str) -> dict:
        """Do something. Return structured result, log errors."""
        try:
            # Configuration aus current_app.config
            api_key = current_app.config.get('SOME_API_KEY')
            if not api_key:
                logger.warning("API key not configured, skipping action")
                return {'success': False, 'reason': 'not_configured'}

            # Tatsächliche Aktion
            result = ...

            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"Action failed: {e}")
            return {'success': False, 'error': str(e)}
```

### Regeln

- **Keine Geschäftslogik in Routes** außer Permission-Checks und Form-Validierung
- **Keine direkten externen API-Calls in Routes** – immer über Service
- **Strukturierte Rückgabe** (Dict mit `success`, `data` o.ä.) statt rohem API-Response
- **Errors loggen, nicht crashen** außer bei wirklich kritischen Fehlern (z.B. `CRYPTO_KEY` fehlt)
- **Konfiguration aus `current_app.config`** lesen, nicht direkt aus `os.environ`
- **Transaktionale E-Mails** nur über `MailService` (`RESEND_API_KEY` gesetzt → Resend/HTTPS, sonst SMTP)

## Routes / Blueprints

### Vorlage

```python
# backend/routes/<area>.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from backend.extensions import db, csrf, limiter
from backend.services.<name>_service import <Name>Service

bp = Blueprint('<area>', __name__)


@bp.route('/list')
@login_required
def list_view():
    """Liste mit Permission-Filter."""
    if current_user.is_admin():
        items = Item.query.all()
    else:
        items = Item.query.filter_by(visibility=Visibility.MEMBER).all()
    return render_template('<area>/list.html', items=items)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per minute", methods=['POST'])
def create():
    form = ItemForm()
    if form.validate_on_submit():
        result = ItemService.create_from_form(form, current_user)
        if result['success']:
            flash('Erfolgreich angelegt', 'success')
            return redirect(url_for('<area>.list_view'))
        flash(result.get('error', 'Fehler beim Anlegen'), 'error')
    return render_template('<area>/new.html', form=form)


@bp.route('/api/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    """Externer Webhook (z.B. Stripe). Signature-Verifikation Pflicht."""
    if not <Name>Service.verify_signature(request):
        return '', 401
    return <Name>Service.handle_webhook(request.get_json()), 200
```

### Regeln

- **Permissions explizit**: `@login_required`, `current_user.is_admin()`-Check, oder `@admin_required`-Decorator wo verwendet
- **CSRF**: standardmässig an. `@csrf.exempt` nur für externe Webhooks **mit** Signature-Check
- **Rate-Limit**: für Login, Reset, Upload, sensitive Endpoints
- **Form-Handling**: WTForms (`FlaskForm`), `validate_on_submit()`-Pattern
- **Flash-Nachrichten** auf Deutsch
- **Redirect nach POST** (PRG-Pattern)
- **Step-Up bei sensiblen Aktionen**: `SecurityService.check_step_up_access()` + ggf. `require_step_up`-Decorator

## Models

### Vorlage

```python
from datetime import datetime
from enum import Enum
from backend.extensions import db


class ItemKind(Enum):
    A = 'A'
    B = 'B'


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    
    # Required fields
    title = db.Column(db.String(200), nullable=False)
    kind = db.Column(db.Enum(ItemKind), nullable=False)

    # Foreign Keys mit explizitem ondelete
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False, index=True,
    )

    # Optional / nullable
    notes = db.Column(db.Text)

    # Money in Rappen
    amount_rappen = db.Column(db.Integer)

    # Soft-Delete
    deleted_at = db.Column(db.DateTime)

    # Timestamps (immer last)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

### Regeln

- **Tabellennamen**: Snake-Case Plural (`members`, `events`, `event_ratings`)
- **Enums**: Python `Enum`-Class als `db.Enum(MyEnum)`
- **Beträge**: immer `int` (Rappen), niemals Float
- **Foreign Keys**: explizit mit `ondelete=` (CASCADE, SET NULL, RESTRICT)
- **Soft-Delete**: via `deleted_at` (nullable DateTime), nicht via Boolean-Flag
- **Timestamps**: `created_at`, `updated_at` (auto via `onupdate=`)
- **Indexes**: auf häufig gefilterte Felder (`email`, FK-Felder, Suche)
- **Properties statt Methoden** für read-only Berechnungen ohne Argumente

### Migrationen

- **Eine Migration = eine logische Änderung**
- **Eigener Commit** für Migrations-Datei, nie zusammen mit Code-Änderungen
- **Reversibel** (downgrade-Funktion ausfüllen)
- **Lokal getestet** vor Push (lokales `flask db upgrade && flask db downgrade && flask db upgrade`)
- **Major Schema-Änderungen**: vorher Backup, mit User absprechen

## Forms (WTForms / Flask-WTF)

```python
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email


class MyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    role = SelectField('Rolle', choices=[
        ('MEMBER', 'Mitglied'),
        ('ADMIN', 'Admin'),
    ], validators=[DataRequired()])
    submit = SubmitField('Speichern')
```

- **Labels Deutsch**, mit Großbuchstaben am Anfang
- **Validators explizit**, niemals `optional()` ohne Begründung
- **Choices als Tuple** `(value, label)`, value matcht Enum-Werten
- **Submit-Button am Ende** als `SubmitField`

## Logging

- **Modul-Logger**: `logger = logging.getLogger(__name__)` am Datei-Anfang
- **Niemals `print()`** in Backend-Code; nutze `logger.info/warning/error/debug`
- **Sensitive Daten nicht loggen**: keine Passwörter, kein verschlüsselter Inhalt, keine API-Keys
- **In Routes**: `current_app.logger.info(...)` ist auch ok für Request-Kontext
- **Exception-Logging**: `logger.error(f"...: {e}", exc_info=True)` wenn Stack-Trace nützlich

## Audit-Log

Sensible Aktionen werden geloggt via `SecurityService.log_audit_event(...)`. Pflicht für:

- Login / Logout
- 2FA aktivieren / deaktivieren / Backup-Code-Verwendung
- Passwort-Änderung / Reset
- Member-Daten ändern (admin-seitig)
- Sensitive-Daten lesen (Step-Up)
- Externe Aktionen (Payment-Webhook, etc.)

Aktionen sind in `AuditAction`-Enum definiert. Bei neuer Aktion: Enum erweitern.

## Encryption (Fernet)

Sensible Felder werden via `SecurityService.encrypt_json()` / `decrypt_json()` ver-/entschlüsselt. Verwendung:

- `MemberSensitive` (z.B. AHV, IBAN – falls erfasst)
- `MemberMFA.totp_secret_encrypted`
- Optional bei neuen sensitiven Feldern

**Niemals** den `CRYPTO_KEY` rotieren in Production – würde alle Daten korrupten. Falls Rotation wirklich nötig: geplante Migration mit Re-Encryption pro Feld.

## Templates

- **Englische Klassennamen** (BEM, siehe `docs/UI.md`)
- **Deutsche Texte** in HTML
- **Macros** für wiederverwendbare Fragmente in `templates/partials/`
- **Layouts** via Jinja-Vererbung von `base.html`
- **Keine Inline-Styles** (siehe `docs/UI.md`)
- **CSRF-Token** in Formularen: `{{ form.hidden_tag() }}`

## Tests

Aktuell kein automatisches Test-Setup. Wenn neue Initiative Tests braucht:

- **pytest** als Framework
- Tests in `tests/` parallel zur `backend/`-Struktur
- Fixtures für DB, App-Context, Test-User
- Mindestens: Service-Layer-Tests + kritische Routes (Login, Webhooks)

## Imports

```python
# 1. Standard-Library
import os
from datetime import datetime

# 2. Third-Party
from flask import Blueprint, render_template
from sqlalchemy import text

# 3. Lokal
from backend.extensions import db
from backend.models.member import Member
from backend.services.security import SecurityService
```

Reihenfolge: Standard → Third-Party → Lokal. Keine Mixed-Imports innerhalb eines Blocks.

## Code-Style

- **PEP 8** als Basis
- **Zeilenlänge**: 100 Zeichen weich, 120 hart
- **Type Hints** wo sie helfen, kein Zwang
- **Docstrings** für public-Methoden in Services und nicht-triviale Funktionen
- **Keine kommentierte Code-Blöcke** im Repo (Git zeigt History)
- **Keine narrativen Kommentare** (`# Increment counter`); nur warum, nicht was

## Fehlerhandling in Production

- **`/health`** Endpoint zeigt App-Health (DB-Connect-Test)
- **Fehler-Templates** in `templates/errors/` (404, 500, 403)
- **App-Boot ohne DB möglich** (siehe `app.py` Fallback-App), damit Healthchecks bei DB-Down zumindest melden können
