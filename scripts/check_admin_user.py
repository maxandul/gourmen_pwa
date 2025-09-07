#!/usr/bin/env python3
"""
Check Admin User Script
Überprüft ob Admin-User existiert und zeigt Details an
"""

import os
import sys
from flask import Flask

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

def check_admin_user():
    """Überprüft Admin-User Status"""
    print("🔍 Überprüfe Admin-User Status...")
    
    app = create_app('production')
    
    with app.app_context():
        try:
            from backend.models.member import Member, Role
            from backend.extensions import db
            
            # Prüfe alle Admin-User
            admin_users = Member.query.filter_by(role=Role.ADMIN).all()
            
            print(f"📊 Gefundene Admin-User: {len(admin_users)}")
            
            for admin in admin_users:
                print(f"  - Email: {admin.email}")
                print(f"  - Name: {admin.vorname} {admin.nachname}")
                print(f"  - Aktiv: {admin.is_active}")
                print(f"  - Erstellt: {admin.created_at}")
                print(f"  - Passwort geändert: {admin.password_changed_at}")
                print()
            
            # Prüfe Umgebungsvariablen
            print("🔧 Umgebungsvariablen:")
            print(f"  - INIT_ADMIN_EMAIL: {app.config.get('INIT_ADMIN_EMAIL', 'NICHT GESETZT')}")
            print(f"  - INIT_ADMIN_PASSWORD: {'GESETZT' if app.config.get('INIT_ADMIN_PASSWORD') else 'NICHT GESETZT'}")
            
            # Prüfe ob konfigurierter Admin existiert
            configured_email = app.config.get('INIT_ADMIN_EMAIL')
            if configured_email:
                configured_admin = Member.query.filter_by(email=configured_email).first()
                if configured_admin:
                    print(f"✅ Konfigurierter Admin-User ({configured_email}) existiert")
                else:
                    print(f"❌ Konfigurierter Admin-User ({configured_email}) existiert NICHT")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Überprüfen: {e}")
            return False

if __name__ == '__main__':
    success = check_admin_user()
    sys.exit(0 if success else 1)
