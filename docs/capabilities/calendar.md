# Capability: iCal-Feed pro Mitglied

> **Zweck**: Jedes Mitglied kann die Vereinstermine in seinem persönlichen Kalender (Apple Calendar, Google Calendar, Outlook) abonnieren. Die App generiert dazu pro Mitglied einen Token-geschützten iCal-Feed; die Kalender-App pollt die URL und hält den Mitglieds-Kalender automatisch aktuell.
>
> **Status**: Konzept abgeschlossen, bereit für Phase-5-Implementation. **Owner**: Andreas. **Stand**: 2026-05-14.
>
> **Verwandte Docs**: `docs/STRATEGY_2026.md` (strategischer Rahmen, MVP-Punkt 3), `docs/initiatives/workspace-railway/PHASE_05_ICAL_FEED.md` (Phasen-Briefing für Cursor), `docs/ARCHITECTURE.md` (Stack-Detail), `docs/capabilities/drive.md` (Schwester-Capability, gleiche Doc-Konvention).

---

## 1. Strategie-Anker

Aus `STRATEGY_2026.md` als Source-of-Truth:

- *MVP-Punkt 3*: «iCal-Feed pro Mitglied — Token-basierter Calendar-Feed zum Abonnieren in Apple/Google/Outlook-Kalender.»
- *Mailwege-Tabelle*: Massenmails / Newsletter sind nicht vorgesehen. Vereins-Kommunikation läuft über PWA, App-Push und WhatsApp-Gruppe. Der iCal-Feed ergänzt diese Kanäle um den Kalender-Touchpoint, ohne Push-Reminder-Konkurrenz aufzumachen.
- *Datenhaltung*: Strukturierte App-Daten leben in Postgres. Der iCal-Feed ist eine **Anzeige-Schicht** auf den bestehenden Event-Daten, kein zweiter Source of Truth.

Bewusst verworfen: ein geteilter Google Calendar im Workspace-Konto als Alternative zum eigenen Feed. Begründung siehe Sektion 4.2.

## 2. User Stories

| Rolle | Story |
|---|---|
| Mitglied | «Ich möchte die Vereinstermine in meinem persönlichen Kalender sehen, ohne dauernd die App öffnen zu müssen.» |
| Mitglied | «Ich aktiviere das Kalender-Abo in den App-Settings mit einem Klick und binde den Link in Apple/Google/Outlook ein.» |
| Mitglied | «Wenn ein Monatsessen verschoben wird, soll sich der Eintrag in meinem Kalender automatisch aktualisieren.» |
| Mitglied | «Wenn ein Event gelöscht wird (z.B. weil es abgesagt wurde), soll der Eintrag aus meinem Kalender verschwinden.» |
| Mitglied | «Falls meine Kalender-URL irgendwo geleakt ist, kann ich den Link neu erzeugen und der alte wird ungültig.» |
| Mitglied | «Falls ich das Abo nicht mehr will, kann ich es deaktivieren.» |
| Admin | «Ich sehe pro Mitglied, ob es das Kalender-Abo aktiviert hat, ohne den Token im Klartext zu sehen.» |

## 3. Token-basierter Zugriff

### 3.1 Token-Modell

Pro Mitglied existiert maximal **ein** iCal-Token, gespeichert als `Member.ical_token`. Der Token wird:

- *erst bei Aktivierung* generiert (kein Default beim Member-Anlegen, keine ungenutzten Tokens in der DB)
- mit `secrets.token_urlsafe(32)` erzeugt (~43 Zeichen URL-safe Base64, kryptografisch sauber)
- als `VARCHAR(64) UNIQUE INDEXED NULLABLE` abgelegt

Token-Format: random, **nicht** HMAC-signiert. Begründung: HMAC-Stateless-Validierung spart keine echte Arbeit, weil wir für die Feed-Generierung sowieso einen DB-Lookup auf den Member machen müssen. Random-Token ist einfacher und stört nicht.

### 3.2 Lifecycle

| Aktion | Auslöser | Effekt |
|---|---|---|
| **Aktivieren** | Klick auf «Kalender-Abo aktivieren» in Settings | `ical_token` wird neu generiert, AuditEvent `CALENDAR_FEED_ENABLED` |
| **Regenerieren** | Klick «Link neu erzeugen» in Settings, mit Bestätigung | Alter Token überschrieben, AuditEvent `CALENDAR_FEED_REGENERATED`; alle abonnierten Clients erhalten ab nächstem Polling 404 |
| **Deaktivieren** | Klick «Kalender-Abo deaktivieren», mit Bestätigung | `ical_token = NULL`, AuditEvent `CALENDAR_FEED_DISABLED` |

### 3.3 Privacy-Hinweis am Token-URL

Token landet in der URL und damit in:

- Browser-History des Mitglieds (irrelevant)
- Web-Server-Access-Logs auf Railway
- ggf. Reverse-Proxy- und Client-Logs der Kalender-App

Das ist Standard für iCal-Feeds (Google und Apple machen es selbst auch so). Der Aspekt wird in die Datenschutz-Erklärung aufgenommen, sobald diese existiert (siehe `docs/capabilities/drive.md` Sektion 13.3). **Kein Blocker für Implementation**, weil der Feed-Inhalt keine sensiblen Daten enthält, die nicht heute schon in der App sichtbar wären.

## 4. Feed-Architektur

### 4.1 Ein Feed pro Mitglied (Variante A)

Jeder Member-Token-URL liefert exakt einen iCal-Feed, der **alle veröffentlichten Events** der Zukunft enthält. Filter: `Event.published == True` und `Event.datum >= today`.

Kein Per-Member-Filtering nach Teilnahmestatus, kein Sub-Feed pro Event-Typ. Begründung:

- Subjektive Filter (z.B. «nur Events, an denen ich teilnehme») führen zu Kalender-Drift, wenn Anmeldungen sich ändern — Clients halten gelöschte Events teilweise im Cache.
- Familiärer Verein mit drei Event-Typen — die meisten Mitglieder wollen schlicht alle Vereinstermine sehen.

Erweiterbar später ohne Modell-Bruch: ein zweiter Endpunkt mit Query-Parametern (`?types=...`) könnte Feed-Varianten anbieten, ohne den Haupt-Token zu invalidieren.

