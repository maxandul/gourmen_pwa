from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from backend.services.notifier import NotifierService
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64
from backend.services.security import SecurityService, AuditAction

bp = Blueprint('notifications', __name__)

@bp.route('/vapid-public-key')
def get_vapid_public_key():
    """Get VAPID public key for frontend"""
    try:
        vapid_public_key_pem = current_app.config.get('VAPID_PUBLIC_KEY')
        if not vapid_public_key_pem:
            return jsonify({'error': 'VAPID public key not configured'}), 500
        
        # Load the PEM public key
        public_key = load_pem_public_key(vapid_public_key_pem.encode())
        
        # Get the raw public key bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        # Convert to base64url encoding (Web Push standard)
        public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
        
        return jsonify({'publicKey': public_key_b64})
        
    except Exception as e:
        current_app.logger.error(f"Error getting VAPID public key: {e}")
        return jsonify({'error': 'Failed to get VAPID public key'}), 500

@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Subscribe user to push notifications"""
    try:
        data = request.get_json()
        subscription_data = data.get('subscription')
        
        if not subscription_data:
            return jsonify({'error': 'No subscription data provided'}), 400
        
        # Validate subscription data
        required_fields = ['endpoint', 'keys']
        if not all(field in subscription_data for field in required_fields):
            return jsonify({'error': 'Invalid subscription data'}), 400
        
        if not all(key in subscription_data['keys'] for key in ['p256dh', 'auth']):
            return jsonify({'error': 'Missing subscription keys'}), 400
        
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
            
            return jsonify({'success': True, 'message': 'Successfully subscribed to push notifications'})
        else:
            return jsonify({'error': 'Failed to subscribe to push notifications'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in push subscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Unsubscribe user from push notifications"""
    try:
        success = NotifierService.unsubscribe_user_from_push(current_user.id)
        
        if success:
            # Log audit event
            SecurityService.log_audit_event(
                AuditAction.PUSH_UNSUBSCRIBE, 'member', current_user.id
            )
            
            return jsonify({'success': True, 'message': 'Successfully unsubscribed from push notifications'})
        else:
            return jsonify({'error': 'Failed to unsubscribe from push notifications'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in push unsubscription: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/test', methods=['POST'])
@login_required
def test_notification():
    """Test push notification for current user (development only)"""
    if not current_app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        title = "Test Notification"
        message = "This is a test push notification from Gourmen!"
        
        success = NotifierService.send_push_notification(
            current_user.id, title, message, 
            {'type': 'test'}, 'test'
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Test notification sent'})
        else:
            return jsonify({'error': 'Failed to send test notification'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error sending test notification: {e}")
        return jsonify({'error': 'Internal server error'}), 500

