# Phase 1 – Mail-Infrastruktur (Resend)

**Status**: pending  
**Aufwand**: ~0.5 Tag (4 Stunden)  
**Branch**: `phase/01-modules-mail`

## Ziel

Transaktionale E-Mails aus der App versenden können, mit klarem Service-Layer und Templates. Ist Schlüssel-Investition: schaltet Phase 2 (Login-Reset), Phase 4 (Buchungs-Bestätigungen), Phase 6 (Payment-Quittungen), Phase 7 (Mail-Fallback) frei.

## Pre-Conditions

- Phase 0 abgeschlossen
- `RESEND_API_KEY` und `RESEND_FROM_EMAIL` in Railway gesetzt
- Domain mit verifiziertem DKIM bei Resend
- Branch `phase/01-modules-mail` von `master` erstellt

## Tasks

### 1. Dependency

- [ ] `resend` Python-SDK in `requirements.txt` aufnehmen
  - Aktuelle stabile Version pinnen (z.B. `resend==2.x.x`)
- [ ] `pip install -r requirements.txt` lokal

### 2. Service-Layer

Datei `backend/services/mail.py`:

- [ ] Klasse `MailService` mit folgenden Methoden:
  - [ ] `send(to: str | list, subject: str, html: str, text: str | None = None, tags: dict | None = None) -> dict`
  - [ ] Liest `RESEND_API_KEY` und `RESEND_FROM_EMAIL` aus `current_app.config`
  - [ ] Test-Modus: wenn `RESEND_API_KEY` leer, Mail nur loggen statt senden
  - [ ] Errors werden geloggt, nicht geworfen (Mail-Versand ist „best effort")
  - [ ] Strukturierte Rückgabe: `{'success': bool, 'message_id': str | None, 'error': str | None}`
- [ ] Optional: Idempotency-Key per Aufruf (wenn Resend das unterstützt)

### 3. Templates

- [ ] Verzeichnis `templates/emails/` anlegen
- [ ] `templates/emails/base.html` (Layout mit Header/Footer in Vereinsfarben)
  - Inline-CSS (E-Mail-Clients) statt externe Stylesheets
  - Logo eingebettet via Cloudflare-CDN-URL oder als CID
  - Vereinsfarben aus Logo-Tokens
- [ ] `templates/emails/test.html` (Smoke-Test-Template)

### 4. Test-Endpoint (Admin-only)

- [ ] Neue Route in `backend/routes/admin.py` oder eigener Mini-Blueprint:
  - [ ] `GET /admin/mail/test`
  - [ ] `@login_required` + Admin-Check
  - [ ] Sendet Test-Mail an `current_user.email`
  - [ ] Zeigt Erfolg/Fehler im Flash
  - [ ] Audit-Log-Eintrag

### 5. Konfiguration

- [ ] `backend/config.py`: `RESEND_API_KEY`, `RESEND_FROM_EMAIL` aus ENV lesen
- [ ] `env.example`: neue Variablen dokumentieren

### 6. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: Resend in „Externe Services"-Tabelle Status auf `aktiv`
- [ ] `docs/CONVENTIONS.md`: nichts zwingend (Service-Layer-Pattern existiert schon)

## Acceptance-Criteria

- [ ] `MailService.send(...)` funktioniert lokal mit echtem Resend-Key
- [ ] `/admin/mail/test` schickt erfolgreich Mail an Admin
- [ ] Im Test-Modus (kein API-Key) wird Mail geloggt statt gesendet
- [ ] Mail kommt mit korrekter Absender-Adresse `noreply@gourmen.ch` an
- [ ] Mail-Layout (base.html) sieht in Gmail + Apple Mail korrekt aus
- [ ] Audit-Log enthält Test-Mail-Aktion
- [ ] Code-Review-tauglich, keine harten Secrets im Code
- [ ] Tests grün (falls Test-Setup existiert)

## Out of Scope

- Kein Passwort-Reset (kommt Phase 2)
- Kein Onboarding-Mail-Flow (kommt Phase 2)
- Kein Mail-Empfang
- Keine Templates für noch nicht existierende Module
- Keine Mass-Mail / Newsletter-Funktion

## Cursor-Agent-Briefing

```
Branch: phase/01-modules-mail
Doc: docs/initiatives/modules-and-hosting/PHASE_01_MAIL.md

Pre-Flight:
- AGENTS.md lesen
- docs/CONVENTIONS.md lesen (Service-Layer-Pattern)
- docs/ARCHITECTURE.md lesen
- docs/initiatives/modules-and-hosting/README.md lesen
- Phase-0 muss abgeschlossen sein, Resend-API-Key in Railway gesetzt

Implementiere Phase 1 (Mail-Infrastruktur via Resend) gemäss Phasen-Doc:
- Halte dich strikt an Tasks und Acceptance-Criteria
- Nichts darüber hinaus implementieren (Out of Scope strikt)
- Service-Layer-Pattern verwenden (siehe docs/CONVENTIONS.md)
- Folge .cursor/rules/ initiatives.mdc

Nach jedem Sub-Task lokal testen.
Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle: Phase 1 → done
- Doc-Updates: Resend in ARCHITECTURE.md auf aktiv setzen
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Resend SDK** ist sehr schlank, brauchst nicht viel Wrapping
- **HTML-Mails** brauchen Inline-CSS (Outlook etc. unterstützen `<style>` schlecht)
- **Test-Mail-Inhalt**: simpel halten – „Test-Mail von Gourmen App, gesendet von <user>"
- Resend hat eine **Sandbox-Adresse** (`onboarding@resend.dev`) für initialen Test, falls deine Domain noch nicht verifiziert ist
