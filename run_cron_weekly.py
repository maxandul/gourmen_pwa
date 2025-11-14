#!/usr/bin/env python
"""
Railway Cron Job Script für Wochen-Erinnerungen (Montag vor Event)
Dieses Script wird von Railway's Cron Schedule ausgeführt
"""

import sys
import os
import logging

# Füge den Projektpfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_weekly_reminders():
    """Führt die Wochen-Erinnerungen aus"""
    try:
        # Importiere Flask App und Services
        from backend.app import create_app
        from backend.services.cron_service import CronService
        
        # Erstelle Flask App Context
        app = create_app()
        
        with app.app_context():
            logger.info("Starting weekly reminder cron job...")
            
            # Führe Cron-Job aus
            result = CronService.run_weekly_reminders()
            
            if result['success']:
                logger.info(f"✅ Cron job completed successfully!")
                logger.info(f"   Processed events: {result['processed_events']}")
                
                if result.get('message'):
                    logger.info(f"   Message: {result['message']}")
                
                for event_result in result.get('results', []):
                    logger.info(f"   Event {event_result['event_id']}: {event_result['event_name']} ({event_result.get('event_type', 'N/A')})")
                    reminder_result = event_result.get('reminder_result', {})
                    logger.info(f"      Participants: {reminder_result.get('sent_count', 0)} notifications sent")
                
                return 0  # Exit code 0 = success
            else:
                logger.error(f"❌ Cron job failed: {result.get('error', 'Unknown error')}")
                return 1  # Exit code 1 = error
                
    except Exception as e:
        logger.error(f"❌ Fatal error in cron job: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Railway Cron Job: Weekly Event Reminders")
    logger.info("=" * 60)
    
    exit_code = run_weekly_reminders()
    
    logger.info("=" * 60)
    logger.info(f"Cron job finished with exit code: {exit_code}")
    logger.info("=" * 60)
    
    sys.exit(exit_code)

