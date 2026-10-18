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
- **Step-Up beim Zugriff auf sensible Daten**: `SecurityService.check_step_up_access()` + ggf. `require_step_up`-Decorator. Sicherheitsänderungen benötigen stattdessen den eigenen Nachweis aus U1w (siehe unten).
- **Step-Up-Sitzungsbindung**: Ablaufzeit und `sensitive_access_member_id` müssen
  zum angemeldeten Mitglied passen. Legacy-Freigaben ohne Mitgliedsbindung,
  fremde, abgelaufene oder fehlerhafte Freigaben werden verworfen. Erteilen nur
  im authentifizierten Kontext; vorhandene konfigurierte TTL bleibt massgeblich.
  Flask-Login-Signale für Login, Logout und Cookie-Wiederanmeldung entfernen
  diese Freigabe sowie `2fa_secret`, `pending_2fa_user_id` und `step_up_next`.
  Keine vollständige Session-Löschung: andere Einstellungen bleiben erhalten.

### Verpflichtender erster Passwortwechsel (U1t / A-076)

`PasswordChangeService.enforce` prüft global vor Views den bestehenden
DB-Zustand `password_changed_at IS NULL`. Auch Admins, direkte URL-Aufrufe,
API-/POST-Aufrufe und Cookie-Wiederanmeldung sind betroffen. Kein Testing-Bypass.
Alle erfolgreichen Passwort-/MFA-Loginzweige verwenden `after_login_target`:
Pflichtwechsel hat Vorrang vor `next`, MFA bleibt dem Pflichtwechsel vorgeschaltet.

Explizite Ausnahmen: `auth.change_password`, `auth.logout`, tokengebundene
`auth.reset_password`, `auth.activate`, `auth.reset_2fa`; `static`, `service_worker`,
`health` sowie Blueprints `public`, `cron`, `calendar_feed` mit ihren eigenen
Zugriffsregeln. Unbekannte Endpoints behalten 404/405. Anonyme Anfragen sind nicht
Gegenstand dieser Sperre, ihre bisherigen Login-/Tokenprüfungen bleiben bestehen.

`password_change_return` enthält Mitglieds-ID und ein mit `local_return_target`
geprüftes Ziel. Auth-Pfade werden als Zwischenziele ausgeschlossen. Das erste
gültige Ziel bleibt bestehen, spätere Seitenaufrufe überschreiben es nicht.
Nur HTML-GET/HEAD darf bei einer direkten Sperre ein Ziel setzen, keine API-
Abfragen oder Mutationen. Login/Logout/Cookie-Login löschen diesen Zustand.
Nach erfolgreichem Pflichtwechsel wird er erneut geprüft und einmalig verbraucht;
Fallback Dashboard. Freiwilliger Passwortwechsel führt weiterhin zum Profil.

HTML-GET/HEAD: 302 zum Wechsel; HTML-Mutation: 303, keine spätere Wiederholung.
JSON (`request.is_json` oder bester Accept-Typ JSON) und `/api/`: 403 mit
`error=password_change_required` und festem `next`. Sperrantworten `no-store`.
CSRF bleibt davor wirksam. Fehler beim Passwort/Commit lassen die Pflicht bestehen.
Andere Fachtests markieren ihre regulären Konten ausdrücklich mit einem
abgeschlossenen Passwortwechsel; spezielle Initialpassworttests setzen NULL.

### Sichere Rückkehrziele über Login und Step-Up

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
Bei Konflikten keine dauerhaften Folgeaktionen (sensible Daten, Onboarding-Token,
Mail, Audit). Fehler nach erfolgreichem ersten Commit folgen dem separaten
Onboarding-Vertrag U1y weiter unten.

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

## Sitzungs- und Gerätewiderruf (U1v / A-077, A-082)

`Member.auth_generation` ist eine zufällige 32-stellige Hex-Version, die
`set_password()` sowie MFA- und administrative Berechtigungsänderungen rotieren.
Alle Credential-Schreibwege halten die bestehende Mitgliedssperre bis zum Commit.
`Member.get_id()` liefert `id:generation`; Flask-Login speichert genau diesen
Wert in Session und signiertem Remember-me-Cookie. Der Loader prüft aktive
Mitgliedschaft und Version bei jedem Laden. Legacy-IDs ohne Version werden
abgelehnt; beim Rollout ist eine erneute Anmeldung erforderlich. Migrationsdefault
`0` dient nur bestehenden DB-Zeilen, nicht als Ausnahme für alte Cookies.