### 4.2 Verworfene Alternative: geteilter Google Calendar

Statt eines eigenen iCal-Feeds könnten Events in einen Workspace-Google-Calendar gepusht und mit allen Mitgliedern geteilt werden. Bewusst nicht gewählt:

- Würde Postgres und Google Calendar als **zweiten Source of Truth** parallel halten — Sync-Konflikte, bidirektionale-Edit-Problematik.
- Bricht die Strategie-Linie «App ist Frontend, externe Plattform ist Speicher» (für Dokumente sinnvoll, für strukturierte Vereinsdaten wie Events nicht).
- Backlog-Punkte «Vorstands-only-Sichtbarkeit» und «pro-Mitglied-Filter» werden über mehrere Kalender und Permission-Pflege deutlich komplexer als über zwei Token-Varianten am selben Endpoint.
- Wesentliche Bequemlichkeit («mit einem Klick einbinden») bringt der Google-Pfad nicht — Google Calendar kann iCal-URLs problemlos via «Anderer Kalender → Über URL hinzufügen» abonnieren.

Push-Latenz vs. Pull-Latenz ist für Vereinstermine, die sich nicht im Stundentakt ändern, kein relevanter Unterschied. Updates werden ohnehin parallel über App-Push und WhatsApp-Gruppe kommuniziert.

### 4.3 Was bei Sichtbarkeits-Erweiterungen passiert (Backlog)

Sobald Vorstandssitzungen als eigener Event-Typ mit `audience = board` kommen, wird der Feed-Filter um eine Sichtbarkeits-Bedingung erweitert: «Standard-Feed zeigt `audience IN ('all')`, Vorstands-Feed zusätzlich `audience IN ('all', 'board')`.» Modell-Erweiterung ist klein, kein Doc-Bruch nötig.

## 5. Datenmodell-Änderungen

### 5.1 Member-Erweiterung

```python
# Ergänzung in models/member.py
ical_token = db.Column(db.String(64), unique=True, index=True, nullable=True)
```

`ical_token IS NULL` heisst: Mitglied hat kein aktives Kalender-Abo. `ical_token IS NOT NULL` heisst: aktiv.

### 5.2 Event-Erweiterungen

```python
# Ergänzung in models/event.py

# Update-Sequenz für iCal-Clients (RFC 5545 SEQUENCE)
ical_sequence = db.Column(db.Integer, nullable=False, default=0)
```

Bewusst **kein** Cancel-Feld am Event. Abgesagte Events werden in der App gelöscht (Hard-Delete oder bestehende Lösch-Mechanik), nicht als «cancelled» geflaggt. Damit:

- Feed sendet kein `STATUS`-Feld (RFC 5545: ohne `STATUS` gilt implizit `CONFIRMED`)
- Gelöschtes Event fällt aus dem Feed-Query → Kalender-Client entfernt den Eintrag beim nächsten Polling, weil die UID nicht mehr ausgeliefert wird (Standard `METHOD:PUBLISH`-Verhalten)
- Kein neuer Lifecycle-Zustand am Event-Modell, keine UI-Cancel-Toggle, kein zusätzlicher Audit-Trail

Trade-off: Outlook-Clients sind beim Cache-Räumen von subscribed Calendars manchmal träge — ein gelöschtes Event kann dort länger hängenbleiben. Bei Apple und Google verschwindet es sauber beim nächsten Refresh. Akzeptabel, weil Outlook-Nutzer ohnehin die App-Push parallel bekommen.

### 5.3 Auto-Inkrement von `ical_sequence`

`ical_sequence` wird **nicht** durch das ORM automatisch inkrementiert. Der Service-Layer inkrementiert das Feld explizit, wenn eine kalendar-relevante Änderung am Event passiert:

- Datums-Änderung (`datum` ändert sich)
- Ort-Änderung (Restaurant, Place-Adresse)
- Event-Typ-Änderung
- Organisator-Wechsel
- Publikations-Toggle (`published` von `false` zu `true` oder zurück)

Reine Cosmetic-Edits (Tippfehler in `notizen`, BillBro-Felder) lösen **kein** Inkrement aus, damit nicht jeder Speichern-Click in jedem Kalender als «Update» geflaggt wird.

### 5.4 Indexes

```sql
CREATE UNIQUE INDEX ix_members_ical_token ON members (ical_token);
-- bestehender Index auf events.datum bleibt, wird im Feed-Query genutzt
```

### 5.5 Migrationen

Zwei separate Alembic-Commits in Phase 5:

1. **Member-Schema-Erweiterung**: `ical_token`-Feld mit UNIQUE-Index.
2. **Event-Schema-Erweiterung**: `ical_sequence INT NOT NULL DEFAULT 0`. Downgrade: Spalte droppen.

## 6. Inhalts-Mapping pro VEVENT

### 6.1 Feld-Tabelle

| iCal-Feld | Quelle | Beispiel |
|---|---|---|
| `UID` | `event-<id>@gourmen.ch` (stabil, unveränderlich) | `event-247@gourmen.ch` |
| `SEQUENCE` | `Event.ical_sequence` | `0`, `1`, `2`, … |
| `DTSTAMP` | aktueller Zeitstempel zur Feed-Generierung in UTC | `20260514T140523Z` |
| `LAST-MODIFIED` | `Event.updated_at` in UTC | `20260513T091230Z` |
| `SUMMARY` | `[Emoji] Gourmen - [Restaurant]` (Mapping in 6.2) | `🍴 Gourmen - Da Marco` |
| `DTSTART` | `Event.datum.date()` plus `18:00` mit `TZID=Europe/Zurich` | `DTSTART;TZID=Europe/Zurich:20260615T180000` |
| `DTEND` | `Event.datum.date()` plus `23:00` mit `TZID=Europe/Zurich` | `DTEND;TZID=Europe/Zurich:20260615T230000` |
| `LOCATION` | `Event.place_name` + `, ` + `Event.place_address` (Fallback `Event.restaurant`) | `Da Marco, Bahnhofstrasse 12, 8001 Zürich` |
| `DESCRIPTION` | `Event.notizen` + Leerzeile + `Details: <App-URL>` | siehe 6.3 |
| `URL` | Deep-Link auf App-Event-Detail-Seite | `https://gourmen.ch/events/247` |
| `CATEGORIES` | `Event.event_typ.value` (`MONATSESSEN`, `AUSFLUG`, `GENERALVERSAMMLUNG`) | `CATEGORIES:MONATSESSEN` |
| `ORGANIZER` | `CN=[Organisator.display_spirit_rufname]:mailto:kontakt@gourmen.ch` | `ORGANIZER;CN=Wolf Andreas:mailto:kontakt@gourmen.ch` |

