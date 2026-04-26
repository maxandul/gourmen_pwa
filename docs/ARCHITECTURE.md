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
| `admin` | `/admin` | Admin-Bereich (Members, Events) |
| `notifications` | `/notifications` | In-App Notifications |
| `ratings` | `/ratings` | Event-Ratings |
| `push_notifications` | (root) | API für Web-Push-Subscriptions |
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
- Externe Integrationen (Google Places, Web-Push, später Resend, R2, Stripe, Meta)

**Routes** rufen Services, **Services** rufen Models. Routes enthalten keine Geschäftslogik außer Permission-Checks und Form-Handling.

Aktuelle Services:

| Service | Zweck |
|---|---|
| `SecurityService` | Hashing, Encryption (Fernet), 2FA, Step-Up-Auth, Audit-Log |
| `GGLService` | Ranking-Berechnung, Punkte, Saisonwertung |
| `MoneyService` | Beträge in Rappen rechnen, Rundung, Trinkgeld-Regeln |
| `PlacesService` | Google-Places-Lookup für Restaurant-Daten |
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
```

## PWA-Aspekte

- **Service Worker** wird vom Origin-Root unter `/sw.js` ausgeliefert (siehe `app.py` Route)
  - `Content-Type: application/javascript`
  - `Service-Worker-Allowed: /`
  - `Cache-Control: no-cache` (Updates müssen schnell wirken)
- **Cache-Buster** bei jedem UI-Deploy: siehe `docs/UI.md` Sektion „Cache-Buster"
- **Push-Notifications** via VAPID (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`); Subscriptions in DB
- **Asset-Manifest** mit Cache-Bust-Hashes (`scripts/fingerprint_assets.py`)

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
| **Cloudflare** (geplant) | Domain-Registrar, DNS, R2 für Files | geplant Phase 0 |
| **Resend** (geplant) | Transaktionale E-Mails | geplant Phase 1 |
| **RaiseNow / Stripe** (geplant) | TWINT-Zahlungen | geplant Phase 6 |
| **Meta Cloud API** (geplant) | WhatsApp Business | geplant Phase 7 |

Aktive Initiative für die Erweiterung: `docs/initiatives/modules-and-hosting/`.

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

- **Login-Reset-Flow**: Token aktuell in Flask-Session statt DB → nur im selben Browser nutzbar. Wird in Phase 2 gefixt.
- **`Document`-Model**: Felder für File-Upload vorbereitet, aber bisher nur URLs. Wird in Phase 3 implementiert.
- **Drei Hilfs-Routes** (`init_db`, `migrate`, `test_migrate`): einmalige Migration-Helper, sollten bei Cleanup entfernt werden.
- **Tests**: aktuell kein automatisches Test-Setup. Manuell + Production-Smoke-Testing.
