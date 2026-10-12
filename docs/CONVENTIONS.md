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
- **Externe Storage-/API-Services** (Beispiel: `DriveStorageService`) muessen idempotente Schreib-Operationen anbieten und bei API-Fehlern explizite Service-Errors werfen (z.B. `DriveError`, `DriveValidationError`). Routes catchen die Service-Errors, mappen sie auf Flash-Meldungen und committen DB-Aenderungen erst nach erfolgreichem externen Call (Drive zuerst, DB danach – siehe `docs/capabilities/drive.md` Sektion 7.2).
- **Feature-Flags**: neue, schaltbare Capabilities laufen hinter einem Boolean-Flag in `Config` (Beispiel: `DRIVE_FEATURE_ENABLED`). Routes / UI pruefen das Flag explizit; ohne Flag liefern Routes 404, UI rendert eine «Bald verfuegbar»-Card.

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

- **Permissions explizit**: `@login_required`, `current_user.is_admin()`, `@admin_required` (nur `Role.ADMIN`), oder `@verein_member_required` für **Lesenden** Zugriff ausgewählter Admin-Oberflächen durch alle aktiven Mitglieder (siehe `backend/routes/admin.py`; schreibende/sensitive Routen bleiben `@admin_required`)
- **Event-Sichtbarkeit**: Listen/Queries über `Event.apply_audience_filter(query, member)`; Einzelzugriff über `event.is_visible_to(member)` (sonst 403). iCal-Feeds mit `for_calendar=True` (nur `vorstandsmitglied`, kein Admin-Shortcut). `VORSTANDSSITZUNG` erzwingt `audience=board` via `Event.resolve_audience_for_type`.
- **Manuelle RSVP-Erinnerungen**: beide Einstiege in `events.py` nutzen nach
  der Sichtbarkeitsprüfung `_can_send_participation_reminders(event)`:
  Organisator dieses Events oder `is_admin()`. Vorstandsstatus oder eine andere
  Vereinsfunktion allein gewähren kein Versandrecht. Ablehnung erreicht den
  Versandservice nicht; API antwortet 403, Formularroute leitet mit Fehlermeldung
  zum Event zurück. Login und CSRF bleiben erforderlich.
- **BillBro / GGL**: `event.supports_ggl` (nur `MONATSESSEN`) steuert Schätzung, Rangliste und `GGLService.calculate_event_points`. Ohne GGL (z.B. Vorstandssitzung): nur Ess-Typ + Rechnungssplit.
- **CSRF**: standardmässig an. `@csrf.exempt` nur für externe Webhooks **mit** Signature-Check
- **Rate-Limit**: für Login, Reset, Upload, sensitive Endpoints, **öffentlicher iCal-Feed** (`60/min` pro Feed-Token via `key_func` auf den URL-Token)
- **Cron-Testzugang**: `/cron/test` nur bei `CRON_TEST_ENABLED is True` und gültigem
  `CRON_AUTH_TOKEN` ausführen; auch lokal keine Ausnahme für fehlendes Token.
  Die Verfügbarkeit wird nicht aus `ENV`, `DEBUG` oder `TESTING` abgeleitet.
  Basis-/Produktions-/Testkonfiguration sperren, `DevelopmentConfig` schaltet
  explizit frei. Reguläre Cron-Endpunkte behalten ihre bestehende Auth-Regel.
- **Form-Handling**: WTForms (`FlaskForm`), `validate_on_submit()`-Pattern
- **Öffentliche Hitlist** (`GET /restaurants`): Query `page`, `q` (Textsuche), `sort` mit `rating` (Standard), `recent` oder `name`; Verarbeitung über `get_landing_restaurant_table`.
- **Flash-Nachrichten** auf Deutsch
- **Redirect nach POST** (PRG-Pattern)
- **Step-Up bei sensiblen Aktionen**: `SecurityService.check_step_up_access()` + ggf. `require_step_up`-Decorator
- **Step-Up-Sitzungsbindung**: Ablaufzeit und `sensitive_access_member_id` müssen
  zum angemeldeten Mitglied passen. Legacy-Freigaben ohne Mitgliedsbindung,
  fremde, abgelaufene oder fehlerhafte Freigaben werden verworfen. Erteilen nur
  im authentifizierten Kontext; vorhandene konfigurierte TTL bleibt massgeblich.
  Flask-Login-Signale für Login, Logout und Cookie-Wiederanmeldung entfernen
  diese Freigabe sowie `2fa_secret`, `pending_2fa_user_id` und `step_up_next`.
  Keine vollständige Session-Löschung: andere Einstellungen bleiben erhalten.

