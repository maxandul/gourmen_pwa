#!/usr/bin/env python
"""
Railway Cron Job Script für alle Event-Erinnerungen
Dieses Script wird von Railway's Cron Schedule ausgeführt und prüft:
- 3-Wochen-Erinnerungen (täglich)
- Montag-vor-Event-Erinnerungen (nur Montags)
- Zukünftige weitere Reminder können hier hinzugefügt werden
"""

import sys
import os
import logging
import argparse

# Füge den Projektpfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Railway Cron Job: Event Reminders")
    parser.add_argument(
        "--test-reminder",
        action="store_true",
        help="Sende einen sofortigen Test-Push an aktive Subscriptions"
    )
    return parser.parse_args()


def run_all_reminders(test_reminder: bool = False):
    """Führt alle Reminder-Checks aus"""
    try:
        # Importiere Flask App und Services
        from backend.app import create_app
        from backend.services.cron_service import CronService
        from backend.extensions import db
        from backend.models.auth_token import AuthToken
        from datetime import datetime, timedelta
        
        # Erstelle Flask App Context
        app = create_app()
        
        # Optionaler, sofortiger Test-Reminder
        if test_reminder:
            with app.app_context():
                logger.info("🧪 Test-Reminder angefordert - sende Test-Push an aktive Subscriptions...")
                test_result = CronService.run_test_reminder()
                if test_result.get("success"):
                    logger.info(f"✅ Test-Reminder gesendet: {test_result}")
                    return 0
                else:
                    logger.error(f"❌ Test-Reminder fehlgeschlagen: {test_result}")
                    return 1

        all_success = True
        
        with app.app_context():
            logger.info("🚀 Starting all reminder checks...")
            logger.info("")
            
            # ========================================
            # 1. 3-Wochen-Reminder (täglich)
            # ========================================
            logger.info("📧 [1/2] Checking 3-week reminders...")
            result_3week = CronService.run_3_week_reminders()
            
            if result_3week['success']:
                logger.info(f"   ✅ 3-week reminders: {result_3week['processed_events']} events processed")
                
                for event_result in result_3week.get('results', []):
                    logger.info(f"      Event {event_result['event_id']}: {event_result['event_name']}")
                    logger.info(f"         Organizer: {event_result['organizer_reminder_sent']}")
                    logger.info(f"         Members: {event_result['member_reminders'].get('sent_count', 0)} notifications")
            else:
                logger.error(f"   ❌ 3-week reminders failed: {result_3week.get('error', 'Unknown')}")
                all_success = False
            
            logger.info("")
            
            # ========================================
            # 2. Montag-Reminder (nur Montags)
            # ========================================
            logger.info("🥰 [2/3] Checking weekly reminders (Monday)...")
            result_weekly = CronService.run_weekly_reminders()
            
            if result_weekly['success']:
                if result_weekly.get('message') == 'Not Monday, skipped':
                    logger.info(f"   ⏭️  Weekly reminders: Skipped (not Monday)")
                else:
                    logger.info(f"   ✅ Weekly reminders: {result_weekly['processed_events']} events processed")
                    
                    for event_result in result_weekly.get('results', []):
                        logger.info(f"      Event {event_result['event_id']}: {event_result['event_name']}")
                        reminder_result = event_result.get('reminder_result', {})
                        logger.info(f"         Participants: {reminder_result.get('sent_count', 0)} notifications")
            else:
                logger.error(f"   ❌ Weekly reminders failed: {result_weekly.get('error', 'Unknown')}")
                all_success = False
            
            logger.info("")
            
            # ========================================
            # 3. Rating-Reminder (Tag nach Event)
            # ========================================
            logger.info("🌟 [3/3] Checking rating reminders (yesterday's events)...")
            result_rating = CronService.run_rating_reminders()
            
            if result_rating['success']:
                logger.info(f"   ✅ Rating reminders: {result_rating['processed_events']} events processed")
                
                for event_result in result_rating.get('results', []):
                    logger.info(f"      Event {event_result['event_id']}: {event_result['event_name']}")
                    reminder_result = event_result.get('reminder_result', {})
                    logger.info(f"         Participants: {reminder_result.get('sent_count', 0)} notifications")
            else:
                logger.error(f"   ❌ Rating reminders failed: {result_rating.get('error', 'Unknown')}")
                all_success = False

            logger.info("")

            # ========================================
            # 4. Auth-Token Cleanup (taeglich)
            # ========================================
            logger.info("🧹 [4/4] Cleaning up old auth tokens...")
            cutoff = datetime.utcnow() - timedelta(days=30)
            deleted_count = AuthToken.query.filter(AuthToken.expires_at < cutoff).delete()
            db.session.commit()
            logger.info(f"   ✅ Auth-Token cleanup: {deleted_count} rows deleted")
            
            logger.info("")
            logger.info("=" * 60)
            
            if all_success:
                logger.info("✅ All reminder checks completed successfully!")
                return 0
            else:
                logger.error("⚠️  Some reminder checks failed (see above)")
                return 1
                
    except Exception as e:
        logger.error(f"❌ Fatal error in cron job: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    args = parse_args()

    # Auch via Env aktivierbar (z.B. TEST_REMINDER_NOW=1)
    test_env = os.getenv("TEST_REMINDER_NOW", "").lower() in ("1", "true", "yes", "y")
    test_reminder = args.test_reminder or test_env

    logger.info("=" * 60)
    logger.info("🔔 Railway Cron Job: All Event Reminders")
    logger.info("=" * 60)
    logger.info("")
    
    exit_code = run_all_reminders(test_reminder=test_reminder)
    
    logger.info("=" * 60)
    logger.info(f"Cron job finished with exit code: {exit_code}")
    logger.info("=" * 60)
    
    sys.exit(exit_code)



