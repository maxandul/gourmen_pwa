#!/usr/bin/env python3
"""
Railway Debug Script - Testet die App-Konfiguration für Railway
"""

import os
import sys
import traceback

def check_environment_variables():
    """Prüfe alle erforderlichen Umgebungsvariablen"""
    print("=== Environment Variables Check ===")
    
    required_vars = [
        'FLASK_ENV',
        'SECRET_KEY',
        'DATABASE_URL',
        'CRYPTO_KEY'
    ]
    
    optional_vars = [
        'VAPID_PUBLIC_KEY',
        'VAPID_PRIVATE_KEY',
        'CRON_AUTH_TOKEN',
        'INIT_ADMIN_EMAIL',
        'INIT_ADMIN_PASSWORD'
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var}: {'*' * min(len(value), 10)}...")
        else:
            print(f"✗ {var}: NOT SET")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var}: {'*' * min(len(value), 10)}...")
        else:
            print(f"⚠ {var}: NOT SET (optional)")
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        return False
    else:
        print(f"\n✅ All required variables are set")
        if missing_optional:
            print(f"⚠️  Optional variables not set: {', '.join(missing_optional)}")
        return True

def test_database_connection():
    """Teste Datenbankverbindung"""
    print("\n=== Database Connection Test ===")
    
    try:
        import psycopg
        from urllib.parse import urlparse
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("✗ DATABASE_URL not set")
            return False
        
        # Parse DATABASE_URL
        parsed = urlparse(database_url)
        
        # Teste Verbindung
        conn = psycopg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path[1:]  # Remove leading slash
        )
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        
        conn.close()
        print("✓ Database connection successful")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_app_startup():
    """Teste App-Startup"""
    print("\n=== App Startup Test ===")
    
    try:
        # Füge das Backend-Verzeichnis zum Python-Pfad hinzu
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        from backend.app import create_app
        
        print("1. Creating app...")
        app = create_app('production')
        print("✓ App created successfully")
        
        print("2. Testing app context...")
        with app.app_context():
            print("✓ App context works")
        
        print("3. Testing health endpoint...")
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Health endpoint works")
            else:
                print(f"✗ Health endpoint failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ App startup failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_vapid_configuration():
    """Teste VAPID-Konfiguration"""
    print("\n=== VAPID Configuration Test ===")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from backend.services.vapid_service import VAPIDService
        
        public_key = os.environ.get('VAPID_PUBLIC_KEY')
        private_key = os.environ.get('VAPID_PRIVATE_KEY')
        
        if public_key and private_key:
            print("✓ VAPID keys from environment variables")
            
            # Teste ob Keys funktionieren
            try:
                test_public = VAPIDService.get_vapid_public_key()
                test_private = VAPIDService.get_vapid_private_key()
                print("✓ VAPID keys are valid")
                return True
            except Exception as e:
                print(f"✗ VAPID keys are invalid: {e}")
                return False
        else:
            print("⚠ VAPID keys not set - push notifications will be disabled")
            return True
            
    except Exception as e:
        print(f"✗ VAPID configuration test failed: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("Railway Debug Script")
    print("=" * 40)
    
    # Prüfe Umgebungsvariablen
    env_ok = check_environment_variables()
    
    # Teste Datenbankverbindung
    db_ok = test_database_connection()
    
    # Teste VAPID-Konfiguration
    vapid_ok = test_vapid_configuration()
    
    # Teste App-Startup
    app_ok = test_app_startup()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Environment Variables: {'✓' if env_ok else '✗'}")
    print(f"Database Connection: {'✓' if db_ok else '✗'}")
    print(f"VAPID Configuration: {'✓' if vapid_ok else '✗'}")
    print(f"App Startup: {'✓' if app_ok else '✗'}")
    
    if all([env_ok, db_ok, vapid_ok, app_ok]):
        print("\n✅ All tests passed! App should work on Railway.")
        return True
    else:
        print("\n❌ Some tests failed. Check the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
