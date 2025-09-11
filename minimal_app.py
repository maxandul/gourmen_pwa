#!/usr/bin/env python3
"""
Minimal test app to isolate Railway deployment issues
"""

import os
from flask import Flask, jsonify

def create_minimal_app():
    """Create a minimal Flask app for testing"""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'app': 'minimal',
            'database_url_set': bool(os.environ.get('DATABASE_URL')),
            'secret_key_set': bool(os.environ.get('SECRET_KEY'))
        })
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Minimal app is running'})
    
    return app

if __name__ == '__main__':
    app = create_minimal_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
