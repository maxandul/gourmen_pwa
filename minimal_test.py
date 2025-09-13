#!/usr/bin/env python3
"""
Minimal Test - Testet nur die kritischsten Teile
"""

import os
import sys
import traceback

def test_minimal_app():
    """Teste minimale App ohne Push-Notifications"""
    print("Testing minimal app...")
    
    try:
        # Füge Backend zum Pfad hinzu
        sys.path.insert(0, '/app/backend')
        
        # Teste nur die grundlegenden Imports
        from flask import Flask
        print("✓ Flask import OK")
        
        from backend.extensions import db
        print("✓ Database extension OK")
        
        from backend.config import config
        print("✓ Config OK")
        
        # Erstelle minimale App
        app = Flask(__name__)
        app.config.from_object(config['production'])
        
        # Teste Health Endpoint
        @app.route('/health')
        def health():
            return {'status': 'ok'}, 200
        
        # Teste App
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Minimal app works")
                return True
            else:
                print(f"✗ Minimal app failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Minimal app failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = test_minimal_app()
    sys.exit(0 if success else 1)
