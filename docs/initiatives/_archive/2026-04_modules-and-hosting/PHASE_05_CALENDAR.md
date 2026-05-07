# Phase 5 – Kalender (iCal-Export)

**Status**: pending  
**Aufwand**: ~1 Tag  
**Branch**: `phase/05-modules-calendar`

## Ziel

Pro Member ein iCal-Feed mit allen relevanten Vereinsterminen, der in Apple Calendar / Google Calendar / Outlook abonniert werden kann. Token-basierter, signierter URL-Zugriff (kein Login nötig im Kalender-Client).

## Pre-Conditions

- Branch `phase/05-modules-calendar` von `master` erstellt
- Keine Modul-Abhängigkeiten

## Tasks

### 1. Dependency

- [ ] `ics` Python-Library in `requirements.txt` (oder `icalendar`, beide funktionieren)

### 2. Member-Modell erweitern

- [ ] Neues Feld in `backend/models/member.py`:
  - `ical_token` (VARCHAR 64, unique, nullable, indexed)
- [ ] Property `ical_url` returnt `url_for('calendar.member_feed', token=...)` falls Token gesetzt
- [ ] Methode `regenerate_ical_token()` – setzt neuen Token, Audit-Log
- [ ] Alembic-Migration in **separatem Commit**

### 3. Service-Layer

Datei `backend/services/calendar.py`:

- [ ] `CalendarService`
  - [ ] `generate_member_feed(member_id) -> str` – iCal-String mit:
    - Alle veröffentlichten Events (`Event.published=true`)
    - VEVENT pro Event mit:
      - SUMMARY: Event-Typ + Restaurant (z.B. `🍽️ Monatsessen – Da Marco`)
      - DTSTART/DTEND mit Europe/Zurich-Zeitzone
      - LOCATION: Place-Address falls vorhanden
      - DESCRIPTION: Notizen + Link zur App
      - URL: Link zur Event-Detail-Page
      - UID: stabil pro Event (z.B. `event-<id>@gourmen.ch`)
      - LAST-MODIFIED: `Event.updated_at`
  - [ ] Optional: Erinnerungen (VALARM) konfigurierbar
  - [ ] Member-Filter: nur Events bei denen Member relevant ist (alle, aktuell)

### 4. Routes

Neuer Blueprint `backend/routes/calendar.py`:

- [ ] `GET /calendar/<token>.ics`
  - **Kein** `@login_required` – authentifiziert über Token
  - Member-Lookup über `ical_token`, bei Miss → 404
  - `Content-Type: text/calendar; charset=utf-8`
  - Cache-Headers konservativ (`Cache-Control: max-age=300`)
  - Rückgabe: iCal-String aus Service
  - Audit-Log: optional, nicht zwingend (sonst zuviele Logs durch Kalender-Polling)

### 5. Member-Settings UI

In `backend/routes/member.py` und Template:

- [ ] Settings-Sektion „Kalender":
  - Wenn Token vorhanden: URL anzeigen mit Copy-Button
  - „Token regenerieren"-Button (Bestätigung, alter Link wird ungültig)
  - „Token entfernen"-Button (Kalender-Sync deaktivieren)
- [ ] Erklärungs-Text: wie Kalender abonnieren (Apple, Google, Outlook)
- [ ] BEM-Klassen, Tokens (siehe `docs/UI.md`)

### 6. Auto-Token-Erstellung

- [ ] Bei erstem Aufruf der Settings-Sektion: Token erstellen wenn noch nicht vorhanden
- [ ] **Nicht** automatisch beim Member-Anlegen (keine ungenutzten Tokens)

### 7. Doc-Updates

- [ ] `docs/ARCHITECTURE.md`: neuer Blueprint
- [ ] `docs/DOMAIN.md`: optional Sektion „Kalender" wenn relevant

## Acceptance-Criteria

- [ ] Member kann in Settings den iCal-Link generieren
- [ ] Link in Apple Calendar, Google Calendar, Outlook einbinden funktioniert
- [ ] Events erscheinen mit korrekter Zeit (Europe/Zurich), Ort, Beschreibung
- [ ] Bei Event-Änderungen aktualisieren sich die Einträge in den Kalendern (binnen 24h)
- [ ] Token regenerieren macht alten Link ungültig
- [ ] Ohne Token: 404
- [ ] Tests grün
- [ ] DB-Migration sauber

## Out of Scope

- **Kein two-way Sync** mit Google/Outlook (würde OAuth + komplexen State-Management bedeuten)
- **Kein eigener CalDAV-Server** (Radicale, Baikal etc.)
- **Keine Reminder-Mails über iCal** (nur Push-Reminder gibt es bereits)
- **Keine pro-Event-Anpassungen** (alle veröffentlichten Events kommen rein)
- **Kein Member-spezifisches Filtering** (z.B. „nur Events an denen ich teilnehme")

## Cursor-Agent-Briefing

```
Branch: phase/05-modules-calendar
Doc: docs/initiatives/modules-and-hosting/PHASE_05_CALENDAR.md

Pre-Flight:
- AGENTS.md lesen
- docs/ARCHITECTURE.md lesen
- docs/CONVENTIONS.md lesen
- docs/DOMAIN.md lesen (Event-Typen)

Implementiere Phase 5 (iCal-Kalender) gemäss Phasen-Doc:
- DB-Migration in eigenem Commit
- ics-Library nutzen, nicht selbst RFC-5545 implementieren
- Token sicher generieren (secrets.token_urlsafe(32))
- Folge .cursor/rules/initiatives.mdc

Lokal verifizieren:
- iCal-Feed aufrufen, Inhalt mit https://icalendar.org/validator.html prüfen
- In Apple Calendar abonnieren testen

Am Ende:
- Acceptance-Criteria abhaken
- Initiative-README Status-Tabelle aktualisieren
- ARCHITECTURE.md updaten
- Commit-Message-Vorschlag, dann auf User-Bestätigung warten
```

## Hinweise

- **Timezone**: Europe/Zurich – `DTSTART;TZID=Europe/Zurich:...`
- **VTIMEZONE-Block** mit DST-Daten ist Pflicht für korrekte Zeit-Anzeige
- **iCalendar-Validator** für Test: https://icalendar.org/validator.html
- **Kalender-Apps cachen**: Änderungen brauchen oft 24h sichtbar zu werden
- **Token-Format**: `secrets.token_urlsafe(32)` ergibt 43 Zeichen – passt in URL ohne Probleme
