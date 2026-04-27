# Phase 2 – Login-Verbesserungen

**Status**: in_progress  
**Aufwand**: ~2 Tage (1 Tag Code, 0.5 Tag Tests, 0.5 Tag Polish)  
**Branch**: `phase/02-modules-login`

## Ziel

Echtes Passwort-Reset und 2FA-Reset auf Basis von Mail aus Phase 1. Onboarding-Mail beim Account-Anlegen. Token werden in der DB statt Flask-Session gespeichert (geräte-übergreifend nutzbar).

## Pre-Conditions

- Phase 1 abgeschlossen, Mail funktioniert (`MailService.send` ok)
- Branch `phase/02-modules-login` von `master` erstellt
- Lokal Mail-Test gemacht vor Start

## Tasks

### 1. Token-Tabelle in DB

- [x] Neues Model `backend/models/auth_token.py`
  - Felder:
    - `id` (PK)
    - `member_id` (FK → members, ondelete CASCADE)
    - `token_hash` (VARCHAR 128, unique, indexed) – SHA-256 oder ähnlich, niemals Klartext-Token speichern
    - `purpose` (Enum: `PASSWORD_RESET`, `MFA_RESET`, `ONBOARDING`, später `MAGIC_LINK`)
    - `expires_at` (DateTime, nicht null)
    - `used_at` (DateTime, nullable)
    - `created_at` (DateTime, default utcnow)
    - `request_ip` (VARCHAR 45, optional, für Audit)
- [x] Index auf `(member_id, purpose, used_at)` für Cleanup
- [x] Alembic-Migration erstellt (`6f9a2d1c4b7e_add_auth_tokens_table.py`)
- [ ] **Separater Commit** für Migration
- [x] Lokal getestet: `flask db upgrade && flask db downgrade && flask db upgrade`

### 2. Forgot-Password-Flow umbauen

In `backend/routes/auth.py`:

- [x] `forgot_password` umbauen:
  - [x] User-Lookup mit Email
  - [x] Bei existierendem User:
    - [x] Sicheres Token generieren (`secrets.token_urlsafe(32)`)
    - [x] Hash in DB speichern (`AuthToken` mit `purpose=PASSWORD_RESET`, `expires_at=now+1h`)
    - [x] Reset-Link `url_for('auth.reset_password', token=token, _external=True)`
    - [x] Mail an User-Email via `MailService` mit Template `password_reset.html`
  - [x] Bei nicht-existierendem User: silently skip (kein User-Enumeration!)
  - [x] Immer gleiche Antwort: „Wenn die Adresse existiert, wurde eine Mail versendet"
- [x] `reset_password/<token>`:
  - [x] Token in DB suchen (gehasht)
  - [x] `expires_at` und `used_at` prüfen
  - [x] Bei Erfolg: Passwort setzen + `used_at` markieren + Audit-Log
- [x] Alte Session-basierte Reset-Logik entfernen (`session['last_generated_reset_url']`)
- [x] Route `show_reset_link` entfernen (war Workaround)

### 3. Mail-Template Passwort-Reset

- [x] `templates/emails/password_reset.html`
  - [x] Erbt von `templates/emails/base.html`
  - [x] Begrüßung mit Member-Display-Name
  - [x] Link mit klarem Call-to-Action
  - [x] Hinweis: Link 1 Stunde gültig
  - [x] Hinweis: wenn nicht selbst angefordert, ignorieren

### 4. 2FA-Reset analog

- [x] `request_2fa_reset`:
  - [x] Token in DB statt Session (`purpose=MFA_RESET`)
  - [x] Mail-Template `templates/emails/2fa_reset.html`
- [x] `reset_2fa/<token>`:
  - [x] Token in DB suchen
  - [x] 2FA disablen + Backup-Codes löschen + `used_at` markieren
  - [x] Audit-Log

### 5. Onboarding-Mail

Bei Member-Erstellung durch Admin:

- [x] In `backend/routes/admin.py` (oder wo Members erstellt werden):
  - [x] Onboarding-Token erstellen (`purpose=ONBOARDING`, `expires_at=now+7d`)
  - [x] Mail an neuen Member mit „Account aktivieren"-Link
  - [x] Template `templates/emails/onboarding.html`
