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
    app = create_app('production')
    
    with app.app_context():
        try:
            print("🚀 Starte Datenbankmigrationen...")
            upgrade()
            print("✅ Migrationen erfolgreich abgeschlossen!")
        except Exception as e:
            print(f"❌ Fehler bei Migrationen: {e}")
            sys.exit(1)

if __name__ == '__main__':
    run_migrations()
