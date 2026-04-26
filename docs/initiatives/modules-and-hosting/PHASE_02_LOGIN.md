# Phase 2 – Login-Verbesserungen

**Status**: pending  
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

- [ ] Neues Model `backend/models/auth_token.py`
  - Felder:
    - `id` (PK)
    - `member_id` (FK → members, ondelete CASCADE)
    - `token_hash` (VARCHAR 128, unique, indexed) – SHA-256 oder ähnlich, niemals Klartext-Token speichern
    - `purpose` (Enum: `PASSWORD_RESET`, `MFA_RESET`, `ONBOARDING`, später `MAGIC_LINK`)
    - `expires_at` (DateTime, nicht null)
    - `used_at` (DateTime, nullable)
    - `created_at` (DateTime, default utcnow)
    - `request_ip` (VARCHAR 45, optional, für Audit)
- [ ] Index auf `(member_id, purpose, used_at)` für Cleanup
- [ ] Alembic-Migration erstellen: `flask db migrate -m "add auth_tokens"`
- [ ] **Separater Commit** für Migration
- [ ] Lokal testen: `flask db upgrade && flask db downgrade && flask db upgrade`

### 2. Forgot-Password-Flow umbauen

In `backend/routes/auth.py`:

- [ ] `forgot_password` umbauen:
  - [ ] User-Lookup mit Email
  - [ ] Bei existierendem User:
    - [ ] Sicheres Token generieren (`secrets.token_urlsafe(32)`)
    - [ ] Hash in DB speichern (`AuthToken` mit `purpose=PASSWORD_RESET`, `expires_at=now+1h`)
    - [ ] Reset-Link `url_for('auth.reset_password', token=token, _external=True)`
    - [ ] Mail an User-Email via `MailService` mit Template `password_reset.html`
  - [ ] Bei nicht-existierendem User: silently skip (kein User-Enumeration!)
  - [ ] Immer gleiche Antwort: „Wenn die Adresse existiert, wurde eine Mail versendet"
- [ ] `reset_password/<token>`:
  - [ ] Token in DB suchen (gehasht)
  - [ ] `expires_at` und `used_at` prüfen
  - [ ] Bei Erfolg: Passwort setzen + `used_at` markieren + Audit-Log
- [ ] Alte Session-basierte Logik entfernen (`session['last_generated_reset_url']`)
- [ ] Route `show_reset_link` entfernen (war Workaround)

### 3. Mail-Template Passwort-Reset

- [ ] `templates/emails/password_reset.html`
  - Erbt von `templates/emails/base.html`
  - Begrüßung mit Member-Display-Name
  - Link mit klarem Call-to-Action
  - Hinweis: Link 1 Stunde gültig
  - Hinweis: wenn nicht selbst angefordert, ignorieren

### 4. 2FA-Reset analog

- [ ] `request_2fa_reset`:
  - [ ] Token in DB statt Session (`purpose=MFA_RESET`)
  - [ ] Mail-Template `templates/emails/2fa_reset.html`
- [ ] `reset_2fa/<token>`:
  - [ ] Token in DB suchen
  - [ ] 2FA disablen + Backup-Codes löschen + `used_at` markieren
  - [ ] Audit-Log

### 5. Onboarding-Mail

Bei Member-Erstellung durch Admin:

- [ ] In `backend/routes/admin.py` (oder wo Members erstellt werden):
  - [ ] Onboarding-Token erstellen (`purpose=ONBOARDING`, `expires_at=now+7d`)
  - [ ] Mail an neuen Member mit „Account aktivieren"-Link
  - [ ] Template `templates/emails/onboarding.html`
- [ ] Aktivierungs-Route `auth.activate/<token>`:
  - [ ] User setzt eigenes Passwort
  - [ ] Token markieren als used
  - [ ] Login + Redirect Dashboard
- [ ] Admin-UI: zeigen, dass Onboarding-Mail versendet wurde
- [ ] **Bestehender** `INIT_ADMIN_EMAIL/PASSWORD`-Mechanismus bleibt für Bootstrap-Admin

### 6. Cleanup

- [ ] Alte Session-basierte Reset-Logik vollständig entfernen
- [ ] Audit-Aktionen ergänzen falls neue (`USE_ONBOARDING_TOKEN` o.ä.)
- [ ] Initial-Passwort-Mechanismus (`needs_password_change`) bleibt als Fallback

### 7. Token-Cleanup-Job

- [ ] In `run_cron_reminders.py` (oder neuer Cron): `AuthToken.query.filter(expires_at < now - 30d).delete()` einmal täglich
  - Optional, aber gute Hygiene

### 8. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: Auth-Flow-Sektion erweitern um Token-Tabelle und Mail-basierte Reset-Flows
- [ ] `docs/ARCHITECTURE.md`: „Bekannte Schwächen" Login-Punkt entfernen

## Acceptance-Criteria

- [ ] User kann „Passwort vergessen" → Mail empfangen → von beliebigem Gerät resetten
- [ ] 2FA-Reset funktioniert analog
- [ ] Neue Mitglieder bekommen Onboarding-Mail mit Aktivierungs-Link
- [ ] Bestehende User mit gesetztem Passwort sind unbeeinträchtigt
- [ ] Token werden nach Verwendung als `used_at` markiert (kein Replay)
- [ ] Abgelaufene Token zeigen sinnvolle Fehlermeldung
- [ ] Kein User-Enumeration (gleiche Antwort egal ob User existiert)
- [ ] Audit-Log enthält alle Reset-Aktionen
- [ ] Tests grün
- [ ] DB-Migration sauber (up + down funktioniert)

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