Passwort-/MFA-Mailreset und administrative Resets entwerten alle alten Sitzungen,
Gerätefreigaben und begonnenen MFA-Logins. Normale Passwortänderung erhält nach
Commit nur die aktuelle Sitzung plus deren gültiges Gerätevertrauen, ohne dessen
Frist zu verlängern. Selbst-Einrichtung/-Deaktivierung von MFA erhält die aktuelle
Sitzung, entwertet aber sämtliches bisheriges Gerätevertrauen. Step-Up verfällt.
Rollen-, Funktions-, Vorstands- und Aktivitätsänderungen im Adminformular rotieren
ebenfalls; gewöhnliche Profilfelder nicht. Deaktivierung entwertet zudem alte
Passwort-/Aktivierungs-/MFA-Resetlinks; Drive-Verifikation folgt ihrem eigenen Vertrag.

Passwortlogin speichert `pending_2fa_generation`. Der MFA-Schritt prüft diese
unter der Mitgliedssperre erneut; fehlende Version, Inaktivität oder inzwischen
entfernte MFA führen zurück zur Anmeldung. Nach einem Commit darf nur dieselbe
Generation angemeldet/erhalten werden, nie eine zwischenzeitlich neu geladene
Resetgeneration. Aktivierung mit bestehender MFA verlangt eine neue Anmeldung.

Gerätevertrauen entsteht ausschliesslich nach erfolgreichem TOTP im Login und
expliziter Checkbox. Es enthält Mitglied, Zugangsversion, Ausstellungs- und
Ablaufzeit, maximal **30 Tage**, ohne automatische Verlängerung. Fehlende,
abgelaufene, überlange, zukünftige oder fehlerhafte Angaben werden verworfen.
Der bisherige POST `/auth/2fa/remember-device` ohne Faktorbeweis liefert 403.
Logout lässt gültiges Gerätevertrauen für einen späteren Passwortlogin bestehen;
es ist keine aktive Sitzung. Remember-me-Cookie und laufende Sitzung behalten
ihre bestehenden separaten Fristen. Kein neuer Geräteverwaltungsbildschirm.

Step-Up bindet `sensitive_access_member_id` nun an die vollständige versionierte
Login-Identität. Testfixtures verwenden `auth_id()` für reguläre Anmeldungen;
kein Testing-Bypass im Loader. Transaktionsrollback erhält die bisherige Version.
Widerruf wirkt auf die nächste Authentifizierungsprüfung; bereits laufende
Requests werden nicht abgebrochen. Echte PostgreSQL-Paralleltests bleiben nötig.

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
nicht. Allgemeiner Sitzungswiderruf bleibt separat; MFA-Resetlinks siehe unten.

## MFA-Resetlinks bei Faktoränderungen

`SecurityService.invalidate_mfa_reset_links()` entwertet ausschliesslich offene
`MFA_RESET`-Links des Mitglieds in der aktuellen Transaktion. Erfolgreiche
Einrichtung, Selbstdeaktivierung, Mail-Reset und bestätigter Admin-Reset
verwenden diesen Helfer vor ihrem Commit. Admin-Reset entwertet auch bei bereits
deaktivierter 2FA. Andere Tokenzwecke und andere Mitglieder bleiben erhalten.

Diese Wege und die MFA-Linkausgabe verwenden dieselbe Mitgliedssperre wie die
Passwortwege. Einrichtung/Deaktivierung lesen danach den MFA-Stand neu; eine
zwischenzeitlich erfolgte Aktivierung wird nicht überschrieben. Mail-Reset
prüft den Link nach Bestätigung unter der Sperre erneut. Neue MFA-Linkausgabe
ersetzt ältere desselben Zwecks. Frist und bestehender GET-/CSRF-Vertrag aus U1k
bleiben erhalten. Kein Geräte-/Sitzungswiderruf oder vollständiges Recovery-
Verfahren dadurch abgedeckt. Echte PostgreSQL-Parallelabnahme bleibt nötig.

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

Externe Mails bekommen einen unveränderlichen Adress-Snapshot, keinen nach
Commit erneut geladenen Member mit möglicherweise neuer Adresse. Mail-Wiederaufnahme
bleibt separat. Drive-Einladungen und Widerrufe folgen dem folgenden Outbox-Vertrag.

## Dauerhafte Drive-Zugangsaufgaben (U1s / A-089)