**Bewusst weggelassen**: `STATUS` (keine Cancelled-Events im Modell, RFC 5545 nimmt ohne `STATUS` implizit `CONFIRMED` an), `ATTENDEE` (Privacy — Teilnehmerliste im Klartext-File), `VALARM` (Reminder-Kanal-Konflikt mit App-Push, siehe Sektion 13).

### 6.2 Emoji-Mapping pro Event-Typ

| `Event.event_typ` | Emoji im SUMMARY |
|---|---|
| `MONATSESSEN` | 🍴 |
| `AUSFLUG` | 🚐 |
| `GENERALVERSAMMLUNG` | 🏛️ |
| *Fallback* (neue, nicht gemappte Typen) | 📅 |

Begründung: SVG-Icons aus der App-UI können im iCal-`SUMMARY` nicht eingebettet werden — RFC 5545 erlaubt im Titel nur Unicode-Text, kein Markup. Unicode-Emojis sind der Kompromiss, der visuell zur App-Icon-Sprache passt. Auf modernen Apple/Google/Outlook-Clients sauber gerendert; Outlook ≤ 2019 zeigt teils Boxen statt Emoji, was akzeptiert ist.

### 6.3 DESCRIPTION-Format

```
<Event.notizen, falls vorhanden>

Details: https://gourmen.ch/events/<event_id>
```

Falls `Event.notizen` leer ist, beginnt die Description direkt mit «Details: …». Der Link auf die App-Detail-Seite ist der zentrale Klickpunkt für mehr Kontext (Organisator-Profil, Teilnehmerliste, BillBro-Stand, Place-Maps-Karte).

### 6.4 LOCATION-Komposition

```python
def _format_location(event: Event) -> str:
    parts = []
    name = event.place_name or event.restaurant
    if name:
        parts.append(name)
    if event.place_address:
        parts.append(event.place_address)
    return ', '.join(parts)
```

Falls weder `place_name` noch `place_address` gesetzt ist, fällt `LOCATION` weg (kein leeres Feld senden). Bei Reisen ohne Place-Daten erscheint im Kalender nur der SUMMARY-Titel, was akzeptabel ist.

### 6.5 Timezone-Block (VTIMEZONE)

Jeder Feed beginnt mit einem RFC-5545-konformen `VTIMEZONE`-Block für Europe/Zurich, der die DST-Regeln definiert. Ohne diesen Block würden manche Clients (insbesondere Outlook) Zeiten falsch konvertieren. Beispiel-Schablone:

```
BEGIN:VTIMEZONE
TZID:Europe/Zurich
BEGIN:STANDARD
DTSTART:19701025T030000
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10
TZNAME:CET
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19700329T020000
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3
TZNAME:CEST
END:DAYLIGHT
END:VTIMEZONE
```

Die genutzte iCal-Library (Empfehlung: `icalendar`, siehe Sektion 8.1) bringt VTIMEZONE-Generierung von Haus aus mit.

### 6.6 Gelöschte Events

Wenn ein Event in der App gelöscht wird (z.B. weil es abgesagt wurde), fällt es im nächsten Feed-Lauf einfach aus dem Query — die `UID` ist nicht mehr im ausgelieferten Feed enthalten. Kalender-Clients mit `METHOD:PUBLISH`-Subscribe entfernen den Eintrag beim nächsten Polling automatisch.

Trade-off: Apple und Google sind dabei sauber, Outlook cached subscribed Calendars manchmal länger und kann gelöschte Events kurzzeitig stehen lassen. Akzeptabel, weil Outlook-Nutzer parallel die App-Push erhalten.

### 6.7 Verschiebung

Wenn ein Event verschoben wird (`datum` ändert sich), bleibt die `UID` gleich, `ical_sequence` wird inkrementiert und das neue `DTSTART` wird ausgespielt. Kalender-Clients verschieben den vorhandenen Eintrag, statt einen Doppeleintrag anzulegen.

«Abgesagt und komplett neu angesetzt» (anderes Restaurant, anderer Kontext) ist domänenmässig **zwei Events**: das alte wird gelöscht (und fällt aus dem Feed), ein neues Event-Record wird angelegt. Das ist sauber sowohl im Feed als auch in BillBro/GGL.

## 7. iCal-Format-Spezifika