### Rückkehrziel bei der Anmeldung

Passwort- und MFA-Login prüfen Rückkehrziele mit
`SecurityService.local_return_target()`: nur root-relative Pfade, keine externen
oder protokollrelativen Adressen, Backslashes oder Steuerzeichen im Pfad.
Erlaubte Query/Fragment-Anteile bleiben erhalten. Das Ziel wird beim erfolgreichen
Passwortschritt zusammen mit `pending_2fa_user_id` als `pending_2fa_next` gespeichert.
MFA liest nur dieses Ziel, keine neue `next`-Angabe. Ein neuer Login-Aufruf verwirft
den bisherigen MFA-Vorgang; Login/Logout/Cookie-Wiederanmeldung entfernen auch
das Rückkehrziel. Fehlgeschlagene MFA-Eingaben erhalten es für die Wiederholung.
Step-Up verwendet denselben Prüfer für Query-`next`, Formular-`next`,
Formular-`next_url` und gespeichertes `step_up_next` in dieser Priorität. Der erste
zulässige Wert gewinnt; ungültige gespeicherte Werte werden sofort entfernt.
Bei Fehlern bleibt nur ein geprüftes Ziel erhalten, bei Erfolg wird es verbraucht.
Das gilt auch bei noch gültiger Step-Up-Freigabe.
`ratings.rate_event` prüft Query-/Formular-`next` vor sämtlichen Erfolgs- und
Fehlerverzweigungen mit demselben Prüfer; das erste zulässige Ziel (Query vor
Formular) gewinnt. Ohne gültiges Ziel bleiben die bisherigen Event-Tabs und
Anker massgeblich. `admin.update_order_status` sowie Dokument-Umbenennen,
Verschieben, Archivieren und Wiederherstellen prüfen freies Formular-`next`
ebenfalls mit `local_return_target()`. Ungültige Ziele nutzen den bestehenden
internen Fallback. Feste Erfolgsziele nach Archivieren/Wiederherstellen bleiben
unverändert; der Prüfer ersetzt keine Zugriffsprüfung der Zielroute.

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
- **Mitgliedsdaten Admin/Profil**: `nationalitaet` und `zimmerwunsch` nutzen dieselben Listen `NATIONALITAET_CHOICES` und `ZIMMERWUNSCH_CHOICES` aus `backend.models.member`. In `admin.edit_member` werden von der Liste abweichende gespeicherte Werte (Legacy-Freitext) temporär als Zusatz-Choice ergänzt (`_select_choices_with_legacy`), damit Speichern ohne Datenverlust möglich ist.
- **Komplexe Module**: alle Forms eines Moduls in einer eigenen Datei `backend/forms/<modul>.py` (Beispiel: `backend/forms/accounting.py`), kein Inline-Definieren im Route-File. Reine State-Mutations via POST-Button (z.B. Jahresfreigabe) laufen als einfache HTML-Forms mit manuellem `csrf_token()` (Validierung via `flask_wtf.csrf.validate_csrf`).

### Optionale Zahlen in Mitgliedsdaten

Profil, Mitgliederanlage und Admin-Bearbeitung verwenden die Feldfabriken in
`backend/forms/member_fields.py`. Grösse/Gewicht sind ganze Zahlen von 0 bis
2147483647 (technische PostgreSQL-INTEGER-Grenze); Schuhgrösse ist eine endliche,
nicht negative Gleitkommazahl. Leere Eingaben inklusive reiner Leerzeichen
werden `None`; Null bleibt eine Zahl. Keine zusätzlichen fachlichen Grenzwerte.
Konvertierung und Prüfung erfolgen in WTForms vor jeder Mutation. Routes
übernehmen die typisierten `.data`-Werte ohne nachträgliches `int()`/`float()`.
Bei Fehlern bleibt das Formular mit seinen Eingaben stehen. Admin verwendet
weiterhin TextInput, das Profil seine bisherigen Zahlenfelder.

