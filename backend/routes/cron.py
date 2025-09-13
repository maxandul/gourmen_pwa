"""
Cron Job Routes für Railway Deployment
Einfache HTTP-Endpunkte für automatische Aufgaben
"""

from flask import Blueprint, request, jsonify, current_app
from backend.services.cron_service import CronService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('cron', __name__)

@bp.route('/cron/3-week-reminders', methods=['POST'])
def cron_3_week_reminders():
    """
    Cron-Job Endpoint für 3-Wochen-Erinnerungen
    Railway Cron-Job: curl -X POST https://your-app.railway.app/cron/3-week-reminders
    """
    try:
        # Einfache Authentifizierung über Header (für Railway Cron)
        auth_header = request.headers.get('X-Cron-Auth')
        expected_auth = current_app.config.get('CRON_AUTH_TOKEN', 'gourmen-cron-2024')
        
        if auth_header != expected_auth:
            logger.warning(f"Unauthorized cron request from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        result = CronService.run_3_week_reminders()
        
        if result['success']:
            logger.info(f"Cron job 3-week reminders completed: {result}")
            return jsonify(result)
        else:
            logger.error(f"Cron job 3-week reminders failed: {result}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in cron 3-week reminders: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cron/cleanup-subscriptions', methods=['POST'])
def cron_cleanup_subscriptions():
    """
    Cron-Job Endpoint für Subscription Cleanup
    Railway Cron-Job: curl -X POST https://your-app.railway.app/cron/cleanup-subscriptions
    """
    try:
        # Einfache Authentifizierung über Header (für Railway Cron)
        auth_header = request.headers.get('X-Cron-Auth')
        expected_auth = current_app.config.get('CRON_AUTH_TOKEN', 'gourmen-cron-2024')
        
        if auth_header != expected_auth:
            logger.warning(f"Unauthorized cron request from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        result = CronService.cleanup_old_subscriptions()
        
        if result['success']:
            logger.info(f"Cron job cleanup subscriptions completed: {result}")
            return jsonify(result)
        else:
            logger.error(f"Cron job cleanup subscriptions failed: {result}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in cron cleanup subscriptions: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cron/status', methods=['GET'])
def cron_status():
    """
    Cron-Job Status Endpoint
    """
    try:
        result = CronService.get_cron_status()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error getting cron status: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cron/test', methods=['POST'])
def cron_test():
    """
    Test Endpoint für Cron-Jobs (nur für Development)
    """
    try:
        if current_app.config.get('ENV') == 'production':
            return jsonify({'error': 'Test endpoint not available in production'}), 403
        
        # Teste 3-Wochen-Erinnerungen
        result = CronService.run_3_week_reminders()
        
        return jsonify({
            'message': 'Test cron job executed',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error in test cron: {e}")
        return jsonify({'error': str(e)}), 500