### 7.1 Calendar-Header

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gourmen Verein//PWA Calendar Feed//DE
METHOD:PUBLISH
CALSCALE:GREGORIAN
X-WR-CALNAME:Gourmen Vereinstermine
X-WR-TIMEZONE:Europe/Zurich
X-WR-CALDESC:Veröffentlichte Termine des Gourmen Vereins.
```

`X-WR-CALNAME` und `X-WR-TIMEZONE` sind Apple-/Google-spezifische Extension-Properties, die im Kalender-Client als Default-Name angezeigt werden. Sauberer Default für die Mitglieder, ohne dass sie den Kalender umbenennen müssen.

### 7.2 Line-Folding und Encoding

RFC 5545 verlangt Line-Folding (Zeilen > 75 Oktette werden umgebrochen mit `CRLF` + Space-Continuation). Die `icalendar`-Library macht das korrekt. Encoding ist UTF-8 ohne BOM. Content-Type-Header: `text/calendar; charset=utf-8`.

### 7.3 UID-Stabilität

`event-<id>@gourmen.ch` darf sich **nie** ändern. Wenn ein Event in der DB gelöscht und neu angelegt wird (statt geupdatet zu werden), erzeugt das neue Event auch eine neue UID — Kalender-Clients sehen das dann als «alter Eintrag verschwunden, neuer Eintrag erschienen», was korrekt ist.

### 7.4 SEQUENCE-Semantik

`SEQUENCE` ist eine reine Update-Zähler-Logik nach RFC 5545: Clients beachten Updates nur, wenn die `SEQUENCE` höher ist als die zuletzt gesehene. Default `0` beim Anlegen, +1 bei kalender-relevanten Edits.

## 8. Service-Layer

### 8.1 Library

Empfehlung: **`icalendar`** (PyPI, BSD-License, etabliert, RFC-5545-konform mit VTIMEZONE-Support). Alternative `ics` ist einfacher in der API, hat aber weniger sauberen VTIMEZONE-Support — für unseren Europe/Zurich-Fall ist `icalendar` der robustere Pfad.

### 8.2 Service-Klasse

Datei `backend/services/calendar_feed.py`:

```python
class CalendarFeedService:
    """Service-Layer für iCal-Feed-Generierung.

    Generiert pro Member einen RFC-5545-konformen Feed mit allen
    veröffentlichten, zukünftigen Vereinstermine. Token-basierter
    Zugriff; keine Authentifizierung des HTTP-Requests nötig.
    """

    # Feed-Generierung
    def generate_feed_for_member(self, member: Member) -> bytes: ...
    def _build_vevent(self, event: Event) -> Component: ...
    def _build_vtimezone(self) -> Component: ...
    def _format_summary(self, event: Event) -> str: ...
    def _format_location(self, event: Event) -> str: ...
    def _format_description(self, event: Event) -> str: ...

    # Token-Lifecycle (genutzt vom Member-Settings-Controller)
    def enable_feed_for_member(self, member: Member) -> str: ...
    def regenerate_token_for_member(self, member: Member) -> str: ...
    def disable_feed_for_member(self, member: Member) -> None: ...

    # SEQUENCE-Bump (genutzt von Event-Service bei relevanten Edits)
    def bump_sequence_if_changed(self, event: Event, before: dict, after: dict) -> None: ...
```

### 8.3 SEQUENCE-Bump-Logik

Der Bump läuft im Event-Service (nicht im CalendarFeedService selbst), wird aber zentral in `CalendarFeedService.bump_sequence_if_changed` definiert, damit die Liste kalender-relevanter Felder an einer Stelle steht:

```python
RELEVANT_FIELDS = {
    'datum',
    'event_typ',
    'restaurant',
    'place_name',
    'place_address',
    'organisator_id',
    'published',  # Event wird publiziert/depubliziert
}
```

### 8.4 Fehler-Verhalten

| Situation | Verhalten |
|---|---|
| Token unbekannt (kein Member matcht) | HTTP 404, kein Body, kein Audit-Log |
| Member existiert, hat aber `ical_token IS NULL` (Race-Condition nach Disable) | HTTP 404, kein Body |
| Member ist inaktiv (`is_active = false`) | HTTP 404, kein Body — Feed wird nicht mehr ausgeliefert |
| Datenbank-Fehler | HTTP 500, Standard-Error-Handler |

Konservatives 404 statt 401/403, weil wir keine Existenz-Information an unbekannte Aufrufer leaken wollen.

## 9. Routes

### 9.1 Public Feed-Endpoint

Neuer Blueprint `backend/routes/calendar_feed.py`:

```python
@calendar_feed_bp.route('/calendar/<token>.ics', methods=['GET'])
def member_feed(token: str):
    # 1. Token-Lookup über Member.ical_token
    # 2. 404 falls Miss, inaktiv oder Token NULL
    # 3. CalendarFeedService.generate_feed_for_member(member)
    # 4. Response mit Content-Type, Cache-Control, ETag-Header
```

- **Kein** `@login_required` — Authentifizierung läuft über den Token in der URL.
- **Kein** AuditEvent pro Request — sonst ertrinkt das Log im Polling-Verkehr.

### 9.2 Member-Settings-Endpoints

In `backend/routes/member.py` (oder neuer Settings-Blueprint, falls vorhanden):

```python
POST /member/settings/calendar/enable     -> enable_feed_for_member  -> 201 + Token-URL
POST /member/settings/calendar/regenerate -> regenerate_token        -> 200 + neue URL
POST /member/settings/calendar/disable    -> disable_feed            -> 204
```

Alle drei sind `@login_required` und operieren nur auf dem eigenen Member-Record.

### 9.3 Admin-Status-Endpoint

In der bestehenden Admin-Member-Detail-View ein zusätzliches read-only-Element «iCal-Abo aktiv seit YYYY-MM-DD» bzw. «kein iCal-Abo». Es gibt **keine** Möglichkeit für den Admin, den Token selbst zu sehen oder zu regenerieren — die Aktionen bleiben beim Mitglied.

«Aktiv seit»-Zeitstempel wird aus dem AuditEvent `CALENDAR_FEED_ENABLED` abgelesen (kein eigenes Spalten-Feld nötig).

## 10. UX in der App

### 10.1 Member-Settings-Sektion

Neuer Card-Block «Kalender abonnieren» in der Settings-Seite des Mitglieds, mit drei UI-States.

#### State 1 — nicht aktiviert

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Vereinskalender abonnieren                              │
│                                                             │
│  Behalte alle Vereinstermine in deinem persönlichen         │
│  Kalender — synchron mit der App.                           │
│                                                             │
│  Funktioniert mit Apple Calendar, Google Calendar und       │
│  Outlook.                                                   │
│                                                             │
│  [  Kalender-Abo aktivieren  ]                              │
└─────────────────────────────────────────────────────────────┘
```

Klick auf Button → POST `/member/settings/calendar/enable` → View springt in State 2.

#### State 2 — aktiviert

```
┌─────────────────────────────────────────────────────────────┐
│  📅 Vereinskalender                                         │
│                                                             │
│  Dein persönlicher Link:                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ https://gourmen.ch/calendar/Ab3kL...x9q.ics    [📋]  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  [  In Apple-Kalender öffnen  ]   ← nur iOS/macOS sichtbar │
│                                                             │
│  ▼ Wie binde ich den Kalender ein?                          │
│     ▸ Apple Calendar (iPhone/iPad/Mac)                      │
│     ▸ Google Calendar                                       │
│     ▸ Outlook                                               │
│                                                             │
│  Hinweis: Änderungen erscheinen je nach Kalender-App nach   │
│  einigen Minuten bis zu 24 Stunden.                         │
│                                                             │
│  Link neu erzeugen · Kalender-Abo deaktivieren              │
└─────────────────────────────────────────────────────────────┘
```

