# Architektur

Stabile High-Level-Übersicht zur Gourmen PWA. Bei substantiellen Architektur-Änderungen pflegen.

## Stack

- **Sprache**: Python 3.11
- **Framework**: Flask 3.x (App-Factory-Pattern)
- **ORM**: SQLAlchemy 2.x via Flask-SQLAlchemy
- **Migrationen**: Alembic via Flask-Migrate
- **DB Production**: PostgreSQL (psycopg v3 via `_normalize_database_url`)
- **DB Development**: SQLite (`instance/gourmen_dev.db`)
- **Auth**: Flask-Login + WTForms + pyotp (TOTP-2FA) + cryptography (Fernet)
- **Web-Server Production**: Gunicorn
- **Cache/Queue**: Redis (für Flask-Limiter-Storage, optional)
- **Frontend**: Server-rendered Jinja2 + Custom CSS V2 (BEM + Tokens) + Vanilla JS
- **PWA**: Service Worker (`static/sw.js`), Web Manifest, Push API mit VAPID
- **Hosting**: Railway (Web + Cron)

## Modul-Struktur

```
backend/
├── app.py              # App-Factory create_app()
├── config.py           # DevelopmentConfig / ProductionConfig / TestingConfig
├── extensions.py       # db, login_manager, csrf, limiter
├── models/             # SQLAlchemy Models
├── routes/             # Flask Blueprints (URL-Endpoints)
├── services/           # Business Logic (Service-Layer)
└── forms/              # FlaskForm-Definitionen (falls separat)

templates/              # Jinja2 Templates
├── partials/           # Layout-Shells, _head_*, Macros
├── auth/, events/, dashboard/, admin/, ...
└── errors/             # 404, 500, 403

static/
├── css/v2/             # Aktuelles Design-System (Tokens, Base, Components, Layout)
├── css/                # Spezialisiertes (animations, responsive, mobile-touch, …)
├── js/                 # app.js, pwa.js, google-maps.js, places-autocomplete.js
├── js/v2/              # Theme-Toggle, Tabs, Accordion, Search, ...
├── img/, icons/        # Statische Assets, Lucide-Sprite
├── sw.js               # Service Worker (von /sw.js ausgeliefert)
└── manifest.json       # PWA Manifest

migrations/             # Alembic-Migrationen
scripts/                # Einmal-Skripte und Tools (Seed, Migration, Asset-Gen)
docs/                   # Diese Dokumentation
```

## Blueprints

Registrierung in `backend/app.py`:

| Blueprint | URL-Prefix | Zweck |
|---|---|---|
| `public` | `/` | Landing, public Info |
| `auth` | `/auth` | Login, 2FA, Passwort-Reset |
| `dashboard` | `/dashboard` | Member-Dashboard |
| `events` | `/events` | Event-Liste, -Detail, Teilnahme |
| `billbro` | `/billbro` | Bill-Splitting-Berechnung |
| `ggl` | `/ggl` | Gourmen Guessing League Ranking |
| `member` | `/member` | Member-Profile, Settings |
| `admin` | `/admin` | Vereinsverwaltung: Dashboard `admin/index` mit **`.admin-hub`** (Hero-Kacheln, siehe `docs/UI.md`); Mitgliederliste und Merch-Übersicht **lesend** für alle aktiven Mitglieder (`verein_member_required`); Bearbeiten, sensible Daten, Security, Mail-Test und Merch-Mutationen nur `Role.ADMIN` (`admin_required`) |
| `notifications` | `/notifications` | **Legacy:** VAPID/Subscribe/Unsubscribe/Test (NotifierService); aktuelle Clients nutzen `push_notifications` unter `/api/...`. |
| `ratings` | `/ratings` | Event-Ratings |
| `push_notifications` | (root) | API für Web-Push: `/api/vapid-public-key`, `/api/push/subscribe`, `/api/push/subscription-status`, … |
| `cron` | (root) | Cron-Trigger-Endpoints (auth via Token) |

## Models (Auswahl)

