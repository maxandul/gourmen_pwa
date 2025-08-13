# Gourmen Webapp

Eine mobile-first Vereins-Webapp für den Gourmen-Verein mit Flask.

## Features

- **Mobile-first Design** mit PWA-Unterstützung
- **Sichere Authentifizierung** mit 2FA (TOTP ohne QR)
- **Event-Management** mit Teilnahme-Tracking
- **BillBro-Schätzspiel** mit fractional ranking
- **GGL (Gourmen Guessing League)** für Saisonwertungen
- **Dokumenten-Management** mit Soft-Delete
- **Audit-Logging** für sensible Aktionen
- **Verschlüsselte sensible Daten** mit Step-Up-Authentifizierung

## Technologie-Stack

- **Backend**: Flask 3.x, SQLAlchemy 2.x, Alembic
- **Datenbank**: SQLite (Development), PostgreSQL (Production)
- **Security**: Flask-Login, Flask-WTF, pyotp, cryptography
- **Frontend**: Mobile-first CSS, PWA
- **Deployment**: Railway mit Gunicorn

## Setup

### Voraussetzungen

- Python 3.12+
- pip

### Lokale Entwicklung

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd gourmen_webapp
   ```

2. **Virtuelle Umgebung erstellen**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   venv\Scripts\activate     # Windows
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren**
   ```bash
   cp env.example .env
   # .env bearbeiten und CRYPTO_KEY generieren:
   # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

5. **Datenbank initialisieren**
   ```bash
   flask db init
   flask db migrate -m "initial schema"
   flask db upgrade
   ```

6. **Anwendung starten**
   ```bash
   flask run
   ```

Die App ist dann unter `http://localhost:5000` verfügbar.

### Admin-Account

Der Admin-Account wird automatisch erstellt mit den Credentials aus der `.env`:
- E-Mail: `INIT_ADMIN_EMAIL`
- Passwort: `INIT_ADMIN_PASSWORD`

## Umgebungsvariablen

| Variable | Beschreibung | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask-Umgebung | `development` |
| `SECRET_KEY` | Flask Secret Key | `change_me_in_production` |
| `DATABASE_URL` | Datenbank-URL | `sqlite:///gourmen_dev.db` |
| `TZ` | Zeitzone | `Europe/Zurich` |
| `TWOFA_ISSUER` | 2FA Issuer | `Gourmen` |
| `CRYPTO_KEY` | Fernet-Schlüssel | **erforderlich** |
| `SENSITIVE_ACCESS_TTL_SECONDS` | Step-Up TTL | `300` |
| `INIT_ADMIN_EMAIL` | Admin-E-Mail | `admin@gourmen.ch` |
| `INIT_ADMIN_PASSWORD` | Admin-Passwort | `change_me_admin` |

## Datenbank-Migrationen

```bash
# Neue Migration erstellen
flask db migrate -m "Beschreibung der Änderung"

# Migrationen anwenden
flask db upgrade

# Migrationen rückgängig machen
flask db downgrade
```

## Railway Deployment

1. **Railway-Projekt erstellen**
2. **GitHub-Repository verbinden**
3. **Umgebungsvariablen setzen**:
   - `FLASK_ENV=production`
   - `DATABASE_URL` (Railway PostgreSQL)
   - `SECRET_KEY` (starkes Secret)
   - `CRYPTO_KEY` (Fernet-Schlüssel)
   - Alle anderen Variablen

4. **Deploy** - Railway erkennt automatisch die `Procfile`

## Projektstruktur

```
gourmen_webapp/
├── backend/
│   ├── app.py              # Flask App Factory
│   ├── config.py           # Konfiguration
│   ├── extensions.py       # Flask Extensions
│   ├── models/             # SQLAlchemy Models
│   ├── routes/             # Blueprint Routes
│   └── services/           # Business Logic
├── templates/              # Jinja2 Templates
├── static/                 # CSS, JS, Images
├── migrations/             # Alembic Migrations
├── requirements.txt        # Python Dependencies
├── Procfile               # Railway Deployment
└── README.md              # Diese Datei
```

## Sicherheit

- **Passwort-Policy**: Mindestens 12 Zeichen
- **2FA**: TOTP ohne QR-Code (mobile-first)
- **Verschlüsselung**: Fernet für sensible Daten
- **Step-Up**: Erneute Authentifizierung für sensible Aktionen
- **Audit-Logging**: Alle sensiblen Aktionen werden protokolliert
- **CSRF**: Globale CSRF-Schutz
- **Rate-Limiting**: Login und Step-Up

## Mobile-First Features

- **Bottom Navigation**: Touch-optimierte Navigation
- **Responsive Design**: Mobile bis Desktop
- **PWA**: Installierbar als App
- **Touch-Friendly**: Mindestens 44px Touch-Targets
- **Offline-Support**: Service Worker Cache

## API-Endpunkte

### Öffentlich
- `GET /` - Landing Page
- `GET /health` - Health Check
- `GET /health/db` - Database Health Check

### Authentifiziert
- `GET /dashboard` - Dashboard
- `GET /events` - Events Liste
- `GET /events/<id>` - Event Details
- `POST /events/<id>/rsvp` - Teilnahme
- `GET /ggl` - GGL Übersicht
- `GET /account/profile` - Profil

### Admin
- `GET /admin/members` - Member-Management
- `GET /admin/events/new` - Event erstellen
- `GET /docs` - Dokumenten-Management

## Entwicklung

### Code-Style
- Keine Eszett (ß) im Code/Kommentaren
- Deutsche Kommentare und Strings
- PEP 8 für Python
- Mobile-first CSS

### Testing
```bash
# Tests ausführen (wenn implementiert)
python -m pytest

# Coverage (wenn implementiert)
python -m pytest --cov=backend
```

## Support

Bei Fragen oder Problemen:
- E-Mail: info@gourmen.ch
- GitHub Issues: [Repository-URL]/issues

## Lizenz

Intern für den Gourmen-Verein. 