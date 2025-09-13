#!/usr/bin/env python3
"""
Test-Script um die App-Startup-Probleme zu debuggen
"""

import os
import sys
import traceback

# Füge das Backend-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Teste alle kritischen Imports"""
    print("=== Testing Imports ===")
    
    try:
        print("1. Testing Flask...")
        from flask import Flask
        print("   ✓ Flask import successful")
    except Exception as e:
        print(f"   ✗ Flask import failed: {e}")
        return False
    
    try:
        print("2. Testing backend.extensions...")
        from backend.extensions import db, init_extensions
        print("   ✓ Backend extensions import successful")
    except Exception as e:
        print(f"   ✗ Backend extensions import failed: {e}")
        return False
    
    try:
        print("3. Testing backend.config...")
        from backend.config import config
        print("   ✓ Backend config import successful")
    except Exception as e:
        print(f"   ✗ Backend config import failed: {e}")
        return False
    
    try:
        print("4. Testing backend.models...")
        from backend.models import member, event, participation
        print("   ✓ Backend models import successful")
    except Exception as e:
        print(f"   ✗ Backend models import failed: {e}")
        return False
    
    try:
        print("5. Testing VAPID service...")
        from backend.services.vapid_service import VAPIDService
        print("   ✓ VAPID service import successful")
    except Exception as e:
        print(f"   ✗ VAPID service import failed: {e}")
        return False
    
    try:
        print("6. Testing Push notification service...")
        from backend.services.push_notifications import PushNotificationService
        print("   ✓ Push notification service import successful")
    except Exception as e:
        print(f"   ✗ Push notification service import failed: {e}")
        return False
    
    return True

def test_vapid_keys():
    """Teste VAPID-Keys"""
    print("\n=== Testing VAPID Keys ===")
    
    try:
        from backend.services.vapid_service import VAPIDService
        
        print("1. Testing VAPID public key...")
        public_key = VAPIDService.get_vapid_public_key()
        print(f"   ✓ VAPID public key: {public_key[:20]}...")
        
        print("2. Testing VAPID private key...")
        private_key = VAPIDService.get_vapid_private_key()
        print(f"   ✓ VAPID private key: {private_key[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ✗ VAPID keys test failed: {e}")
        return False

def test_app_creation():
    """Teste App-Erstellung"""
    print("\n=== Testing App Creation ===")
    
    try:
        from backend.app import create_app
        
        print("1. Creating Flask app...")
        app = create_app('development')
        print("   ✓ Flask app created successfully")
        
        print("2. Testing app context...")
        with app.app_context():
            print("   ✓ App context works")
        
        print("3. Testing routes...")
        with app.test_client() as client:
            response = client.get('/health')
            print(f"   ✓ Health endpoint: {response.status_code}")
            
            response = client.get('/test')
            print(f"   ✓ Test endpoint: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ App creation failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Hauptfunktion"""
    print("Gourmen PWA - App Startup Test")
    print("=" * 40)
    
    # Teste Imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Teste VAPID-Keys
    if not test_vapid_keys():
        print("\n⚠️  VAPID keys not available - push notifications will be disabled")
    
    # Teste App-Erstellung
    if not test_app_creation():
        print("\n❌ App creation failed!")
        return False
    
    print("\n✅ All tests passed! App should work correctly.")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
