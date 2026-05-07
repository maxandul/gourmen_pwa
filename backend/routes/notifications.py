from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend.services.notifier import NotifierService
from backend.services.vapid_service import VAPIDService
from backend.services.security import SecurityService, AuditAction
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('notifications', __name__)

@bp.route('/vapid-public-key')
def get_vapid_public_key():
    """Legacy: gleicher Zweck wie /api/vapid-public-key — Antwort `publicKey` (camelCase)."""
    try:
        public_key = VAPIDService.get_vapid_public_key()
        return jsonify({'publicKey': public_key})
    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return jsonify({'error': 'Öffentlicher VAPID-Schlüssel nicht verfügbar'}), 500

@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Legacy: gleicher Zweck wie POST /api/push/subscribe (NotifierService)."""
    try:
        data = request.get_json()
        subscription_data = data.get('subscription')
        
        if not subscription_data:
            return jsonify({'error': 'Subscription-Daten fehlen'}), 400
        
        # Validate subscription data
        required_fields = ['endpoint', 'keys']
        if not all(field in subscription_data for field in required_fields):
            return jsonify({'error': 'Ungültige Subscription-Daten'}), 400
        
        if not all(key in subscription_data['keys'] for key in ['p256dh', 'auth']):
            return jsonify({'error': 'Ungültige Subscription-Keys'}), 400
        
        # Subscribe user
        success = NotifierService.subscribe_user_to_push(current_user.id, subscription_data)
        
        if success:
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.PUSH_SUBSCRIBE, 'member', current_user.id,
                extra_data={
                    'endpoint': subscription_data['endpoint'][:50] + '...'  # Truncate for privacy
                }
            )
            
            return jsonify({'success': True, 'message': 'Push-Benachrichtigungen sind aktiviert.'})
        else:
            return jsonify({'error': 'Registrierung der Push-Subscription fehlgeschlagen'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in push subscription: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Legacy: gleicher Zweck wie POST /api/push/unsubscribe."""
    try:
        success = NotifierService.unsubscribe_user_from_push(current_user.id)
        
        if success:
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.PUSH_UNSUBSCRIBE, 'member', current_user.id
            )
            
            return jsonify({'success': True, 'message': 'Push-Benachrichtigungen abgemeldet.'})
        else:
            return jsonify({'error': 'Abmeldung fehlgeschlagen'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in push unsubscription: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

@bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Nur in DEBUG: Test-Push über NotifierService (Legacy-Pfad)."""
    if not current_app.debug:
        return jsonify({'error': 'Test ist in Produktion nicht verfügbar.'}), 403
    
    try:
        title = 'Gourmen Test'
        message = 'Das ist eine Test-Push-Benachrichtigung.'
        
        success = NotifierService.send_push_notification(
            current_user.id, title, message, 
            {'type': 'test'}, 'test'
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Test-Benachrichtigung gesendet.'})
        else:
            return jsonify({'error': 'Test-Benachrichtigung konnte nicht gesendet werden'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'Interner Fehler'}), 500