### Profil-Mailadresse: Konflikte behandeln

`ProfileForm.validate_email` prüft vor jeder Profiländerung die belegte Adresse
anderer Konten (einschliesslich deaktivierter). Das eigene Konto ist ausgenommen.
Der Vergleich folgt der bestehenden DB-/Login-Schreibweise, ohne neue
Normalisierung. Der Profil-Commit behandelt zusätzlich `IntegrityError` mit
vollständigem Rollback. Nur ein danach nachweisbarer Adresskonflikt wird am
E-Mail-Feld gemeldet; andere Integritätsfehler erhalten eine neutrale Meldung.
Formularwerte bleiben erhalten, DB-/SQL-Fehlertexte werden nicht ausgegeben.
Dies gilt auch für Administration/Anlage: `MemberForm.validate_email` verwendet
nur die von der Edit-Route gesetzte `editing_member_id` als Ausnahme; bei Anlage
keine Ausnahme. `_commit_member_form()` schützt den ersten Mitglieds-Commit.
Bei Konflikten keine Folgeaktionen (sensible Daten, Onboarding-Token, Mail, Audit).
Fehler nach erfolgreichem ersten Commit bleiben ein separater Onboarding-Vertrag.

### Letzten aktiven Admin bewahren

`admin.edit_member` prüft nach WTForms und vor jeder Mutation über
`_validate_admin_continuity`, dass eine Herabstufung oder Deaktivierung keinen
Bestand von null aktiven Admins erzeugt. Ein inaktiver Admin oder aktives
gewöhnliches Mitglied zählt nicht als Ersatz. Ablehnung ist ein Feldfehler an
Rolle/Aktivstatus; das gesamte Formular bleibt ungespeichert und ohne Erfolgs-Audit.
Eine Übergabe funktioniert durch vorherige Vergabe an ein anderes aktives Mitglied.

Alle Adminzeilen werden in ID-Reihenfolge mit `FOR UPDATE` gesperrt. Danach
werden handelndes und bearbeitetes Mitglied neu gelesen und aktive Admins neu
gezählt (PostgreSQL READ COMMITTED). Verlorene Adminrechte oder Deaktivierung
des Handelnden führen vor Mutation zu 403. Sperren bleiben bis zum vorhandenen
Commit/Rollback bestehen. SQLite prüft die Abläufe, nicht parallele PostgreSQL-
Sperren. Direkte DB-/Skriptänderungen werden dadurch nicht abgesichert.

## Passwortlinks bei Zugangsaenderungen

Normaler Passwortwechsel, Passwort-Reset per Link, Aktivierung und Admin-
Passwortreset sperren die Mitgliedszeile mit
`SecurityService.lock_credential_member()` vor der Aenderung. Beim normalen
Wechsel wird das aktuelle Passwort erst anhand dieses frischen Stands geprüft.
Reset/Aktivierung verwenden vor Mutation erneut `_resolve_auth_token(...,
lock=True)`: frischer Tokenzweck, Ablauf, Verwendung und aktives Mitglied.

`SecurityService.invalidate_password_links()` entwertet offene `PASSWORD_RESET`-
und `ONBOARDING`-Links desselben Mitglieds in derselben Transaktion wie das neue
Passwort. Der Helfer committet nicht selbst. `used_at` kennzeichnet sowohl
Verbrauch als auch Widerruf; bestehende Links werden dadurch vom Resolver
abgelehnt. Kein globales Löschen von Tokens oder Aendern anderer Tokenzwecke.