`DriveAccessService.queue_revocation()` erfasst alte Adresse/Drive zusammen mit
Adresswechsel oder Deaktivierung, ohne eigenen Commit. Verifikation erfasst den
Invite in derselben Transaktion wie den Tokenverbrauch. `DriveAccessTask` speichert
`pending/failed/done/cancelled`, Versuche, Zeitpunkte und feste Fehlercodes.
Ausstehende Invites werden bei Wechsel/Deaktivierung verworfen; bekannte frühere
Invite-Ziele werden zusätzlich zum aktuellen Adressziel widerrufen. Deaktivierung
entwertet Google-Links und Verifikationsstatus, Reaktivierung braucht neue Verifikation.

Alle beteiligten App-Wege sperren dieselbe Mitgliedszeile. Admin-Bearbeitung sperrt
wie bisher zuerst Admins in ID-Reihenfolge, danach das Zielmitglied. Abarbeitung
liest unter der Mitgliedssperre neu und hält diese bis nach API und Commit eines
einzelnen Schritts. Widerrufe vor Invites; Fehler stoppen die Abarbeitung. Keine
selbst committenden Audit-Helfer innerhalb dieser Transaktion. Auditzeilen werden
gemeinsam mit dem Auftragsstatus gespeichert; bei Adminaktionen ist der Admin Akteur.

`DriveStorageService.apply_membership()` arbeitet nur auf dem gespeicherten Drive
und der gespeicherten Adresse, paginiert vollständig und hat keine DB-Seiteneffekte.
Fehlende Permission ist nach erfolgreicher Liste erledigt; Delete-404 erfordert
erneute Prüfung. Fehlendes Drive/API-Recht ist kein erfolgreicher Entzug. Invite-
Wiederholung prüft zuerst vorhandene Freigaben, kein blindes Create-Retry. Rohe
Fehlerantworten weder anzeigen noch speichern/loggen. Bei API-Erfolg/DB-Fehler
bleibt die Aufgabe offen und wird idempotent wiederholt.

Offene Aufgaben bleiben in `admin.index` auch ohne Drive-Feature sichtbar, nur für
Admins. Wiederholung per CSRF-geschütztem POST für aktive Admins. Fehlende Drive-ID
wird ausschliesslich mit ausdrücklicher Checkbox-Zuordnung auf das konfigurierte
Vereins-Drive gesetzt; vorhandene IDs bleiben unverändert. Kein automatischer Cron
oder neuer externer Dienst. PostgreSQL-Nebenläufigkeit und echte Drive-Fehler müssen
vor Veröffentlichung zusätzlich abgenommen werden.

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

Bei erfolgreicher MFA-Einrichtung ersetzt `replace_backup_codes()` die Codes
unter der bestehenden Mitgliedssperre: alte Codes widerrufen, zehn neue gesalzene
Hashes speichern. Der Helfer committet nicht; Faktoraktivierung, Codeersetzung
und MFA-Linkwiderruf gehören in dieselbe Transaktion. GET/HEAD erzeugen weder
MFA-Zeilen noch Backup-Codes. Andere Mitglieder bleiben unberührt.

Bewusste PRG-Ausnahme: Die bestätigte Einrichtung liefert die bestehende
Backup-Code-Ansicht direkt als POST-Antwort (`no-store`, `no-referrer`). Klartext
lebt nur im Request und in dieser Antwort, niemals in Session/Cookie oder DB.
Rendern vor Commit, Ausgabe erst danach; Fehler rollen zurück und erhalten den
Einrichtungsschlüssel für einen erneuten Versuch. Wiederholte POSTs bei aktivem
Faktor ersetzen/zeigen keine Codes. Der alte GET-Einstieg verweist nur auf den
bestehenden Weg Deaktivierung plus Neueinrichtung; keine automatische Erneuerung
bei verbrauchten Codes. Bei verlorener Antwort ist dieser Weg ebenfalls nötig.
Browser-Zurück/gespeicherte Kopien können nicht nachträglich gelöscht werden.

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

## Aktionsgebundene Identitätsbestätigung (U1w)

