#!/usr/bin/env python3
"""
Railway Emergency Debug Script
Führt detaillierte Diagnose direkt in Railway aus
"""

import os
import sys
import traceback
import json

def log(message):
    """Log mit Timestamp"""
    print(f"[DEBUG] {message}")

def check_environment():
    """Prüfe alle Umgebungsvariablen"""
    log("=== ENVIRONMENT VARIABLES ===")
    
    vars_to_check = [
        'FLASK_ENV',
        'SECRET_KEY', 
        'DATABASE_URL',
        'CRYPTO_KEY',
        'VAPID_PUBLIC_KEY',
        'VAPID_PRIVATE_KEY',
        'CRON_AUTH_TOKEN',
        'PORT'
    ]
    
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            # Zeige nur ersten/letzten Teil für Sicherheit
            if len(value) > 20:
                display_value = f"{value[:10]}...{value[-10:]}"
            else:
                display_value = f"{value[:5]}..."
            log(f"✓ {var}: {display_value}")
        else:
            log(f"✗ {var}: NOT SET")

def test_imports():
    """Teste alle kritischen Imports"""
    log("=== IMPORT TESTS ===")
    
    try:
        log("Testing Flask...")
        from flask import Flask
        log("✓ Flask OK")
    except Exception as e:
        log(f"✗ Flask FAILED: {e}")
        return False
    
    try:
        log("Testing backend.extensions...")
        sys.path.insert(0, '/app/backend')
        from backend.extensions import db
        log("✓ Backend extensions OK")
    except Exception as e:
        log(f"✗ Backend extensions FAILED: {e}")
        return False
    
    try:
        log("Testing backend.config...")
        from backend.config import config
        log("✓ Backend config OK")
    except Exception as e:
        log(f"✗ Backend config FAILED: {e}")
        return False
    
    try:
        log("Testing VAPID service...")
        from backend.services.vapid_service import VAPIDService
        log("✓ VAPID service import OK")
    except Exception as e:
        log(f"✗ VAPID service import FAILED: {e}")
        return False
    
    try:
        log("Testing push notifications...")
        from backend.services.push_notifications import PushNotificationService
        log("✓ Push notifications import OK")
    except Exception as e:
        log(f"✗ Push notifications import FAILED: {e}")
        return False
    
    return True

def test_vapid_keys():
    """Teste VAPID-Keys detailliert"""
    log("=== VAPID KEYS TEST ===")
    
    try:
        from backend.services.vapid_service import VAPIDService
        
        # Teste Public Key
        log("Testing VAPID public key...")
        public_key = VAPIDService.get_vapid_public_key()
        log(f"✓ Public key: {public_key[:20]}...")
        
        # Teste Private Key
        log("Testing VAPID private key...")
        private_key = VAPIDService.get_vapid_private_key()
        log(f"✓ Private key: {private_key[:50]}...")
        
        return True
        
    except Exception as e:
        log(f"✗ VAPID keys test FAILED: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        return False

def test_database():
    """Teste Datenbankverbindung"""
    log("=== DATABASE TEST ===")
    
    try:
        import psycopg
        from urllib.parse import urlparse
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            log("✗ DATABASE_URL not set")
            return False
        
        log("Parsing DATABASE_URL...")
        parsed = urlparse(database_url)
        log(f"Host: {parsed.hostname}")
        log(f"Port: {parsed.port}")
        log(f"Database: {parsed.path[1:]}")
        
        log("Connecting to database...")
        conn = psycopg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path[1:]
        )
        
        log("Testing database query...")
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            log(f"✓ Database query result: {result}")
        
        conn.close()
        log("✓ Database connection successful")
        return True
        
    except Exception as e:
        log(f"✗ Database test FAILED: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        return False

def test_app_creation():
    """Teste App-Erstellung"""
    log("=== APP CREATION TEST ===")
    
    try:
        from backend.app import create_app
        
        log("Creating Flask app...")
        app = create_app('production')
        log("✓ Flask app created")
        
        log("Testing app context...")
        with app.app_context():
            log("✓ App context works")
        
        log("Testing health endpoint...")
        with app.test_client() as client:
            response = client.get('/health')
            log(f"Health endpoint status: {response.status_code}")
            if response.status_code == 200:
                log("✓ Health endpoint works")
            else:
                log(f"✗ Health endpoint failed: {response.get_data()}")
                return False
        
        return True
        
    except Exception as e:
        log(f"✗ App creation FAILED: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Hauptfunktion"""
    log("RAILWAY EMERGENCY DEBUG STARTING...")
    log("=" * 50)
    
    # Teste Umgebungsvariablen
    check_environment()
    
    # Teste Imports
    imports_ok = test_imports()
    
    # Teste VAPID-Keys
    vapid_ok = test_vapid_keys()
    
    # Teste Datenbank
    db_ok = test_database()
    
    # Teste App-Erstellung
    app_ok = test_app_creation()
    
    log("=" * 50)
    log("FINAL RESULTS:")
    log(f"Imports: {'✓' if imports_ok else '✗'}")
    log(f"VAPID Keys: {'✓' if vapid_ok else '✗'}")
    log(f"Database: {'✓' if db_ok else '✗'}")
    log(f"App Creation: {'✓' if app_ok else '✗'}")
    
    if all([imports_ok, vapid_ok, db_ok, app_ok]):
        log("✅ ALL TESTS PASSED - App should work!")
        return True
    else:
        log("❌ SOME TESTS FAILED - Check logs above")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
