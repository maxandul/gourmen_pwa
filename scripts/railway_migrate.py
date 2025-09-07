#!/usr/bin/env python3
"""
Railway Migration Script
Führt Datenbankmigrationen für Railway Deployment aus
"""

import os
import sys
from flask import Flask
from flask_migrate import upgrade

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

def run_migrations():
    """Führt alle ausstehenden Migrationen aus"""
    # Prüfe ob DATABASE_URL gesetzt ist (Railway PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("⚠️  Keine DATABASE_URL gefunden - überspringe Migrationen")
        print("   Migrationen werden beim ersten App-Start ausgeführt")
        return
    
    # Prüfe ob es eine PostgreSQL URL ist
    if not database_url.startswith('postgresql://'):
        print("⚠️  Keine PostgreSQL-Datenbank - überspringe Migrationen")
        return
    
    # Prüfe ob wir im Build-Prozess sind (keine echte DB-Verbindung möglich)
    try:
        # Teste eine einfache DB-Verbindung
        import psycopg2
        conn = psycopg2.connect(database_url)
        conn.close()
    except Exception as e:
        print(f"⚠️  Datenbank nicht erreichbar während Build: {e}")
        print("   Migrationen werden beim ersten App-Start ausgeführt")
        return
    
    app = create_app('production')
    
    with app.app_context():
        try:
            print("🚀 Starte Datenbankmigrationen...")
            upgrade()
            print("✅ Migrationen erfolgreich abgeschlossen!")
        except Exception as e:
            print(f"❌ Fehler bei Migrationen: {e}")
            print("   Migrationen werden beim ersten App-Start erneut versucht")
            # Nicht mit Fehler beenden, da App trotzdem starten kann
            return

if __name__ == '__main__':
    run_migrations()