- **`Member`** – Vereinsmitglied, UserMixin, Rollen `MEMBER`/`ADMIN`, mit `Funktion`-Enum
- **`MemberSensitive`** – verschlüsselte sensible Felder (Fernet via `CRYPTO_KEY`)
- **`MemberMFA`** + **`MFABackupCode`** – 2FA-Konfiguration
- **`Event`** – Vereinsevents (Monatsessen, Ausflug, Generalversammlung) mit Google-Places-Daten und BillBro-Kalkulationsfeldern
- **`Participation`** – Teilnahme an Event mit Rolle (sparsam/normal/allin), Schätzbetrag (für GGL), Punkten
- **`Document`** – Vereinsdokumente (aktuell als Links, Felder für File-Upload vorbereitet)
- **`EventRating`** – Bewertung eines Events (Food/Drinks/Service)
- **`MerchArticle/Variant/Order/OrderItem`** – Vereins-Merchandise-Shop
- **`PushSubscription`** – Web-Push-Subscriptions pro Member+Gerät
- **`AuditEvent`** – Audit-Log sensibler Aktionen

Detail siehe direkt im Code unter `backend/models/`.

## Service-Layer

Services in `backend/services/` sind die einzige Stelle für:

- Komplexe Business-Logik (BillBro-Kalkulation, GGL-Punkte)
- Verschlüsselung und 2FA (`SecurityService`)
- Externe Integrationen (Google Places, Web-Push, Resend/SMTP-Mail, Infomaniak Storage, Stripe, Meta)

**Routes** rufen Services, **Services** rufen Models. Routes enthalten keine Geschäftslogik außer Permission-Checks und Form-Handling.

Aktuelle Services:

| Service | Zweck |
|---|---|
| `SecurityService` | Hashing, Encryption (Fernet), 2FA, Step-Up-Auth, Audit-Log |
| `GGLService` | Ranking-Berechnung, Punkte, Saisonwertung |
| `MoneyService` | Beträge in Rappen rechnen, Rundung, Trinkgeld-Regeln |
| `PlacesService` | Google-Places-Lookup für Restaurant-Daten |
| `MailService` | Transaktionale E-Mails (Resend HTTPS oder SMTP) |
| `PushNotificationService` | Web-Push-Versand via pywebpush, Subscription-Mgmt |
| `VAPIDService` | VAPID-Key-Bereitstellung für Push |
| `CronService` | Reminder-Trigger (3-Wochen, Montag, Rating-Tag) |
| `NotifierService` | In-App-Notifications |
| `MonatsessenStatsService` | Statistiken über Monatsessen |
| `RatingPromptService` | Logik wann Rating angezeigt wird |
| `RetroCleanupService` | Datenbereinigungs-Workflow für Member |

## Auth-Flow

```
LOGIN
  ├─ POST /auth/login  (Email + Passwort)
  ├─ Member.check_password() (werkzeug)
  ├─ wenn 2FA aktiv:
  │     ├─ Remembered Device? → eingeloggt
  │     └─ sonst: Redirect /auth/2fa/verify
  └─ Login-Audit-Event

2FA VERIFY
  ├─ TOTP via pyotp (window=3 für Clock-Skew)
  ├─ alternativ Backup-Code (gehasht in DB)
  └─ Optional: "Remember this device"

STEP-UP (sensible Aktionen)
  ├─ Time-limitierter Re-Auth via Passwort
  ├─ TTL: SENSITIVE_ACCESS_TTL_SECONDS (default 300)
  └─ SecurityService.check_step_up_access()

SENSITIVE-FELDER (MemberSensitive, totp_secret_encrypted)
  └─ Fernet-Encryption via CRYPTO_KEY
     (CRYPTO_KEY-Verlust = Daten-Verlust!)

RESET / ONBOARDING TOKENS
  ├─ Tabelle auth_tokens (Hash statt Klartext, purpose + expires_at + used_at)
  ├─ Password-Reset via Mail (1h gueltig)
  ├─ 2FA-Reset via Mail (1h gueltig)
  └─ Onboarding-Aktivierung via Mail (7 Tage gueltig)
```

## PWA-Aspekte

