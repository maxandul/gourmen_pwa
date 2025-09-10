import json
import base64
from datetime import datetime, timedelta
from flask import current_app
from backend.extensions import db
from pywebpush import webpush, WebPushException

class PushSubscription(db.Model):
    """Push subscription model for Web-Push notifications"""
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), 
                         nullable=False, index=True)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.String(255), nullable=False)
    auth_key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<PushSubscription {self.member_id}>'

class NotifierService:
    """Notification service for PWA/Web-Push"""
    
    @staticmethod
    def send_push_notification(user_id, title, message, data=None, notification_type='general'):
        """Send push notification to user"""
        try:
            # Get user's push subscriptions
            subscriptions = PushSubscription.query.filter_by(member_id=user_id).all()
            
            if not subscriptions:
                current_app.logger.info(f"No push subscriptions found for user {user_id}")
                return False
            
            payload = {
                'title': title,
                'body': message,
                'type': notification_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if data:
                payload.update(data)
            
            success_count = 0
            for subscription in subscriptions:
                try:
                    success = NotifierService._send_to_subscription(subscription, payload)
                    if success:
                        success_count += 1
                        subscription.last_used_at = datetime.utcnow()
                    else:
                        # Remove invalid subscription
                        db.session.delete(subscription)
                except Exception as e:
                    current_app.logger.error(f"Error sending to subscription {subscription.id}: {e}")
                    db.session.delete(subscription)
            
            db.session.commit()
            current_app.logger.info(f"Push notification sent to {success_count}/{len(subscriptions)} subscriptions for user {user_id}")
            return success_count > 0
            
        except Exception as e:
            current_app.logger.error(f"Error sending push notification to user {user_id}: {e}")
            return False
    
    @staticmethod
    def send_billbro_start(event_id, user_ids):
        """Send BillBro start notification to participants"""
        from backend.models.event import Event
        
        event = Event.query.get(event_id)
        if not event:
            return False
        
        title = "BillBro gestartet!"
        message = f"🍽️ BillBro für {event.restaurant or event.event_typ.value} ist gestartet. Jetzt schätzen!"
        
        data = {
            'type': 'billbro_start',
            'event_id': event_id,
            'event_name': event.restaurant or event.event_typ.value,
            'event_date': event.display_date
        }
        
        success_count = 0
        for user_id in user_ids:
            if NotifierService.send_push_notification(user_id, title, message, data, 'billbro_start'):
                success_count += 1
        
        current_app.logger.info(f"BillBro start notification sent to {success_count}/{len(user_ids)} users")
        return success_count > 0
    
    @staticmethod
    def send_billbro_reminder(event_id, user_ids):
        """Send BillBro reminder to users who haven't guessed yet"""
        from backend.models.event import Event
        
        event = Event.query.get(event_id)
        if not event:
            return False
        
        title = "Schätzung ausstehend"
        message = f"⏰ Du hast noch nicht für {event.restaurant or event.event_typ.value} geschätzt!"
        
        data = {
            'type': 'billbro_reminder',
            'event_id': event_id,
            'event_name': event.restaurant or event.event_typ.value
        }
        
        success_count = 0
        for user_id in user_ids:
            if NotifierService.send_push_notification(user_id, title, message, data, 'billbro_reminder'):
                success_count += 1
        
        current_app.logger.info(f"BillBro reminder sent to {success_count}/{len(user_ids)} users")
        return success_count > 0
    
    @staticmethod
    def send_event_reminder(event_id, user_ids):
        """Send event reminder to multiple users"""
        from backend.models.event import Event
        
        event = Event.query.get(event_id)
        if not event:
            return False
        
        title = "Event-Erinnerung"
        message = f"📅 Vergiss nicht: {event.restaurant or event.event_typ.value} am {event.display_date}"
        
        data = {
            'type': 'event_reminder',
            'event_id': event_id,
            'event_name': event.restaurant or event.event_typ.value,
            'event_date': event.display_date
        }
        
        success_count = 0
        for user_id in user_ids:
            if NotifierService.send_push_notification(user_id, title, message, data, 'event_reminder'):
                success_count += 1
        
        current_app.logger.info(f"Event reminder sent to {success_count}/{len(user_ids)} users")
        return success_count > 0
    
    @staticmethod
    def subscribe_user_to_push(user_id, subscription_data):
        """Subscribe user to push notifications"""
        try:
            # Remove existing subscriptions for this user
            PushSubscription.query.filter_by(member_id=user_id).delete()
            
            # Create new subscription
            subscription = PushSubscription(
                member_id=user_id,
                endpoint=subscription_data['endpoint'],
                p256dh_key=subscription_data['keys']['p256dh'],
                auth_key=subscription_data['keys']['auth']
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            current_app.logger.info(f"User {user_id} subscribed to push notifications")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error subscribing user {user_id} to push notifications: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def unsubscribe_user_from_push(user_id):
        """Unsubscribe user from push notifications"""
        try:
            deleted_count = PushSubscription.query.filter_by(member_id=user_id).delete()
            db.session.commit()
            
            current_app.logger.info(f"User {user_id} unsubscribed from push notifications ({deleted_count} subscriptions removed)")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error unsubscribing user {user_id} from push notifications: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _send_to_subscription(subscription, payload):
        """Send push notification to a specific subscription"""
        try:
            # Prepare subscription data for pywebpush
            subscription_data = {
                'endpoint': subscription.endpoint,
                'keys': {
                    'p256dh': subscription.p256dh_key,
                    'auth': subscription.auth_key
                }
            }
            
            # Prepare VAPID data
            vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
            vapid_claims = current_app.config.get('VAPID_CLAIMS', {'sub': 'mailto:admin@gourmen.ch'})
            
            # Send push notification using pywebpush
            response = webpush(
                subscription_info=subscription_data,
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            
            current_app.logger.info(f"Push notification sent to subscription {subscription.id}: {response.status_code}")
            return True
            
        except WebPushException as e:
            current_app.logger.error(f"WebPush error for subscription {subscription.id}: {e}")
            # If subscription is invalid, mark it for deletion
            if e.response and e.response.status_code in [410, 404]:
                current_app.logger.info(f"Subscription {subscription.id} is invalid, will be removed")
                return False
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error sending to subscription {subscription.id}: {e}")
            return False 