- [x] Aktivierungs-Route `auth.activate/<token>`:
  - [x] User setzt eigenes Passwort
  - [x] Token markieren als used
  - [x] Login + Redirect Dashboard
- [x] Admin-UI: zeigen, dass Onboarding-Mail versendet wurde (Flash-Feedback im Create-Flow)
- [x] **Bestehender** `INIT_ADMIN_EMAIL/PASSWORD`-Mechanismus bleibt für Bootstrap-Admin

### 6. Cleanup

- [x] Alte Session-basierte Reset-Logik vollständig entfernen
- [x] Audit-Aktionen ergänzen falls neue (`USE_ONBOARDING_TOKEN` o.ä.)
- [x] Initial-Passwort-Mechanismus (`needs_password_change`) bleibt als Fallback

### 7. Token-Cleanup-Job

- [x] In `run_cron_reminders.py` (oder neuer Cron): `AuthToken.query.filter(expires_at < now - 30d).delete()` einmal täglich
  - Optional, aber gute Hygiene

### 8. Doc-Updates

- [x] `docs/ARCHITECTURE.md`: Auth-Flow-Sektion erweitern um Token-Tabelle und Mail-basierte Reset-Flows
- [x] `docs/ARCHITECTURE.md`: „Bekannte Schwächen" Login-Punkt entfernen

## Acceptance-Criteria

- [ ] User kann „Passwort vergessen" → Mail empfangen → von beliebigem Gerät resetten (E2E mit realer Mailadresse ausstehend)
- [ ] 2FA-Reset funktioniert analog (E2E mit realer Mailadresse ausstehend)
- [ ] Neue Mitglieder bekommen Onboarding-Mail mit Aktivierungs-Link (E2E mit realer Mailadresse ausstehend)
- [x] Bestehende User mit gesetztem Passwort sind unbeeinträchtigt
- [x] Token werden nach Verwendung als `used_at` markiert (kein Replay)
- [x] Abgelaufene Token zeigen sinnvolle Fehlermeldung
- [x] Kein User-Enumeration (gleiche Antwort egal ob User existiert)
- [x] Audit-Log enthält alle Reset-Aktionen
- [x] Tests grün (lokaler Smoke-Test via test_client + UI-Sanity)
- [x] DB-Migration sauber (up + down funktioniert)

## Out of Scope

- Kein Magic-Link-Login (separate Mini-Phase falls gewünscht)
- Keine Google/Apple/Microsoft OAuth (separate Mini-Phase falls gewünscht)
- Keine Self-Signup-Funktion (User-Anlage bleibt Admin-only)
- Keine Email-Verifikation für bestehende User (nur für neue)

## Cursor-Agent-Briefing

```
Branch: phase/02-modules-login
Doc: docs/initiatives/modules-and-hosting/PHASE_02_LOGIN.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen (Auth-Flow-Sektion)
- docs/CONVENTIONS.md lesen (Models + Migrationen)
- Phase 1 muss abgeschlossen sein

Implementiere Phase 2 (Login-Verbesserungen) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- Bestehender Login-Flow MUSS funktionieren bleiben (Member mit Passwort + 2FA)
- Bestehende ENV vars und Config-Strukturen nicht ändern, nur erweitern
- Folge .cursor/rules/initiatives.mdc

Nach jedem Sub-Task lokal verifizieren:
- Test-User mit funktionierendem Reset-Flow
- 2FA-Reset über zweites Gerät prüfen

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Token-Hashing**: Verwende `hashlib.sha256(token.encode()).hexdigest()` oder ähnlich. Damit ist auch bei DB-Leak der Klartext-Token nicht direkt nutzbar.
- **Rate-Limiting**: `forgot_password` und `request_2fa_reset` haben bereits `@limiter.limit("3 per hour")`. Beibehalten.
- **Mail-Inhalt**: nicht zu detailreich, kurz und präzise. Link prominent platzieren.
- **`used_at`-Check** muss vor `expires_at`-Check kommen, sonst kannst du verwendete-aber-nicht-abgelaufene Tokens nochmal nutzen.