- **Service Worker** wird vom Origin-Root unter `/sw.js` ausgeliefert (ausschliesslich Route in der App-Factory `create_app()` in `backend/app.py`, nicht im Public-Blueprint)
  - `Content-Type: application/javascript`
  - `Service-Worker-Allowed: /`
  - `Cache-Control: no-cache` (Updates müssen schnell wirken)
- **Cache-Buster** bei jedem UI-Deploy: siehe `docs/UI.md` Sektion „Cache-Buster"
- **Push-Notifications** via VAPID (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`); Subscriptions in DB
- **Client-Registrierung** in `static/js/pwa.js`: `navigator.serviceWorker.register('/sw.js', { scope: '/' })` (nicht `/static/`); legacies Scope `/static/` wird beim erfolgreichen Register entfernt
- **`member.technical`** (`templates/member/technical.html`): Einstellungs-Hub für **Push**, **Homescreen/PWA**, **Technik/Offline**; Verweis auf **`member.security`** (Passwort, 2FA). Auf **localhost** Hinweis/Toast wenn kein Service Worker (`?pwa_sw=1`), damit Push-Init nicht an `serviceWorker.ready` hängt (`static/js/app.js`).
- **Install-Hinweise** (iOS/Android, nur App-Shell): Schliessen (X) setzt einen **7-Tage**-Cooldown (`localStorage`-Timestamps, siehe `pwa.js`); Aktionen «Installieren» / «Push» schliessen nur das Banner ohne Cooldown; dauerhafte Kurzanleitung: **Einstellungen** (`member/technical`) – Card «App auf dem Homescreen»
- **Top-Leiste «Benachrichtigungen aktivieren»** (`pwa.js`): wird nur eingeblendet, wenn `/api/push/subscription-status` **keine** aktive Subscription meldet (und Berechtigung nicht `denied`); bei unklarem API-Resultat Fallback nur bei `Notification.permission === 'default'`; bei Tab-Fokus erneute Prüfung (throttled)
- **Basis-Healthcheck** `GET /health` nur in der App-Factory (`backend/app.py`); **`GET /health/db`** (DB-Ping) bleibt am Public-Blueprint (`backend/routes/public.py`)

### Service-Worker Caching-Strategie

- **Release-Version** (Cache-Buster): `const VERSION` in `static/sw.js` und `const PWA_VERSION` in `static/js/pwa.js` (siehe `scripts/update_pwa_version.py`)

| Request-Typ | Strategie | Cache | Begründung |
|---|---|---|---|
| **HTML / Navigation** (`request.mode === 'navigate'` oder `Accept: text/html`) | `networkOnlyHtml` mit `cache: 'no-store'`, optional Navigation Preload | **kein** SW-Cache | HTML ist fluechtig + version-gebunden; aus dem Cache zurueckgespielte Seiten waren die Hauptursache fuer „Updates kommen nicht an". |
| **Static Assets** (gehashte Filenames in `STATIC_ASSETS`) | `cacheFirst(STATIC_CACHE)` | versioniert (`gourmen-static-v<X>`) | Hash im Filename → Inhalt unveränderlich, sofortiger Hit. |
| **API / sonstige GETs** | `networkFirst(DYNAMIC_CACHE)` | versioniert (`gourmen-dynamic-v<X>`) | Frische Daten bevorzugt, Offline-Fallback aus Cache. |
| **Offline-Fallback** | `caches.match('/static/offline.<hash>.html')` | STATIC_CACHE | Wird nur bei Netzwerkfehler ausgeliefert. |

### Update-Pfad (skipWaiting + clients.claim)

1. **Install** des neuen SW: `self.skipWaiting()` synchron im Install-Handler → kein `waiting`-State.
2. **Activate** des neuen SW:
   - alle Caches mit nicht-aktivem Namen werden geloescht;
   - der eigene `DYNAMIC_CACHE` wird zusaetzlich frisch geleert (gegen HTML-Reste aus Vorversionen);
   - `navigationPreload.enable()` (falls verfuegbar);
   - `self.clients.claim()` → der neue SW kontrolliert sofort alle offenen Tabs;
   - alle Clients erhalten `postMessage({ type: 'SW_ACTIVATED', ... })`.
3. **Client** (`static/js/pwa.js`):
   - `controllerchange`-Listener triggert genau **einmal** ein `window.location.reload()` (Reload-Guard `_reloadingForUpdate`);
   - die allererste Aktivierung (vorher kein Controller) reloadet **nicht**, weil die Page bereits korrekt laeuft.

Praktische Konsequenz: Ein neuer Deploy braucht keinen manuellen Cache-Clear mehr. Tab offen lassen → spaetestens beim naechsten Update-Check (alle 5 min oder beim Fokus) installiert sich der neue SW, claimt die Page und reloadet einmal.

## Cron-Jobs

`run_cron_reminders.py` ist ein **One-Shot-Script** (kein Daemon), wird vom Hosting-Scheduler aufgerufen. Steuerung via `SERVICE_TYPE=cron` in `start.sh`.

Drei Reminder-Typen:

1. **3-Wochen-Reminder** – täglich, prüft Events 21 Tage in der Zukunft
2. **Wochen-Reminder** – nur Montags, für Events in derselben Woche
3. **Rating-Reminder** – täglich, für Events vom Vortag

## Externe Services

| Service | Zweck | Status |
|---|---|---|
| **Railway** | App-Hosting (Web + Cron + Postgres + Redis-Plugin) | aktiv |
| **Google Places API** | Restaurant-Daten beim Event-Anlegen | aktiv |
| **Google Maps API** | Karten-Anzeige im Frontend | aktiv |
| **Infomaniak** | Domain/DNS, Object Storage | aktiv |
| **Resend (HTTPS)** | Transaktionale E-Mails aus der App (Production, empfohlen) | aktiv (Phase 2) |
| **SMTP (Infomaniak / sonst)** | Transaktionale E-Mails lokal oder mit SMTP-faehigem Hosting | optional |
| **RaiseNow / Stripe** (geplant) | TWINT-Zahlungen | geplant Phase 6 |
| **Meta Cloud API** (geplant) | WhatsApp Business | geplant Phase 7 |

Aktive Initiative: `docs/initiatives/workspace-railway/` (aeltere Detailphasen: `modules-and-hosting/`). Strategischer Rahmen: `docs/STRATEGY_2026.md`.

## Datenfluss-Beispiele

### Event-Anlage (Admin)

```
Admin → /admin/events/new (POST)
  → EventForm.validate_on_submit
  → Wenn place_id gesetzt:
      → PlacesService.lookup_place(place_id) → Place-Felder befüllen
  → Event() insert + Participations für alle Members anlegen
  → Audit-Log
  → Redirect /events/<id>
```

### BillBro-Eingabe (Member)

```
Member → /events/<id>/billbro/guess (POST)
  → Schätzbetrag in Participation.guess_bill_amount_rappen
  → Audit-Log

Nach Event (Rechnungsbetrag eingetragen):
  → MoneyService berechnet Anteile pro Rolle
    (sparsam=0.7, normal=1.0, allin=1.3)
  → MoneyService berechnet Trinkgeld + Rundung
  → GGLService.calculate_event_points(event_id)
    → fractional ranking nach Differenz
    → Punkte (N - rank + 1)
```

### Push-Reminder (Cron)

```
Cron-Trigger → run_cron_reminders.py
  → CronService.run_3_week_reminders()
    → Events 3 Wochen in Zukunft finden
    → für jeden Member mit Push-Subscription:
        → PushNotificationService.send_push_notification(...)
    → Audit-Log
```

## Bekannte Schwächen

- **`Document`-Model**: Felder für File-Upload vorbereitet, aber bisher nur URLs. Wird in Phase 3 implementiert.
- **Drei Hilfs-Routes** (`init_db`, `migrate`, `test_migrate`): einmalige Migration-Helper, sollten bei Cleanup entfernt werden.
- **Tests**: aktuell kein automatisches Test-Setup. Manuell + Production-Smoke-Testing.
