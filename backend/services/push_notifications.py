"""
Push Notification Service für Gourmen PWA
Handles echte Web Push Notifications über das Betriebssystem
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from backend.extensions import db
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.member import Member
from backend.models.push_subscription import PushSubscription
from backend.services.vapid_service import VAPIDService

logger = logging.getLogger(__name__)

try:
    from pywebpush import webpush, WebPushException
    from py_vapid import Vapid02
    WEBPUSH_AVAILABLE = True
except ImportError:
    logger.warning("pywebpush not available - install with: pip install pywebpush")
    WEBPUSH_AVAILABLE = False

class PushNotificationService:
    """Service für echte Push-Benachrichtigungen über das Betriebssystem"""
    
    @staticmethod
    def send_push_notification(subscription_data: Dict, payload: Dict, return_error_details: bool = False):
        """
        Sendet eine echte Push-Benachrichtigung über das Betriebssystem
        """
        if not WEBPUSH_AVAILABLE:
            logger.error("pywebpush not available - cannot send push notifications")
            return {'success': False, 'error': 'pywebpush not available'} if return_error_details else False
        
        try:
            # VAPID-Keys holen
            vapid_private_key_pem = VAPIDService.get_vapid_private_key()
            vapid_public_key = VAPIDService.get_vapid_public_key()
            
            # Erstelle Vapid02-Objekt aus PEM-Key
            # Verwende from_raw mit dem private_key object aus cryptography
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            
            private_key_obj = load_pem_private_key(
                vapid_private_key_pem.encode('utf-8'),
                password=None
            )
            
            vapid = Vapid02.from_raw(private_key_obj.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
            # Push-Benachrichtigung senden
            # Extrahiere Push-Server Domain für aud (audience)
            try:
                endpoint_url = subscription_data.get('endpoint', '')
                # Für FCM (Chrome/Android)
                if 'fcm.googleapis.com' in endpoint_url or 'android.googleapis.com' in endpoint_url:
                    audience = 'https://fcm.googleapis.com'
                # Für Mozilla (Firefox)
                elif 'mozilla.com' in endpoint_url:
                    audience = 'https://updates.push.services.mozilla.com'
                # Fallback: Extrahiere aus endpoint
                else:
                    from urllib.parse import urlparse
                    parsed = urlparse(endpoint_url)
                    audience = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                audience = 'https://fcm.googleapis.com'  # Fallback auf FCM
            
            result = webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=vapid,
                vapid_claims={
                    "sub": "mailto:ulrich.andreas@hotmail.com",
                    "aud": audience
                }
            )
            
            logger.info(f"Push notification sent successfully to {subscription_data['endpoint'][:50]}...")
            return {'success': True} if return_error_details else True
            
        except WebPushException as e:
            status = None
            body = None
            try:
                status = getattr(e.response, 'status_code', None)
                body = e.response.json() if hasattr(e.response, 'json') else getattr(e.response, 'content', None)
            except Exception:
                pass
            logger.error(f"WebPush error: status={status} detail={body} exc={e}")
            return ({'success': False, 'status': status, 'error': str(e), 'detail': body}
                    if return_error_details else False)
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return {'success': False, 'error': str(e)} if return_error_details else False
    
    @staticmethod
    def send_event_reminder_to_organizer(event_id: int) -> bool:
        """
        Sendet eine Push-Benachrichtigung an den Organisator eines Events,
        wenn das Event in 3 Wochen ansteht
        """
        try:
            event = Event.query.get(event_id)
            if not event or not event.is_upcoming:
                return False
            
            organizer = event.organisator
            if not organizer:
                return False
            
            # Prüfe ob Event in 3 Wochen (21 Tagen) ist
            time_until_event = event.datum - datetime.utcnow()
            if not (timedelta(days=20) <= time_until_event <= timedelta(days=22)):
                return False
            
            # Hole Push-Subscriptions des Organisators
            subscriptions = PushSubscription.query.filter_by(
                member_id=organizer.id,
                is_active=True
            ).all()
            
            if not subscriptions:
                logger.info(f"No push subscriptions found for organizer {organizer.email}")
                return False
            
            # Zähle Mitglieder die noch nicht geantwortet haben
            total_members = Member.query.filter_by(aktiv=True).count()
            responded_count = Participation.query.filter_by(event_id=event_id).count()
            non_responded_count = total_members - responded_count
            
            # Push-Benachrichtigung Payload
            payload = {
                'title': f'Event-Organisation: {event.event_typ.value}',
                'body': f"Das Event '{event.restaurant or 'Unbekanntes Restaurant'}' findet in 3 Wochen statt. {non_responded_count} Mitglieder haben noch nicht geantwortet.",
                'icon': '/static/img/pwa/icon-192.png',
                'badge': '/static/img/pwa/icon-96.png',
                'tag': f'event-organizer-{event_id}',
                'data': {
                    'url': f'/events/{event_id}',
                    'event_id': event_id,
                    'type': 'event_organizer_reminder'
                },
                'actions': [
                    {
                        'action': 'view_event',
                        'title': 'Event anzeigen'
                    }
                ]
            }
            
            # Sende an alle Subscriptions des Organisators
            success_count = 0
            for subscription in subscriptions:
                if PushNotificationService.send_push_notification(subscription.subscription_data, payload):
                    subscription.mark_used()
                    success_count += 1
            
            logger.info(f"Sent organizer reminder to {success_count}/{len(subscriptions)} subscriptions for {organizer.email}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending event reminder to organizer: {e}")
            return False
    
    @staticmethod
    def send_participation_reminder_to_members(event_id: int) -> dict:
        """
        Sendet Push-Benachrichtigungen an Mitglieder die noch nicht geantwortet haben
        """
        try:
            event = Event.query.get(event_id)
            if not event or not event.is_upcoming:
                return {"success": False, "message": "Event nicht gefunden oder bereits vorbei"}
            
            # Finde Mitglieder die noch nicht geantwortet haben
            responded_member_ids = db.session.query(Participation.member_id).filter_by(
                event_id=event_id
            ).subquery()
            
            non_responded_members = Member.query.filter(
                Member.aktiv == True,
                ~Member.id.in_(responded_member_ids)
            ).all()
            
            # Push-Benachrichtigung Payload
            payload = {
                'title': f'Teilnahme gesucht: {event.event_typ.value}',
                'body': f"Das Event '{event.restaurant or 'Unbekanntes Restaurant'}' am {event.display_date} benötigt deine Antwort!",
                'icon': '/static/img/pwa/icon-192.png',
                'badge': '/static/img/pwa/icon-96.png',
                'tag': f'event-participation-{event_id}',
                'data': {
                    'url': f'/events/{event_id}',
                    'event_id': event_id,
                    'type': 'event_participation_reminder'
                },
                'actions': [
                    {
                        'action': 'view_event',
                        'title': 'Event anzeigen'
                    }
                ]
            }
            
            sent_count = 0
            total_subscriptions = 0
            
            for member in non_responded_members:
                # Hole Push-Subscriptions des Mitglieds
                subscriptions = PushSubscription.query.filter_by(
                    member_id=member.id,
                    is_active=True
                ).all()
                
                total_subscriptions += len(subscriptions)
                
                # Sende an alle Subscriptions des Mitglieds
                for subscription in subscriptions:
                    if PushNotificationService.send_push_notification(subscription.subscription_data, payload):
                        subscription.mark_used()
                        sent_count += 1
            
            return {
                "success": True, 
                "message": f"Erinnerungen an {sent_count} Geräte von {len(non_responded_members)} Mitgliedern gesendet",
                "sent_count": sent_count,
                "members_count": len(non_responded_members),
                "total_subscriptions": total_subscriptions
            }
            
        except Exception as e:
            logger.error(f"Error sending participation reminders: {e}")
            return {"success": False, "message": f"Fehler beim Senden der Erinnerungen: {e}"}
    
    @staticmethod
    def get_event_participation_stats(event_id: int) -> dict:
        """
        Gibt Statistiken über die Teilnahme an einem Event zurück
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return {"error": "Event nicht gefunden"}
            
            # Zähle verschiedene Teilnahme-Status
            total_members = Member.query.filter_by(aktiv=True).count()
            participated = Participation.query.filter_by(
                event_id=event_id, 
                teilnahme=True
            ).count()
            declined = Participation.query.filter_by(
                event_id=event_id, 
                teilnahme=False
            ).count()
            no_response = total_members - participated - declined
            
            return {
                "event_id": event_id,
                "event_name": event.restaurant or "Unbekanntes Restaurant",
                "event_date": event.display_date,
                "total_members": total_members,
                "participated": participated,
                "declined": declined,
                "no_response": no_response,
                "participation_rate": round((participated + declined) / total_members * 100, 1) if total_members > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting event participation stats: {e}")
            return {"error": f"Fehler beim Abrufen der Statistiken: {e}"}
    
    @staticmethod
    def check_and_send_3_week_reminders():
        """
        Prüft alle Events und sendet 3-Wochen-Erinnerungen automatisch
        Sollte täglich als Cron-Job ausgeführt werden
        """
        try:
            # Finde Events die in 3 Wochen (21 Tagen) sind
            target_date = datetime.utcnow() + timedelta(days=21)
            start_date = target_date - timedelta(hours=12)  # 12h Toleranz
            end_date = target_date + timedelta(hours=12)
            
            events = Event.query.filter(
                Event.datum >= start_date,
                Event.datum <= end_date,
                Event.published == True
            ).all()
            
            results = []
            for event in events:
                # Sende Erinnerung an Organisator
                organizer_success = PushNotificationService.send_event_reminder_to_organizer(event.id)
                
                # Sende Erinnerungen an Mitglieder
                member_result = PushNotificationService.send_participation_reminder_to_members(event.id)
                
                results.append({
                    'event_id': event.id,
                    'event_name': event.restaurant or 'Unbekanntes Restaurant',
                    'event_date': event.display_date,
                    'organizer_reminder_sent': organizer_success,
                    'member_reminders': member_result
                })
                
                logger.info(f"Processed 3-week reminder for event {event.id}: organizer={organizer_success}, members={member_result}")
            
            return {
                'success': True,
                'processed_events': len(events),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in 3-week reminder check: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def subscribe_member_to_push(member_id: int, subscription_data: Dict, user_agent: str = None) -> bool:
        """
        Registriert ein Mitglied für Push-Benachrichtigungen
        """
        try:
            # Prüfe ob bereits eine Subscription mit diesem Endpoint existiert
            existing = PushSubscription.query.filter_by(
                endpoint=subscription_data['endpoint']
            ).first()
            
            if existing:
                # Aktualisiere bestehende Subscription
                existing.member_id = member_id
                existing.p256dh_key = subscription_data['keys']['p256dh']
                existing.auth_key = subscription_data['keys']['auth']
                existing.user_agent = user_agent
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
            else:
                # Erstelle neue Subscription
                subscription = PushSubscription(
                    member_id=member_id,
                    endpoint=subscription_data['endpoint'],
                    p256dh_key=subscription_data['keys']['p256dh'],
                    auth_key=subscription_data['keys']['auth'],
                    user_agent=user_agent
                )
                db.session.add(subscription)
            
            db.session.commit()
            logger.info(f"Push subscription registered for member {member_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering push subscription for member {member_id}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def unsubscribe_member_from_push(member_id: int, endpoint: str = None) -> bool:
        """
        Entfernt Push-Subscription eines Mitglieds
        """
        try:
            if endpoint:
                # Entferne spezifische Subscription
                subscription = PushSubscription.query.filter_by(
                    member_id=member_id,
                    endpoint=endpoint
                ).first()
            else:
                # Entferne alle Subscriptions des Mitglieds
                subscription = PushSubscription.query.filter_by(member_id=member_id).first()
            
            if subscription:
                subscription.is_active = False
                db.session.commit()
                logger.info(f"Push subscription deactivated for member {member_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing member {member_id} from push: {e}")
            db.session.rollback()
            return False
