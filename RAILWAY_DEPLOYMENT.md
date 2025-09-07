# Railway Deployment Guide

## 🚀 Deployment Checklist

### ✅ Vorbereitung abgeschlossen:
- [x] `requirements.txt` mit allen Dependencies
- [x] `runtime.txt` mit Python Version
- [x] `railway.json` mit korrekter Konfiguration
- [x] `Procfile` für Gunicorn
- [x] Migrations-Script für automatische DB-Migrationen
- [x] PostgreSQL Support in `config.py`

### 🔧 Railway Umgebungsvariablen

Setze diese Variablen in deinem Railway Dashboard:

#### **Erforderlich:**
```bash
FLASK_ENV=production
SECRET_KEY=dein-super-sicherer-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname  # Wird automatisch von Railway gesetzt
CRYPTO_KEY=dein-fernet-key-fuer-verschluesselung
```

#### **Admin Setup:**
```bash
INIT_ADMIN_EMAIL=admin@gourmen.ch
INIT_ADMIN_PASSWORD=dein-sicheres-admin-passwort
```

#### **Optional (für erweiterte Features):**
```bash
GOOGLE_PLACES_API_KEY=dein-google-places-key
GOOGLE_MAPS_API_KEY=dein-backend-maps-key
GOOGLE_MAPS_API_KEY_FRONTEND=dein-frontend-maps-key
TWOFA_ISSUER=Gourmen
TZ=Europe/Zurich
```

### 🗄️ PostgreSQL Setup

1. **Railway PostgreSQL Service hinzufügen:**
   - Gehe zu deinem Railway Projekt
   - Klicke auf "New" → "Database" → "PostgreSQL"
   - Railway setzt automatisch `DATABASE_URL`

2. **Migrationen werden automatisch ausgeführt:**
   - Das `buildCommand` in `railway.json` führt Migrationen aus
   - Admin-User wird automatisch erstellt (falls konfiguriert)

### 🔐 Security Checklist

- [ ] `SECRET_KEY` ist stark und einzigartig
- [ ] `CRYPTO_KEY` für sensible Daten ist gesetzt
- [ ] Admin-Passwort ist sicher
- [ ] Alle API-Keys sind gesetzt (falls benötigt)

### 🚀 Deployment Steps

1. **Repository zu Railway verbinden:**
   ```bash
   # Via Railway CLI
   railway login
   railway link
   railway up
   ```

2. **Oder via GitHub Integration:**
   - Repository in Railway importieren
   - Automatisches Deployment bei Push

3. **Umgebungsvariablen setzen** (siehe oben)

4. **Deploy starten:**
   - Railway führt automatisch Migrationen aus
   - App startet mit Gunicorn

### 🔍 Troubleshooting

**Migrationen schlagen fehl:**
- Prüfe `DATABASE_URL` in Railway Dashboard
- Schaue in Railway Logs nach Fehlermeldungen

**App startet nicht:**
- Prüfe alle erforderlichen Umgebungsvariablen
- Schaue in Railway Logs nach Import-Fehlern

**Admin-User wird nicht erstellt:**
- Prüfe `INIT_ADMIN_EMAIL` und `INIT_ADMIN_PASSWORD`
- Schaue in App-Logs nach Fehlermeldungen

### 📊 Monitoring

- Railway Dashboard zeigt App-Status
- Logs sind in Railway Dashboard verfügbar
- Healthcheck auf `/` Route

### 🔄 Updates

Bei Code-Updates:
1. Push zu GitHub
2. Railway deployt automatisch
3. Migrationen werden automatisch ausgeführt
4. App wird neu gestartet
