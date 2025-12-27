"""
Cron Service für automatische Aufgaben
Handles scheduled tasks wie 3-Wochen-Erinnerungen
"""

import logging
from datetime import datetime, timedelta
from backend.extensions import db
from backend.services.push_notifications import PushNotificationService
from backend.models.event import Event

logger = logging.getLogger(__name__)

class CronService:
    """Service für automatische Cron-Jobs"""
    
    @staticmethod
    def run_test_reminder():
        """
        Sendet einen sofortigen Test-Push an aktive Subscriptions (limitiert).
        Dient nur zum manuellen Test via `run_cron_reminders.py --test-reminder`.
        """
        try:
            logger.info("Starting test reminder cron job...")
            result = PushNotificationService.send_test_push_to_active_subscriptions()
            if result.get("success"):
                logger.info(f"Test reminder sent: {result}")
                return result
            logger.error(f"Test reminder failed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in test reminder: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def run_3_week_reminders():
        """
        Cron-Job für 3-Wochen-Erinnerungen
        Sollte täglich ausgeführt werden
        """
        try:
            logger.info("Starting 3-week reminder cron job...")
            
            result = PushNotificationService.check_and_send_3_week_reminders()
            
            if result['success']:
                logger.info(f"3-week reminder cron job completed successfully: {result['processed_events']} events processed")
                return result
            else:
                logger.error(f"3-week reminder cron job failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error in 3-week reminder cron job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_cron_status():
        """
        Gibt den Status aller Cron-Jobs zurück
        """
        try:
            from backend.models.event import EventType
            
            # Prüfe Events die in 3 Wochen sind (nur MONATSESSEN und GENERALVERSAMMLUNG)
            target_date = datetime.utcnow() + timedelta(days=21)
            start_date = target_date - timedelta(hours=12)
            end_date = target_date + timedelta(hours=12)
            
            upcoming_events = Event.query.filter(
                Event.datum >= start_date,
                Event.datum <= end_date,
                Event.published == True,
                Event.event_typ.in_([EventType.MONATSESSEN, EventType.GENERALVERSAMMLUNG])
            ).count()
            
            # Prüfe Push-Subscriptions
            from backend.models.push_subscription import PushSubscription
            total_subscriptions = PushSubscription.query.filter_by(is_active=True).count()
            
            return {
                'success': True,
                'status': {
                    'upcoming_events_3_weeks': upcoming_events,
                    'active_push_subscriptions': total_subscriptions,
                    'last_check': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cron status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def run_weekly_reminders():
        """
        Cron-Job für Wochen-Erinnerungen (Montag vor Event)
        Sollte jeden Montag ausgeführt werden
        """
        try:
            logger.info("Starting weekly reminder cron job...")
            
            result = PushNotificationService.check_and_send_weekly_reminders()
            
            if result['success']:
                logger.info(f"Weekly reminder cron job completed successfully: {result['processed_events']} events processed")
                return result
            else:
                logger.error(f"Weekly reminder cron job failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error in weekly reminder cron job: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def run_rating_reminders():
        """
        Cron-Job für Rating-Erinnerungen (Tag nach Event)
        Sollte täglich ausgeführt werden
        """
        try:
            logger.info("Starting rating reminder cron job...")
            
            result = PushNotificationService.check_and_send_rating_reminders()
            
            if result['success']:
                logger.info(f"Rating reminder cron job completed successfully: {result['processed_events']} events processed")
                return result
            else:
                logger.error(f"Rating reminder cron job failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            logger.error(f"Error in rating reminder cron job: {e}")
            return {
                'success': False,
                'error': str(e)
            }