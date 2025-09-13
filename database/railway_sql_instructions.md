# SQL auf Railway ausführen - Schritt-für-Schritt

## Option 1: Railway Dashboard (Einfachste Methode)

1. **Gehe zu Railway Dashboard** → Dein Projekt
2. **Klicke auf "Data"** (oder "Database") 
3. **Klicke auf "Query"** (oder "SQL Editor")
4. **Kopiere den SQL-Code** aus `create_push_subscriptions_table.sql`
5. **Füge ihn in den Query-Editor ein**
6. **Klicke "Run"** oder "Execute"

## Option 2: Railway CLI

```bash
# Installiere Railway CLI
npm install -g @railway/cli

# Login
railway login

# Verbinde mit deinem Projekt
railway link

# Führe SQL aus
railway run psql $DATABASE_URL -f database/create_push_subscriptions_table.sql
```

## Option 3: Externer PostgreSQL Client

1. **Hole Connection String** aus Railway Dashboard → Variables → `DATABASE_URL`
2. **Verwende pgAdmin, DBeaver, oder ähnliches**
3. **Verbinde mit der Datenbank**
4. **Führe das SQL aus**

## Was passiert nach dem SQL?

Das SQL erstellt:
- ✅ Tabelle `push_subscriptions`
- ✅ Foreign Key zu `members` Tabelle
- ✅ Indexes für Performance
- ✅ Trigger für `updated_at` Auto-Update

## Überprüfung

Nach dem SQL kannst du prüfen ob es funktioniert hat:
```sql
-- Prüfe ob Tabelle existiert
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'push_subscriptions';

-- Prüfe Tabellenstruktur
\d push_subscriptions
```