Bei Ausgabe eines neuen Passwort-/Aktivierungslinks sperrt `_issue_auth_token`
dieselbe Mitgliedszeile und ersetzt nur ältere Links desselben Zwecks. Neue
Anforderung nach erfolgreichem Wechsel bleibt möglich. Ausgabe und Verbrauch
verwenden unveränderte Tokenformate/Fristen. PostgreSQL-Sperren müssen vor
Veröffentlichung parallel getestet werden; lokale SQLite-Tests genügen dafür
nicht. Allgemeiner Sitzungswiderruf und MFA-Resetlinks bleiben separate Verträge.

## Google-Adressverifikation

Ausgabe und Verbrauch von `GOOGLE_EMAIL_VERIFY` ausschliesslich über
`GoogleEmailVerificationService`. Die bestehende `AuthToken.token_hash`-Spalte
(128 Zeichen) enthält zwei SHA-256-Hexwerte: Lookup-Hash des zufälligen Tokens
und Bindungshash über Token, Null-Trennzeichen und konkrete Google-Adresse.
Keine Adresse im Link, kein rohes Token in der DB. Andere Tokenzwecke verwenden
weiter ihr bisheriges Format. Ungebundene alte Google-Links werden abgelehnt;
das Mitglied muss einen neuen Link anfordern. Gültigkeit bleibt sieben Tage.

Ausgabe sperrt die Mitgliedszeile, ersetzt unbenutzte Links desselben Zwecks
und speichert Adressänderung samt neuem Token in einer Transaktion. Verbrauch
liest Mitglied und Token nach der Mitgliedssperre neu, prüft Adresse/Zweck,
Aktivstatus/Ablauf/Verbrauch und setzt `used_at` zusätzlich bedingt. Erst nach
erfolgreichem Commit wird eine Einladung möglich. PostgreSQL verwendet dafür
`FOR UPDATE`; SQLite-Tests ersetzen keinen echten Paralleltest.

Externe Mail-/Drive-Aufrufe bekommen einen unveränderlichen Adress-Snapshot,
keinen nach Commit erneut geladenen Member mit möglicherweise neuer Adresse.
Widerruf alter Drive-Rechte und Wiederaufnahme fehlgeschlagener Zustellungen/
Einladungen sind separate Verträge (A-089), keine atomare DB-/Drive-Transaktion.

## Logging

- **Modul-Logger**: `logger = logging.getLogger(__name__)` am Datei-Anfang
- **Niemals `print()`** in Backend-Code; nutze `logger.info/warning/error/debug`
- **Sensitive Daten nicht loggen**: keine Passwörter, kein verschlüsselter Inhalt, keine API-Keys
- **In Routes**: `current_app.logger.info(...)` ist auch ok für Request-Kontext
- **Exception-Logging**: Exception-Text/Traceback nur, wenn keine vertraulichen Werte
  enthalten sein können. HTTP-Fehler können URLs mit API-Schlüsseln enthalten.
- **Auth-/Places-Logs**: nur feste Vorgangsnamen, Ergebnisse und sichere numerische
  Metadaten (HTTP-Status, Anzahl). Keine MFA-Geheimnisse oder Codes, Passwortformulare,
  Request-Dictionaries, Rückkehr-URLs, Places-Parameter, vollständigen API-Antworten
  oder ungefilterten Fehlertexte. Auch Logger-Argumente müssen geheimnisfrei sein;
  blosses Verschieben auf DEBUG genügt nicht. Tests prüfen Erfolgs- und Fehlerpfade.

## Audit-Log

Sensible Aktionen werden geloggt via `SecurityService.log_audit_event(...)`. Pflicht für:

- Login / Logout
- 2FA aktivieren / deaktivieren / Backup-Code-Verwendung
- Passwort-Änderung / Reset
- Member-Daten ändern (admin-seitig)
- Sensitive-Daten lesen (Step-Up)
- Externe Aktionen (Payment-Webhook, etc.)

Aktionen sind in `AuditAction`-Enum definiert. Bei neuer Aktion: Enum erweitern.

## MFA-Reset-Bestätigung