Für eigenen Passwortwechsel, MFA-Einrichtung/-Deaktivierung, administrative
Passwort-/MFA-Resets und Änderungen bestehender Kontoberechtigungen gilt
`ActionConfirmationService`: Passwort des Handelnden im selben POST erneut
prüfen. Ein Step-Up-Fenster ersetzt dies nicht. Der signierte Formularnachweis
bindet Aktion, versionierte handelnde Identität, zufällige Anmeldesitzungskennung,
Ziel-ID und Ziel-Zugangsversion; maximale Gültigkeit 600 Sekunden. Keine Secrets
im Nachweis, keine gespeicherte Authentifizierungsfreigabe und keine automatische
Wiederholung des POST nach Redirect. Neue Werte und Passwort kommen gemeinsam.

Vor Schreiben unter Mitgliedssperren Login-Identität und Rechte frisch prüfen.
Verlorene handelnde Identität oder Adminrechte führen direkt zu 403, ohne neue
privilegierte Formularausgabe. Adminaktionen sperren wie der Letzter-Admin-Schutz alle Admins nach ID, dann das
Ziel. Jede erfolgreiche geschützte Mutation muss die Ziel-Zugangsversion atomar
rotieren: dies ist der dauerhafte Einmalverbrauch, einschliesslich Cookie-Replay.
Bei Rollback kein Verbrauch; erneute Ausführung braucht erneut das Passwort.
Nicht auf Aktionen ohne garantierte Rotation übertragen. Fehler speichern keine
Teiländerungen; gewöhnliche Profiländerungen benötigen keinen Passwortnachweis.

`action_session` wird bei Login/Logout/Cookie-Wiederanmeldung entfernt.
Formularantworten sind `no-store`; Passwortprüfungen sind auf fünf pro Minute
je Endpoint/IP begrenzt, über den Limiter der aktuellen App (erst im Request
auflösen, damit frühe Blueprint-Imports keine uninitialisierte Extension binden).
Bestehende CSRF- und Loginprüfungen bleiben davor aktiv. Zusätzliche Pflicht-MFA
wird nicht eingeführt; Einrichtung verlangt weiterhin den neuen TOTP.
Recovery mit Einmallink bleibt separat. Mitgliederanlage/initiale Rechte und
vollständige Rollenmatrix sind mit diesem Paket noch nicht abgeschlossen.
Details und Grenzen: `initiatives/app-audit/U1W_AKTIONSBESTAETIGUNG.md`.

### Mitgliederanlage (U1x)

`member_create` bestätigt initiale Rechte mit dem aktuellen Adminpasswort im
Anlage-POST. Ohne bestehende Zielgeneration bindet der Nachweis stattdessen eine
zufällige Auftragskennung. Deren SHA-256-Hash wird als `ActionConfirmationUse`
mit dem Mitglied im ersten Commit gespeichert (eindeutiger Primärschlüssel).
Der Service committet nicht selbst. Niemals zwischen Nachweisprüfung und Anlage
separat committen oder den Verbrauch nur im Cookie speichern. GET legt keine
Verbrauchszeile an. Rollback erhält den Auftrag; nach Commit bleiben Wiederholungen
auch mit geändertem Formular und altem Cookie gesperrt. Spätere Mail-/Auditfehler
geben den Auftrag nicht wieder frei. Kein Widerruf der Adminsitzungen erforderlich.
Sitzungsbindung, 600 Sekunden Frist, Sperrreihenfolge, frische Rechteprüfung,
CSRF und Rate-Limit folgen U1w. Tabelle vor Nutzung der U1x-App migrieren;
keine Bereinigung noch gültiger Verbrauchsnachweise. Rollenmodell und bestehende
Onboarding-Folgeprobleme bleiben separat. Details: `initiatives/app-audit/U1X_MITGLIEDERANLAGE.md`.

### Onboarding-Zustellung und Wiederholung (U1y / A-139)

`OnboardingService.prepare()` erzeugt einen gehashten ONBOARDING-Token mit
`recipient_email`, `issued_generation` und `delivery_status='pending'`.
Bei Anlage werden Token, Mitglied und U1x-Verbrauch zusammen committet; bei
Wiederholung Tokenersetzung und Aktionsverbrauch zusammen. Erst danach `deliver()`.
Transport verwendet die gespeicherte Adresse, keine später neu geladene Zieladresse.
Keine Klartexttokens in DB, Session, Audit oder Fehlerlogs; keine automatische
Transportwiederholung. Neue Einladung ersetzt ältere ONBOARDING-Links, sieben Tage
gültig. Andere Tokenzwecke bleiben erhalten. Vor Aktivierung unter Mitgliedssperre
Empfänger und Zugangsversion erneut prüfen; Legacy-Links ohne Snapshots behalten
ihren bisherigen Vertrag und sind nicht Grundlage einer erneuten Einladung.

