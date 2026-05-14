# Phase 5 – App: iCal-Feed pro Mitglied

**Status**: done — umgesetzt 2026-05-14 auf Branch `phase/05-workspace-ical-feed`.
**Aufwand**: ~1–1.5 Tage
**Branch**: `phase/05-workspace-ical-feed`

## Ziel

Jedes Mitglied kann die Vereinstermine in seinem persönlichen Kalender (Apple Calendar, Google Calendar, Outlook) abonnieren. Die App generiert dazu pro Mitglied einen Token-geschützten iCal-Feed; die Kalender-App pollt die URL und hält den Mitglieds-Kalender automatisch aktuell.

Ersetzt die frühere Planung aus `_archive/2026-04_modules-and-hosting/PHASE_05_CALENDAR.md` (vor dem Strategie-Pivot 2026-05-07 entstanden, ohne AI/Automation-Sektion und Cancel-Konzept).

## Autoritative Spezifikation

**Source of Truth für diese Phase ist `docs/capabilities/calendar.md`.**

Dieses Phase-Doc ist nur der Phasen-Briefing-Rahmen. Alle Details (Architektur, Datenmodell, Service-Layer, UX, Sicherheit, Acceptance-Criteria) stehen im Capability-Doc und gelten bei Konflikt vor Aussagen in diesem Phase-Doc.

## Pre-Conditions

- Branch `phase/05-workspace-ical-feed` von `master` erstellt.
- Member-Modell hat `spirit_animal` und `rufname` (heute vorhanden, siehe `display_spirit_rufname` Property).
- Event-Modell hat `published`, `datum`, `place_name`/`place_address`/`restaurant`, `organisator_id`, `notizen` (heute vorhanden).
- **Neu durch diese Capability**: `Event.ical_sequence` wird in der Migration ergänzt. Kein Cancel-Konzept im Modell — abgesagte Events werden in der App gelöscht und fallen damit aus dem Feed.
- Redis ist auf Railway aktiv (für Rate-Limit-Counter; nutzt bestehende Infrastruktur).

Keine Abhängigkeit zu Phase 1–4. Phase 5 kann parallel zu Phase-4-Vorbereitungen laufen.

## Implementations-Reihenfolge (siehe Capability-Doc Sektion 17.1)

1. *Schema-Migration Member*: `ical_token VARCHAR(64) UNIQUE INDEXED NULLABLE`. Eigener Alembic-Commit.
2. *Schema-Migration Event*: `ical_sequence INT NOT NULL DEFAULT 0`. Eigener Alembic-Commit.
3. *Service-Layer*: `backend/services/calendar_feed.py` gemäss Capability-Doc Sektion 8. Unit-Tests gegen iCalendar-Validator.
4. *SEQUENCE-Bump-Hook*: Event-Service-Erweiterung, die bei Edits auf kalender-relevante Felder `ical_sequence += 1` setzt. Liste der Felder gemäss Capability-Doc Sektion 8.3.
5. *Routes und UI*: Public Feed-Endpoint, Member-Settings-Sektion mit drei UI-States, Admin-Detail-Status-Anzeige.
6. *Rate-Limit und Cache-Header*: Limiter-Decorator (Flask-Limiter, falls vorhanden, sonst Redis-Counter), `Cache-Control`, ETag.

## Acceptance-Criteria

Vollständige Liste in `docs/capabilities/calendar.md`, Sektion 17.3.

Kurzfassung:

- [ ] Feed-URL liefert RFC-5545-konformes iCal (Validator-Pass)
- [ ] Mitglied kann in Settings aktivieren, neuen Link erzeugen, deaktivieren
- [ ] Veröffentlichte zukünftige Events erscheinen mit SUMMARY `[Emoji] Gourmen - [Restaurant]`
- [ ] DTSTART/DTEND immer 18:00–23:00 Europe/Zurich (VTIMEZONE im Feed)
- [ ] Verschiebung: gleiche UID, neues DTSTART, höhere SEQUENCE
- [ ] Gelöschtes Event verschwindet beim nächsten Polling aus den abonnierten Kalendern (Apple, Google)
- [ ] Apple Calendar abonniert und Update binnen 15 Min sichtbar
- [ ] Google Calendar (Desktop, «Per URL hinzufügen») abonniert und Events sichtbar
- [ ] Rate-Limit 60/min pro Token greift, Cache-Header gesetzt
- [ ] Admin-Detail zeigt Abo-Status, nicht Token-Wert
- [ ] AuditEvents `CALENDAR_FEED_ENABLED`/`REGENERATED`/`DISABLED`
- [ ] Tests grün, kein Token im Audit-Log oder Admin-UI

## Out of Scope

Vollständige Liste in `docs/capabilities/calendar.md`, Sektion 17.4.

Kurzfassung: keine VALARMs, kein ATTENDEE, keine Feed-Varianten, kein `audience`-Filter, keine Mehrtages-Container-Events, keine AI-Features, kein bidirektionaler Sync mit Google Calendar, kein `ical_last_fetched_at`-Tracking, kein Caldav-Server.

## Cutover-Hinweis

Phase 5 geht **direkt live**, ohne Feature-Flag. Sobald die Implementation gemerged und deployed ist, sehen Mitglieder die Settings-Sektion und können den Kalender abonnieren.

Mit der App-weiten MVP-Update-Mail (Drive + iCal + Merch + System-Mail) wird die neue Funktion aktiv kommuniziert; das Feature ist aber bereits ab Deploy nutzbar.

## Cursor-Agent-Briefing

```
Branch: phase/05-workspace-ical-feed

Lies vor Implementation: docs/capabilities/calendar.md (autoritativ).
Dieses Phase-Doc ist nur der Rahmen, Details aus Capability-Doc.

Implementations-Reihenfolge gemäss Capability-Doc Sektion 17.1:
Member-Migration → Event-Migration → Service-Layer mit Tests →
SEQUENCE-Bump-Hook → Routes/UI → Rate-Limit/Cache-Header.

Zwei Migrationen sind separate Alembic-Commits.

Library: icalendar (PyPI), nicht ics — wegen sauberem VTIMEZONE-Support.

Token-Format: secrets.token_urlsafe(32). Token NIEMALS in Audit-Log oder
Admin-UI im Klartext speichern oder anzeigen.

Phase 5 geht direkt live, ohne Feature-Flag.

UX-Texte deutsch, schweizerische Schreibweise mit Guillemets («…»),
Doppel-S statt Eszett. BEM-Klassen und Tokens gemäss docs/UI.md.

Lokale Verifikation:
- Feed-Output gegen https://icalendar.org/validator.html prüfen
- In Apple Calendar abonnieren via webcal://-Link aus den Settings
- Test-Update an einem Event (Datum verschieben) → SEQUENCE-Bump
  → in Apple Calendar binnen 15 Min sichtbar
- Test-Cancel an einem Event → Eintrag wird gestrichen
- Test gegen Validator: nach Validator-Pass und Live-Test
  Acceptance-Criteria abhaken, Initiative-README Status-Tabelle
  aktualisieren, ARCHITECTURE.md um Calendar-Blueprint ergänzen,
  Commit-Message-Vorschlag, dann auf User-Bestätigung warten.
```
