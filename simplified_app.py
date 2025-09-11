#!/usr/bin/env python3
"""
Simplified version of the main app to identify the specific issue
"""

import os
from flask import Flask, jsonify

def create_simplified_app():
    """Create a simplified version of the main app"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False
    
    print(f"Creating simplified app with config: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Database URL set: {bool(os.environ.get('DATABASE_URL'))}")
    
    # Try to import and initialize extensions step by step
    try:
        print("Step 1: Importing extensions...")
        from backend.extensions import db, login_manager, csrf, limiter
        print("✅ Extensions imported successfully")
        
        print("Step 2: Initializing database...")
        db.init_app(app)
        print("✅ Database initialized successfully")
        
        print("Step 3: Initializing login manager...")
        login_manager.init_app(app)
        print("✅ Login manager initialized successfully")
        
        print("Step 4: Initializing CSRF...")
        csrf.init_app(app)
        print("✅ CSRF initialized successfully")
        
        print("Step 5: Initializing limiter...")
        limiter.init_app(app)
        print("✅ Limiter initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing extensions: {e}")
        import traceback
        traceback.print_exc()
        # Continue with basic app even if extensions fail
    
    # Try to import models
    try:
        print("Step 6: Importing models...")
        from backend.models import member, member_sensitive, member_mfa, mfa_backup_code, event, participation, document, audit_event
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        import traceback
        traceback.print_exc()
    
    # Try to import and register blueprints
    try:
        print("Step 7: Importing blueprints...")
        from backend.routes import public
        print("✅ Public blueprint imported successfully")
        
        print("Step 8: Registering public blueprint...")
        app.register_blueprint(public.bp)
        print("✅ Public blueprint registered successfully")
        
    except Exception as e:
        print(f"❌ Error with public blueprint: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: create basic health endpoint
        @app.route('/health')
        def health_fallback():
            return jsonify({
                'status': 'ok',
                'app': 'simplified',
                'note': 'Using fallback health endpoint due to blueprint error'
            })
    
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Simplified app is running',
            'status': 'success'
        })
    
    print("✅ Simplified app created successfully")
    return app

if __name__ == '__main__':
    app = create_simplified_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