Der Copy-Button kopiert die volle URL inklusive `https://`. Der «In Apple-Kalender öffnen»-Button rendert nur, wenn das User-Agent auf iOS oder macOS hindeutet — der Button verwendet ein `webcal://`-Schema, das macOS und iOS automatisch an Apple Calendar routen.

«Link neu erzeugen» und «Kalender-Abo deaktivieren» sind sekundäre Aktionen als kleine Links unter dem Card-Block, jeweils mit Bestätigungs-Dialog.

#### Regenerate-Dialog

```
Link neu erzeugen?

Dein bisheriger Kalender-Link wird sofort ungültig. Wo immer du
ihn schon eingebunden hast (Apple Calendar, Google Calendar,
Outlook), musst du den neuen Link nochmal einfügen.

  [ Abbrechen ]      [ Neu erzeugen ]
```

#### Disable-Dialog

```
Kalender-Abo deaktivieren?

Dein Link wird ungültig und Vereinstermine erscheinen nicht
mehr in deinem Kalender. Du kannst das Abo jederzeit wieder
aktivieren — du bekommst dann allerdings einen neuen Link.

  [ Abbrechen ]      [ Deaktivieren ]
```

### 10.2 Anleitungs-Texte für die drei Plattformen

Im Akkordeon unter dem Link, ein Eintrag pro Plattform. Erst-Entwurf (Tonart bitte korrigieren):

**Apple Calendar (iPhone/iPad/Mac)**

> 1. Tippe oben auf **In Apple-Kalender öffnen** — der Kalender öffnet sich automatisch und fragt, ob du das Abo hinzufügen willst.
> 2. Auf dem Mac: Kalender öffnen → Ablage → Neues Kalender-Abonnement → Link einfügen.
> 3. Bestätige mit **Abonnieren**.

**Google Calendar**