`auth.reset_2fa` verändert bei GET/HEAD weder MFA noch Backup-Codes oder Token.
Erst ein gültiger POST mit CSRF und ausdrücklicher Formularbestätigung führt
den bestehenden Reset aus. Tokenzweck, Ablauf, Verbrauch und aktives Konto
werden bei jedem Aufruf erneut geprüft. Die Bestätigungsantwort verwendet
`Cache-Control: no-store` und `Referrer-Policy: no-referrer`.

## MFA-Backup-Codes

MFA-Backup-Codes behalten gesalzene Hashes. Zur Prüfung immer
`SecurityService.check_backup_code()` verwenden, niemals einen neu erzeugten
Hash auf Gleichheit suchen. `consume_backup_code()` prüft ausschliesslich aktive
Codes des betreffenden Mitglieds und verbraucht den Treffer mit bedingtem UPDATE
(`used_at` und `revoked_at` weiterhin NULL). Erst nach genau einer geänderten
Zeile und erfolgreichem Commit darf die Route anmelden. Bei Schreibfehlern
Rollback ohne Anmeldung; im Audit nur die Code-ID, nie Code oder Hash.

## Encryption (Fernet)

Sensible Felder werden via `SecurityService.encrypt_json()` / `decrypt_json()` ver-/entschlüsselt. Verwendung:

- `MemberSensitive` (z.B. AHV, IBAN – falls erfasst)
- `MemberMFA.totp_secret_encrypted`
- Optional bei neuen sensitiven Feldern

**Niemals** den `CRYPTO_KEY` rotieren in Production – würde alle Daten korrupten. Falls Rotation wirklich nötig: geplante Migration mit Re-Encryption pro Feld.

`MemberSensitive` wird vor Anzeige **und vor dem Überschreiben** über
`SecurityService.read_member_sensitive()` gelesen. Entschlüsselungs-/Formatfehler
erzeugen `SensitiveDataReadError`, niemals leere Ersatzwerte oder eine Löschung.
Routes zeigen die bestehende technische Fehlerseite (HTTP 500) mit sicherer
Flash-Meldung, ohne sensibles Bearbeitungsformular. Nur ein tatsächlich fehlender
Datensatz erlaubt die leere Ersterfassung. Logs enthalten weder Payload, Schlüssel,
Klartext noch ursprüngliche Exception. Audit-Logging liegt ausserhalb der
Lesefehlerbehandlung. Regression: `tests/routes/test_sensitive_data_preservation.py`.

## Templates

- **Englische Klassennamen** (BEM, siehe `docs/UI.md`)
- **Deutsche Texte** in HTML
- **Macros** für wiederverwendbare Fragmente in `templates/partials/`
- **Layouts** via Jinja-Vererbung von `base.html`
- **Keine Inline-Styles** (siehe `docs/UI.md`)
- **CSRF-Token** in Formularen: `{{ form.hidden_tag() }}`

## Tests

- **pytest** als Framework (`pytest.ini` im Repo-Root, `tests/`-Verzeichnis parallel zu `backend/`)
- Tests in `tests/services/`, `tests/routes/`, `tests/models/` parallel zur `backend/`-Struktur
- Fixtures fuer DB, App-Context, Test-User (bei Bedarf in `tests/conftest.py`)
- **Mindestens** fuer neue Services: Unit-Tests fuer Sanitization-/Validierungs-Funktionen
  und kritische Edge-Cases. Beispiel: `tests/services/test_drive_storage.py`
  testet `sanitize_drive_filename` und `sanitize_svg_bytes` (Pflicht, da Marketing-Use-Case
  SVGs aus dem Web zulaesst).
- Bei externen API-Calls: Mocking, kein Live-Hit gegen Drittsystem in Unit-Tests.
- **Route-Smoke**: bei komplexen Jinja-Templates mindestens ein GET mit Test-DB-Daten,
  wenn die Seite z. B. Relationen (`Event` im Upload-Modal auf `/docs/`) rendert –
  sonst zerspringt die UI in Production/Dev erst zur Laufzeit (pytest-Beispiel:
  `tests/routes/test_docs_smoke.py`).

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
