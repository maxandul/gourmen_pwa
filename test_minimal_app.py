#!/usr/bin/env python3
"""
Minimal test app to debug Railway deployment issues
"""

import os
from flask import Flask

def create_minimal_app():
    """Create minimal Flask app for testing"""
    app = Flask(__name__)
    
    # Minimal config
    app.config['SECRET_KEY'] = 'test-key'
    
    @app.route('/')
    def index():
        return {'status': 'ok', 'message': 'Minimal app is running'}
    
    @app.route('/test')
    def test():
        return {'status': 'ok', 'message': 'Test endpoint works'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'message': 'App is healthy'}
    
    return app

if __name__ == '__main__':
    app = create_minimal_app()
    print("✅ Minimal app created successfully!")
    print("🚀 Starting minimal app...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