Status `accepted` bestätigt nur Maildienst-Annahme, niemals Zustellung. Ausnahme,
negatives Ergebnis oder Fehler beim Speichern werden als unbestätigt/offen
ausgewiesen. Spätes Ergebnis betrifft ausschliesslich die eigene Token-ID. Audit
und Versandstatus werden nach Transport gemeinsam gespeichert; Rollback lässt
den zuvor gesicherten Link bestehen. Ein Prozessabbruch lässt `pending` für die
manuelle Wiederaufnahme zurück. Allgemeine Audit-Ausfallsicherheit bleibt separat.

`admin.onboarding` ist ein separater Admin-GET/POST-Einstieg. Er benötigt für POST
frisches Passwort und den U1x-Einmalverbrauch unter `onboarding_resend`, zusätzlich
an Zielgeneration und angezeigte Adresse gebunden. Nur aktives Konto mit aktuellem
Ausgabesnapshot derselben Zugangsversion darf erneut eingeladen werden. Nach
Aktivierung/Passwortwechsel/Sicherheitswiderruf bestehende Recoverywege verwenden.
Normale Profilbearbeitung erhält dadurch keine zusätzliche Passwortabfrage.

## Service-Worker-Cache (U1z)

Private APIs, Dokumentdownloads, Tokenlinks und sonstige dynamische Antworten
sind network-only mit no-store; keine nutzerbezogenen Offline-Fachdaten.
Statische Zulassung und Antwortpruefung gelten auch beim Installieren und Lesen.
Keine globalen Cache-Lookups, keine pauschale Loeschung fremder Origin-Caches.
Details und Grenzen: ARCHITECTURE.md und U1Z_CACHE_NUTZERTRENNUNG.md im App-Audit.

## Event-/Bewertungssichtbarkeit (U1-R02)

Einzelbewertungen mit Namen/Kommentaren sind fuer alle angemeldeten Mitglieder
mit Eventzugriff lesbar (bestaetigt 18.10.2026); Teilnahme ist kein Lesekriterium.
Schreibberechtigung bleibt separat. Oeffentliche Restaurantaggregate/Teaser
beruecksichtigen nur publizierte all-Events. Interne Monatsessenstatistiken
filtern vor Aggregation nach Event.apply_audience_filter; Teilnahmequoten nach
der Sichtbarkeit des jeweiligen Mitglieds. Event-Edit setzt Formularinitialwerte
nur bei GET. Eigene Forderungen bleiben bei Sichtbarkeitsverlust erhalten;
Dashboard zeigt dann keine Eventmetadaten oder gesperrten Links.

## Beleg-/Dokumentzuordnung (U1-R03)

Eventoptionen in Dokument- und Belegformularen werden vor Limitierung ueber
Event.apply_audience_filter gefiltert. Direkte Buchungszuordnung beim Belegupload
nur fuer Schatzmeister/Admin und nur fuer offene Jahre mit sichtbarem Event;
Mitglieder reichen ohne Buchungszuordnung ein. Query-Kontext ist ebenfalls geprueft.
AccountingService prueft dieselben Grenzen vor Drive-I/O, DriveStorageService
prueft Eventzuordnung vor Upload. Vorhandene Belege in Auswahl/Kontext/Download
und Zuordnung folgen can_read_receipt: eigener Einreichender oder Finanz-/
Revisionsrolle/Admin, zusaetzlich alle verknuepften Eventberechtigungen.
Der eigene Vorgang/Status bleibt bestehen; das erteilt kein Leserecht auf ein
inzwischen gesperrtes Eventdokument. Umfassende Ordner-/Drive-Rechte folgen U1-R04.

## Begrenzte sensible Reisedokumentansicht (U1-R04a)

`admin.member_travel_documents` ist GET-only fuer aktive Reisekommissare/Admins
nach sitzungsgebundenem Step-Up. `MemberSensitiveService` prueft Rolle und aktuelle
Identitaet vor Entschluesselung und gibt nur sechs Pass-/ID-Felder ans Template.
Keine Allergien, Fuehrerscheindaten oder unbekannten JSON-Felder in dieser Ansicht.
Lesefehler bleiben ohne Mutation; Antworten inklusive Fehler/Step-Up-Redirect
tragen private/no-store und no-referrer. Bestehende eigene/Admin-Editwege bleiben.
Schatzmeister erhalten keinen Ersatz-Zugriff auf den Gesamtpayload: definierte
sensible Zahlungsfelder existieren aktuell nicht.

