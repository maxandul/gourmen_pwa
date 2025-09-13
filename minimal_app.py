#!/usr/bin/env python3
"""
Minimale Flask-App für Railway Debugging
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Minimal Flask app is running',
        'port': os.environ.get('PORT', 'not set')
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Minimal app is healthy'
    })

@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Test endpoint works',
        'environment': {
            'PORT': os.environ.get('PORT'),
            'FLASK_ENV': os.environ.get('FLASK_ENV'),
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT')
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting minimal app on port {port}")
    print(f"PORT environment variable: {os.environ.get('PORT')}")
    app.run(host='0.0.0.0', port=port, debug=False)
