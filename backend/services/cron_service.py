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
    def cleanup_old_subscriptions():
        """
        Bereinigt alte/inaktive Push-Subscriptions
        Sollte wöchentlich ausgeführt werden
        """
        try:
            logger.info("Starting push subscription cleanup...")
            
            # Entferne Subscriptions die länger als 90 Tage nicht verwendet wurden
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            from backend.models.push_subscription import PushSubscription
            
            old_subscriptions = PushSubscription.query.filter(
                PushSubscription.last_used_at < cutoff_date,
                PushSubscription.is_active == True
            ).all()
            
            cleaned_count = 0
            for subscription in old_subscriptions:
                subscription.is_active = False
                cleaned_count += 1
            
            db.session.commit()
            
            logger.info(f"Push subscription cleanup completed: {cleaned_count} subscriptions deactivated")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            logger.error(f"Error in push subscription cleanup: {e}")
            db.session.rollback()
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
            # Prüfe Events die in 3 Wochen sind
            target_date = datetime.utcnow() + timedelta(days=21)
            start_date = target_date - timedelta(hours=12)
            end_date = target_date + timedelta(hours=12)
            
            upcoming_events = Event.query.filter(
                Event.datum >= start_date,
                Event.datum <= end_date,
                Event.published == True
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