> 1. Kopiere oben den Link.
> 2. Öffne [calendar.google.com](https://calendar.google.com) am Computer (in der mobilen App geht es nicht).
> 3. Links unter **Weitere Kalender** auf das **+** klicken → **Per URL** → Link einfügen → **Kalender hinzufügen**.
> 4. Der Vereinskalender erscheint danach auch in der Google-Calendar-App auf deinem Smartphone.

**Outlook**

> 1. Kopiere oben den Link.
> 2. In Outlook (Desktop oder Web) → **Kalender hinzufügen** → **Aus dem Internet abonnieren** → Link einfügen.
> 3. Auf Outlook.com geht das unter **Kalender hinzufügen → Aus dem Web abonnieren**.

### 10.3 Admin-Sicht

Im Admin-Member-Detail eine zusätzliche kleine Zeile:

```
Kalender-Abo:  aktiv seit 12.05.2026
                — bzw. —
Kalender-Abo:  nicht aktiv
```

Token-Wert wird nie angezeigt, weder im UI noch in Audit-Log-Details (im AuditEvent steht nur «enabled», nicht der Token-String).

### 10.4 Sprache und Stil

DB-Spalten-Namen bleiben englisch (`ical_token`, `ical_sequence`), UI-Labels sind deutsch, schweizerische Schreibweise mit Guillemets «…». Doppel-S statt Eszett. BEM-Klassen und Design-Tokens gemäss `docs/UI.md`.

## 11. Caching, Rate-Limit, Performance

### 11.1 Cache-Header

```
Cache-Control: private, max-age=300
ETag: "<sha256 des Feed-Inhalts>"
```

- `private` verhindert öffentliches Proxy-Caching (Token im URL).
- `max-age=300` (5 min) reduziert Last bei aggressiv pollenden Clients.
- ETag-Vergleich: bei unverändertem Feed antwortet der Server mit `304 Not Modified` und sparte den Body — bei mittlerem Vereins-Volumen vernachlässigbar, aber sauberer HTTP-Stil.

### 11.2 Rate-Limit

`60 Requests / Minute pro Token`, alles darüber → HTTP `429 Too Many Requests`.

Begründung: legitimes Polling auch bei aggressivster Apple-Calendar-Einstellung (5 min) liegt bei 12 Requests/h — Faktor 300 unter dem Limit. Schützt vor fehlerhaft konfigurierten Clients (Endlos-Schleife) und Scrapern. Kein IP-Limit, weil Familien- und Vereins-NAT kollidieren würden.

Implementation: bestehender Flask-Limiter falls vorhanden, sonst kleiner eigener Decorator mit Redis-Counter (Redis ist auf Railway bereits aufgesetzt für andere Cronjob-Locks).

### 11.3 Feed-Grösse

Pro Event ca. 400 Bytes inkl. allen Properties. Bei realistisch ~30 zukünftigen Events im Worst Case → ~12 KB Feed-Body plus VTIMEZONE-Header. Vernachlässigbar.

### 11.4 DB-Last

Pro Feed-Request: ein SELECT auf `Event` mit Filter `published=true AND datum >= now()`, plus Join auf `Member` für den Organisator-Namen. Mit dem bestehenden Index auf `events.datum` ist das ein Index-Range-Scan über ~30 Rows. Vernachlässigbar.

## 12. Audit-Log-Strategie

### 12.1 Was geloggt wird

| Event | Auslöser |
|---|---|
| `CALENDAR_FEED_ENABLED` | Mitglied aktiviert Kalender-Abo |
| `CALENDAR_FEED_REGENERATED` | Mitglied erzeugt Link neu |
| `CALENDAR_FEED_DISABLED` | Mitglied deaktiviert Kalender-Abo |

Event-Lebenszyklus (Erstellen, Bearbeiten, Löschen) wird nicht hier dokumentiert — das ist Sache der bestehenden Event-Capability.

### 12.2 Was bewusst nicht geloggt wird

- **Einzelne Feed-Requests**: Apple Calendar pollt alle 15 min, das ergibt pro Mitglied 100 Requests/Tag. Audit-Log wäre nach einer Woche unbrauchbar.
- **Token-Wert** in den `_ENABLED`/`_REGENERATED`-Events: das wäre ein Token-Leak im Audit-Log. Stattdessen nur «enabled», ohne Wert.

### 12.3 Liveness-Information

Bewusst **kein** `Member.ical_last_fetched_at`-Tracking. Wer den Kalender abonniert hat, ergibt sich aus `ical_token IS NOT NULL`. Eine «letzte Aktivität»-Metrik wäre nice-to-have, kostet aber pro Feed-Request einen DB-Write und ist für die Vereinsgrösse ohne Mehrwert (Andreas kennt seine Mitglieder).

## 13. AI/Automation — geprüft und verworfen

Die Strategie 2026 verlangt für jede Capability eine ehrliche Sektion zu AI/Automation-Optionen. Für die iCal-Feed-Capability lautet die Antwort: **nicht im Scope.**

| Ansatz | Bewertung |
|---|---|
| AI-generierte Event-Beschreibungen (Restaurant-Charakterisierung) | Nicht hier. Mehrwert mager, weil Kalender-Apps DESCRIPTION oft nur als kleines Textfeld zeigen. Falls AI später in die Event-Erstellung einzieht (STRATEGY_2026 «AI/Automation-Diskussionsfelder»), profitiert der Feed passiv mit, ohne dass die iCal-Capability dafür AI-Code braucht. |
| AI-generierte VALARM-Texte | Entfällt — keine VALARMs im Feed (Sektion 13.4). |
| AI-SUMMARY-Varianten | Entfällt. Wiedererkennbarkeit (`[Emoji] Gourmen - [Restaurant]`) schlägt Variation. |
| Anomalie-Erkennung «wer hat seit X Wochen nicht mehr abgerufen?» | Entfällt — `ical_last_fetched_at` bewusst weggelassen (12.3). |
| Natural-Language-Subscribe-Anleitung (Chatbot statt Akkordeon) | Overkill für drei statische Plattform-Anleitungen. |

**Entscheidung**: Kein AI-Einsatz im iCal-Feed-MVP. Die Capability ist eine reine Transformations-Schicht. AI-Hebel liegt potenziell upstream (Event-Erstellung) und downstream (Public-Page-Texte), nicht in der iCal-Generierung selbst.

### 13.4 Kein VALARM im Feed

Erinnerungen werden bewusst **nicht** als `VALARM` mitgeschickt. Begründung: die App sendet bereits Push-Reminder über VAPID (drei bestehende Cronjobs: 3-Wochen, Wochen, Rating). Eine zusätzliche Kalender-Erinnerung würde Doppelbenachrichtigung erzeugen.

Offener Punkt (in Sektion 19): interne Entscheidung steht aus, ob langfristig App-Push oder Kalender-Reminder der Default-Kanal sein soll. Bis dahin gilt: App-Push allein, kein VALARM.

## 14. Datenschutz

### 14.1 Was im Feed steht

- Event-Datum, Restaurant-Name und -Adresse, Notiz-Text, Event-Typ, App-URL.
- Organisator-Anzeigename (Spirit + Rufname). Keine Klartext-Mail-Adresse des Organisators — nur die Sammeladresse `kontakt@gourmen.ch`.

### 14.2 Was nicht im Feed steht

- Teilnehmerlisten, persönliche Anmeldedaten, BillBro-Beträge, GGL-Stände.
- Mitglieds-Mail-Adressen, Wohnadressen, Telefonnummern.
- Sensible Felder aus `MemberSensitive`.

### 14.3 Datenschutz-Hinweis

In die noch zu erstellende Datenschutz-Erklärung (siehe `docs/capabilities/drive.md` Sektion 13.3) wird ein Absatz aufgenommen:

> Kalender-Abos: Wenn du das Kalender-Abo aktivierst, generieren wir einen geheimen Link, der die Vereinstermine als iCal-Datei ausliefert. Der Link enthält ein Zufalls-Token, das deinem Mitglied-Konto eindeutig zugeordnet ist. Über den Link werden Datum, Ort und kurze Beschreibung veröffentlichter Vereinstermine übertragen — keine Teilnehmerlisten, keine persönlichen Daten anderer Mitglieder. Du kannst den Link jederzeit deaktivieren oder neu erzeugen.

Kein Blocker für Implementation, weil der Feed keine über die App hinaus neuen Daten preisgibt.

### 14.4 Token-Leak-Szenario

Bei kompromittiertem Token (z.B. versehentlich in einem öffentlichen Chat gepostet) kann das Mitglied selbst regenerieren — alter Token sofort ungültig, neuer Token in zwei Klicks aktiv. Kein Admin-Eingriff nötig. AuditEvent `CALENDAR_FEED_REGENERATED` dokumentiert den Vorgang.

## 15. Operations

### 15.1 Monitoring

Nichts Eigenes. Standard-Railway-Metriken (Request-Count, 4xx/5xx-Rate auf dem Feed-Endpoint) reichen für Anomalie-Erkennung. Bei auffällig vielen 404 auf `/calendar/*.ics` würde ein altes Token-Leak oder Polling-Schleifen vom Ex-Mitglied entdeckt — manueller Check auf Vorstandsebene.

### 15.2 Backups

Nichts Eigenes. Member- und Event-Daten sind durch das bestehende Postgres-Backup abgedeckt. `ical_token`-Werte sind reproduzierbar (Mitglied regeneriert), kein Recovery-Pfad nötig.

### 15.3 Rotation

Keine technische Rotation. `ical_token`-Tokens bleiben bestehen, bis das Mitglied regeneriert oder deaktiviert. Optional künftig: Cronjob, der Tokens älter als X Jahre invalidiert — heute nicht relevant.

## 16. Verzahnung mit Folge-Capabilities

### 16.1 Backlog: Vorstandssitzungen

Sobald Vorstandssitzungen als eigener Event-Typ kommen, wird ein `Event.audience`-Feld (`all`, `board`) eingeführt. Der Feed-Filter wird erweitert: Standard-Feed zeigt nur `audience='all'`, Vorstand-Mitglieder sehen zusätzlich `audience='board'`. Trigger für diese Erweiterung ist die Schaffung des Event-Typs selbst — kein Pre-Build im aktuellen MVP.

### 16.2 Backlog: Mehrtages-Container-Events

Ausflüge sind heute eine Sequenz einzelner Tages-Events (ein Event pro Essen). Falls künftig ein zusätzlicher «Reise-Container-Event» fürs Gesamt-Datum gebraucht wird, käme im Feed ein VEVENT mit `DTSTART;VALUE=DATE` und Mehrtages-`DTEND` dazu (All-Day-Event). Modell-Erweiterung wäre minimal: neuer `EventType.REISE_CONTAINER` oder ein Multi-Day-Flag.

### 16.3 Event-Erstellung (AI-Hebel laut STRATEGY_2026)

Wenn AI-Vorschläge bei der Event-Erstellung eingebaut werden (Restaurant-Vorschläge, Auto-Beschreibungen), profitiert der Feed-Inhalt passiv ohne Code-Änderung in dieser Capability — die Texte landen über die normalen DB-Felder im Feed.

### 16.4 Drive-Capability

Keine direkte Verzahnung. Drive ist Storage für Dokumente, iCal ist Anzeige-Schicht für Events. Allenfalls könnten Event-Detail-Seiten in der App auf zugehörige Drive-Dokumente verlinken (z.B. Reise-Programm), aber das ist UX-Detail der App, nicht des Feeds.

### 16.5 Public-Seite

Out of Scope hier. Eine öffentliche Variante «kommende Vereinstermine auf gourmen.ch sichtbar» wäre eine separate Public-Page-Capability, nicht Teil des iCal-Feeds.

## 17. Cursor-Briefing für Phase 5

### 17.1 Reihenfolge der Commits

| # | Commit | Inhalt |
|---|---|---|
| 1 | Schema-Migration: Member | `ical_token VARCHAR(64) UNIQUE INDEXED NULLABLE` |
| 2 | Schema-Migration: Event | `ical_sequence INT NOT NULL DEFAULT 0` |
| 3 | Service-Layer | `backend/services/calendar_feed.py` inkl. VTIMEZONE-Build, SUMMARY-Format, ETag-Berechnung, Token-Lifecycle-Methoden. Unit-Tests gegen iCalendar-Validator. |
| 4 | SEQUENCE-Bump-Integration | Event-Service-Hook, der bei Edits auf relevante Felder `ical_sequence += 1` macht. Liste der relevanten Felder gemäss Sektion 8.3. |
| 5 | Routes und UI | Public Feed-Endpoint, Member-Settings-Sektion (drei States), Admin-Detail-Anzeige. |
| 6 | Rate-Limit & Cache-Header | Limiter-Decorator, `Cache-Control`-Header, ETag-Logik. |

### 17.2 Cursor-Briefing-Block

```
Branch: phase/05-workspace-ical-feed
Lies vor Implementation: docs/capabilities/calendar.md (autoritativ).
Lies docs/initiatives/workspace-railway/PHASE_05_ICAL_FEED.md nur für Rahmen.

Implementations-Reihenfolge: Migrationen (Member, Event) → Service-Layer
mit Tests → SEQUENCE-Bump-Hook → Routes/UI → Rate-Limit/Cache.

Zwei Migrationen sind separate Alembic-Commits. Service-Layer und
Routes/UI sind eigene Code-Commits.

Library: icalendar (PyPI), nicht ics — wegen sauberem VTIMEZONE-Support.

Token-Format: secrets.token_urlsafe(32). Token NIEMALS in Audit-Log
oder Admin-UI im Klartext.

UX-Texte deutsch, schweizerische Schreibweise mit Guillemets («…»),
Doppel-S statt Eszett. BEM-Klassen und Tokens gemäss docs/UI.md.

Lokale Verifikation:
- Feed-Endpoint aufrufen, Output gegen https://icalendar.org/validator.html prüfen
- In Apple Calendar abonnieren (webcal://-Link aus den Settings)
- Test-Update an einem Event (Datum verschieben) → SEQUENCE-Bump
  → in Apple Calendar binnen 15 Min sichtbar
- Test-Cancel an einem Event → Eintrag wird gestrichen
```

### 17.3 Akzeptanzkriterien für Phase 5

- [ ] Member kann in Settings das Kalender-Abo aktivieren, neuen Link erzeugen, deaktivieren
- [ ] Feed-URL liefert RFC-5545-konformes iCal (Validator-Pass)
- [ ] VTIMEZONE für Europe/Zurich ist im Feed enthalten
- [ ] Veröffentlichte zukünftige Events erscheinen mit SUMMARY `[Emoji] Gourmen - [Restaurant]`
- [ ] DTSTART/DTEND immer 18:00–23:00 Europe/Zurich, unabhängig vom DB-Zeitfeld
- [ ] LOCATION enthält Restaurant + Adresse, fällt sauber weg wenn beide leer
- [ ] DESCRIPTION enthält Notiz + Link zur App-Detail-Seite
- [ ] ORGANIZER enthält Spirit + Rufname als CN und `kontakt@gourmen.ch` als Mail
- [ ] CATEGORIES enthält Event-Typ
- [ ] Vergangene Events erscheinen nicht im Feed
- [ ] Gelöschtes Event verschwindet beim nächsten Polling aus den abonnierten Kalendern (Apple, Google)
- [ ] Verschobenes Event behält UID, neue Zeit, höhere `SEQUENCE`
- [ ] Unbekannter Token → 404, kein Audit-Log-Eintrag
- [ ] Cache-Control und ETag werden gesetzt; bei unverändertem Inhalt 304
- [ ] Rate-Limit 60/min pro Token greift
- [ ] In Apple Calendar abonniert und Update binnen 15 Min sichtbar
- [ ] In Google Calendar (Desktop, «Per URL hinzufügen») abonniert und Events sichtbar
- [ ] Admin-View zeigt «Kalender-Abo aktiv seit YYYY-MM-DD» bzw. «nicht aktiv»
- [ ] AuditEvents `CALENDAR_FEED_ENABLED`/`REGENERATED`/`DISABLED` werden korrekt geloggt
- [ ] Tests grün, kein Token-Klartext in Logs

### 17.4 Out of Scope für Phase 5

- VALARM/Reminder im Feed (Push reicht; interne Klärung läuft)
- ATTENDEE-Liste im Feed (Privacy)
- Mehrere Feed-Varianten pro Mitglied (Variante B/C aus Capability-Doc 4.1)
- Sichtbarkeits-Filter `audience` (Backlog, mit Vorstandssitzungen)
- Mehrtages-Container-Events (Backlog)
- AI-generierte Inhalte
- Public-Calendar auf gourmen.ch
- Bidirektionaler Sync mit Google Calendar
- `ical_last_fetched_at`-Tracking
- Caldav-Server, Webhook-Push

## 18. Decision Log

| Datum | Entscheid | Begründung |
|---|---|---|
| 2026-05-14 | Pfad A: eigener iCal-Feed statt geteilter Google Calendar | Single Source of Truth in Postgres, keine Sync-Konflikte, gleiche UX für Apple/Google/Outlook über iCal-Subscribe |
| 2026-05-14 | Inhalts-Scope: alle veröffentlichten Events, kein Per-Member-Filter | Familiärer Verein, jeder will alles sehen; subjektive Filter erzeugen Client-Cache-Drift |
| 2026-05-14 | Zeit-Fenster: nur zukünftige Events (`datum >= today`) | Feed bleibt schlank, vergangene Termine sind im Kalender-Client schon persistiert |
| 2026-05-14 | Abgesagte Events werden in der App gelöscht, kein Cancel-Konzept im Modell | Eintrag fällt aus dem Feed-Query und verschwindet beim nächsten Polling aus dem Kalender; spart `cancelled`-Felder und UI-Toggle |
| 2026-05-14 | Update-Mechanik: gleiche UID + SEQUENCE+1 + neues DTSTART | iCal-Standard für «Update», Client verschiebt vorhandenen Eintrag statt neuen anzulegen |
| 2026-05-14 | Variante A: ein Feed pro Mitglied | Einfachster Token-Lifecycle, deckt 90% der Use-Cases ab |
| 2026-05-14 | DTSTART/DTEND: generell 18:00–23:00 Europe/Zurich | Events werden datumsgenau erfasst, Zeitangabe wäre Scheinpräzision |
| 2026-05-14 | Mehrtägige Events: nicht im MVP, Backlog | Heute durch ein Event pro Essen abgebildet, Container-Event ist späteres Feature |
| 2026-05-14 | SUMMARY-Format `[Emoji] Gourmen - [Restaurant]` mit Unicode-Emoji | RFC 5545 erlaubt im SUMMARY kein Markup, Unicode-Emoji ist der nächste Schritt zu den App-Icons |
| 2026-05-14 | ORGANIZER: CN aus Spirit+Rufname, mailto = `kontakt@gourmen.ch` | Organisator-Name sichtbar, persönliche Mail-Adresse geschützt, Antworten landen in Vereinsmailbox |
| 2026-05-14 | CATEGORIES mitsenden, ATTENDEE und VALARM weglassen | Categories kostenlos, Attendee-Privacy-Risiko, VALARM-Konflikt mit App-Push |
| 2026-05-14 | Token: `secrets.token_urlsafe(32)`, kein HMAC | Stateless-HMAC spart keine echte Arbeit, weil Member-DB-Lookup eh nötig |
| 2026-05-14 | Token-Auto-Erstellung erst bei Subscribe-Klick | Keine ungenutzten Tokens, klares Audit-Signal |
| 2026-05-14 | Kein `ical_last_fetched_at`-Tracking | DB-Write pro Polling-Request ohne erkennbaren Mehrwert für Vereinsgrösse |
| 2026-05-14 | Rate-Limit: 60 Requests / Minute pro Token | Faktor 300 über legitimem Polling, fängt Endlos-Schleifen und Scraper |
| 2026-05-14 | Cache: `private, max-age=300` + ETag | Reduziert Last bei aggressivem Polling, sauberer HTTP-Stil |
| 2026-05-14 | Library: `icalendar` statt `ics` | Sauberer VTIMEZONE-Support, RFC-5545-konform |
| 2026-05-14 | `Event.ical_sequence` als neues Feld | Pflicht für RFC-5545-Update-Semantik |
| 2026-05-14 | Webcal-Button nur auf iOS/macOS sichtbar | Apple-Handler ist verlässlich, Android/Desktop-Routing instabil |
| 2026-05-14 | Anleitungstexte für Apple/Google/Outlook im Capability-Doc | Tonart wichtig, im Capability-Doc gepflegt statt von Cursor erfunden |
| 2026-05-14 | Admin sieht Abo-Status, nicht Token-Wert | Support-Use-Case ohne Privacy-Bruch |
| 2026-05-14 | AI/Automation explizit nicht im Scope | Feed ist reine Transformations-Schicht, AI-Hebel liegt anderswo |

## 19. Offene Punkte und Trade-offs

- *VALARM-Strategie*: interne Klärung, ob langfristig App-Push oder Kalender-Reminder Default sein soll. Bis dahin: kein VALARM, nur Push. Wird im Mitglieder-Settings explizit erwähnt («Erinnerungen kommen über die App-Push»).
- *Datenschutz-Erklärung*: existiert noch nicht (siehe Drive-Capability Sektion 13.3). Wenn sie erstellt wird, ist der vorbereitete Absatz aus Sektion 14.3 zu übernehmen.
- *Outlook-Emoji-Rendering*: ältere Outlook-Clients (≤ 2019) zeigen die Emojis 🍴/🚐/🏛️ teils als Boxen. Akzeptiert; bei häufigen Beschwerden Wechsel auf Tag-Prefix (`[Monatsessen] Gourmen - …`) als Fallback.
- *SEQUENCE-Bump-Trigger*: Liste der relevanten Felder (Sektion 8.3) ist ein Sample. Falls in der Implementation auffällt, dass weitere Felder kalender-relevant sind, wird sie ergänzt.
- *Token-Rotation*: keine automatische Rotation alter Tokens. Bei der Vereinsgrösse irrelevant; falls künftig nötig, kommt es als kleiner Cronjob («Tokens älter als X Jahre invalidieren mit Mail-Hinweis»).
- *Public-Calendar*: ob auf der öffentlichen Seite eine reduzierte Termin-Vorschau angezeigt werden soll, ist Public-Page-Capability-Scope, nicht hier.
