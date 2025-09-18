"""
Push Notifications API Routes
Handles Push Subscription Management und VAPID Keys
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend.services.push_notifications import PushNotificationService
from backend.services.vapid_service import VAPIDService
from backend.models.push_subscription import PushSubscription
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('push_notifications', __name__)

@bp.route('/api/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """Holt den öffentlichen VAPID-Key für Push-Subscriptions"""
    try:
        public_key = VAPIDService.get_vapid_public_key()
        return jsonify({
            'public_key': public_key
        })
    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return jsonify({'error': 'VAPID key not available'}), 500

@bp.route('/api/push/subscribe', methods=['POST'])
@login_required
def subscribe_to_push():
    """Registriert den aktuellen Benutzer für Push-Benachrichtigungen"""
    try:
        data = request.get_json()
        
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Subscription data required'}), 400
        
        subscription_data = data['subscription']
        user_agent = request.headers.get('User-Agent')
        
        # Validiere Subscription-Daten
        required_keys = ['endpoint', 'keys']
        if not all(key in subscription_data for key in required_keys):
            return jsonify({'error': 'Invalid subscription data'}), 400
        
        required_key_keys = ['p256dh', 'auth']
        if not all(key in subscription_data['keys'] for key in required_key_keys):
            return jsonify({'error': 'Invalid subscription keys'}), 400
        
        # Registriere Subscription
        success = PushNotificationService.subscribe_member_to_push(
            current_user.id,
            subscription_data,
            user_agent
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully subscribed to push notifications'
            })
        else:
            return jsonify({'error': 'Failed to subscribe'}), 500
            
    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/push/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_from_push():
    """Entfernt Push-Subscription des aktuellen Benutzers"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint') if data else None
        
        success = PushNotificationService.unsubscribe_member_from_push(
            current_user.id,
            endpoint
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Successfully unsubscribed from push notifications'
            })
        else:
            return jsonify({'error': 'No subscription found to unsubscribe'}), 404
            
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/push/subscription-status', methods=['GET'])
@login_required
def get_subscription_status():
    """Holt den Push-Subscription Status des aktuellen Benutzers"""
    try:
        subscriptions = PushSubscription.query.filter_by(
            member_id=current_user.id,
            is_active=True
        ).all()
        
        return jsonify({
            'subscribed': len(subscriptions) > 0,
            'subscription_count': len(subscriptions),
            'subscriptions': [
                {
                    'id': sub.id,
                    'endpoint': sub.endpoint[:50] + '...' if len(sub.endpoint) > 50 else sub.endpoint,
                    'created_at': sub.created_at.isoformat(),
                    'last_used_at': sub.last_used_at.isoformat() if sub.last_used_at else None
                }
                for sub in subscriptions
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/push/test', methods=['POST'])
@login_required
def test_push_notification():
    """Sendet eine Test-Push-Benachrichtigung an den aktuellen Benutzer"""
    try:
        # Hole aktive Subscriptions des Benutzers
        subscriptions = PushSubscription.query.filter_by(
            member_id=current_user.id,
            is_active=True
        ).all()
        
        if not subscriptions:
            return jsonify({'error': 'No active subscriptions found'}), 400
        
        # Test-Payload
        payload = {
            'title': 'Gourmen Test-Benachrichtigung',
            'body': f'Hallo {current_user.display_name}! Dies ist eine Test-Push-Benachrichtigung.',
            'icon': '/static/img/pwa/icon-192.png',
            'badge': '/static/img/pwa/icon-96.png',
            'tag': 'gourmen-test',
            'data': {
                'url': '/account/profile',
                'type': 'test_notification'
            }
        }
        
        sent_count = 0
    for subscription in subscriptions:
        result = PushNotificationService.send_push_notification(subscription.subscription_data, payload, return_error_details=True)
        if (isinstance(result, dict) and result.get('success')) or result is True:
            subscription.mark_used()
            sent_count += 1
        else:
            logger.warning(f"Push send failed for endpoint {subscription.endpoint[:50]}... result={result}")
        
        return jsonify({
            'success': True,
            'message': f'Test notification sent to {sent_count}/{len(subscriptions)} devices',
            'sent_count': sent_count,
            'total_subscriptions': len(subscriptions)
        })
        
    except Exception as e:
        logger.error(f"Error sending test push notification: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/push/cron/3-week-reminders', methods=['POST'])
def trigger_3_week_reminders():
    """
    Cron-Job Endpoint für 3-Wochen-Erinnerungen
    Sollte mit einem API-Key gesichert werden
    """
    try:
        # TODO: API-Key Authentifizierung hinzufügen
        # auth_header = request.headers.get('Authorization')
        # if auth_header != f'Bearer {current_app.config.get("CRON_API_KEY")}':
        #     return jsonify({'error': 'Unauthorized'}), 401
        
        result = PushNotificationService.check_and_send_3_week_reminders()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error triggering 3-week reminders: {e}")
        return jsonify({'error': str(e)}), 500
