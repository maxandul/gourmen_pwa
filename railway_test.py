#!/usr/bin/env python3
"""
Minimal test app for Railway deployment
"""

from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return {'status': 'ok', 'message': 'Railway test app is running'}

@app.route('/test')
def test():
    return {'status': 'ok', 'message': 'Test endpoint works'}

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'App is healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