## Zusaetzliche Bereichsfreigaben (U1-R04b1)

MemberAreaGrant speichert Vergabe und Widerruf mit Actor/Zeitpunkt. Partial-Unique-
Index verhindert mehrere aktive Eintraege je Mitglied/Scope; neue Vergabe nach
Entzug erzeugt neue Historie. Keine automatisch vergebenen Rechte in der Migration.
AreaPermissionService erlaubt nur registrierte Scopes, aktive Konten und die
jeweilige Funktionsrolle/Admin oder aktive Einzelvergabe. travel_documents ist
zunaechst der einzige Scope; er hebt Step-Up/Feldprojektion nicht auf.
Adminverwaltung nutzt action=area_permissions, Ziel-/Sitzungs-/Aktionsbindung,
frisches Passwort und gleiche Mitgliedssperren wie U1w. Historie und rotierte
Zugangsversion committen atomar; Fehler rollen beides zurueck. Kein Secret im
Verlauf. Mitglieder lesen nur eigene Freigaben, nur Admin schreibt. Funktionsrechte
bleiben unabhaengig bestehen; Entzug einer Zusatzfreigabe entzieht kein Vereinsamt.

## Finanzbereichsfreigaben (U1-R04b2)

accounting_write impliziert accounting_read. Schatzmeister hat write, Revisor read;
gezielte Freigaben ergaenzen dies. Explizite Endpointmengen unterscheiden lesende
Ansichten/Exporte und schreibende Buchungs-/Import-/Budget-/Beitragswege. Nicht
aufgefuehrte Endpoints erhalten keine implizite Freigabe. Kontenplan/Jahresanlage
sind fuer Finanzbearbeitung erreichbar. Revisionsstatuswechsel bleiben bis R04d
bei ihren nativen Rollen, niemals durch einen allgemeinen Finanzscope freigeben.
Read-only zeigt keine Kommentar-/Bearbeitungsformulare. Vereinsnavigation und
Belegrechte nutzen denselben Scopepruefer; Eventrecht fuer Belege bleibt zusaetzlich.

## Reisebereichsfreigaben (U1-R04b3)

travel_manage gilt fuer native Reisekommissare und gezielte Freigaben. Event-
Verwaltung verwendet AreaPermissionService.can_manage_event mit aktiver Identitaet,
Audience und Admin/Organisator/Reisebereich. Auch BillBro-Controls und Polling
verwenden diese Pruefung. Ausflug-Anlage und Typwahl sind serverseitig begrenzt;
Reiseberechtigte koennen Ausfluege auch nach Selbstzuweisung nicht umtypisieren.
travel_documents bleibt ein separater Scope mit Step-Up. RSVP-Erinnerungen bleiben
Organisator/Admin, Jahresplanung und Loeschung Admin. Keine neuen UI-Klassen.

## Merchbereichsfreigaben (U1-R04b4)

merch_manage erlaubt Marketingchef, Systemadmin oder explizit Freigegebenen die
vorhandene Merchverwaltung. Alle admin.merch*-Leseseiten und Mutationswege nutzen
den gemeinsamen merch_manager_required-Pruefer. Mitgliederwege bleiben auf eigene
Bestellungen gebunden, auch fuer Bereichsverwalter. UI verwendet denselben Scope;
Vorstandsamt oder fremde Funktionsrechte genuegen nicht. Kein neues CMS.

## Dokumentklassifikation (U1-R04c1 Grundlage)

DocumentPolicy ordnet eine Drive-ID explizit als Datei/Ordner einer Leseebene und
einem Pflegebereich zu. Keine Namensheuristik/Altbestandsfreigabe. Unbekannte oder
ungueltige Policy ist nur fuer aktive Admins lesbar. DocumentPermissionService
prueft Datei, direkten Elternordner, Event und gleichnamige Belegreferenzen. Root
ist nur Navigation, keine Schreibfreigabe. Pflege setzt Lesen voraus. Die neuen
Scopes documents_manage/board_documents_manage sind gezielte Zusatzfreigaben.
classify prueft aktuellen aktiven Admin, erlaubte Werte und erwarteten Vorzustand;
Policy und DocumentPolicyChange bleiben in einer Caller-Transaktion. PostgreSQL-
Sperrnachweis bleibt offen. Routenbindung folgt separat in R04c2.
