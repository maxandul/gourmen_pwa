#!/usr/bin/env python3
"""
Start-Script für Railway mit Cron-Schedule Support
"""

import os
import sys
import logging

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Hauptfunktion für App-Start"""
    try:
        logger.info("Starting Gourmen PWA...")
        
        # Füge Backend zum Python-Pfad hinzu
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Importiere und erstelle App
        from backend.app import create_app
        app = create_app('production')
        
        logger.info("App created successfully")
        
        # Starte Gunicorn
        import gunicorn.app.wsgiapp as wsgi
        
        # Gunicorn-Konfiguration
        port = os.environ.get('PORT', '8000')
        workers = 1  # Ein Worker für Cron-Schedule Services
        timeout = 300  # Längerer Timeout für Cron-Jobs
        
        logger.info(f"Starting Gunicorn on port {port} with {workers} worker(s)")
        
        # Starte Gunicorn
        sys.argv = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', str(workers),
            '--timeout', str(timeout),
            '--preload',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info',
            'backend.app:create_app()'
        ]
        
        wsgi.run()
        
    except Exception as e:
        logger.error(f"Failed to start app: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
