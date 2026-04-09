"""
Cron Job Routes für Railway Deployment
Einfache HTTP-Endpunkte für automatische Aufgaben
"""

from flask import Blueprint, request, jsonify, current_app
from backend.services.cron_service import CronService
from backend.extensions import csrf
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('cron', __name__)


def _is_authorized_cron_request():
    """
    Prüft Cron-Auth robust über:
    - X-Cron-Auth
    - Authorization: Bearer <token>
    - ?token=<token> (Fallback für Scheduler ohne Header-Support)
    """
    expected_auth = current_app.config.get('CRON_AUTH_TOKEN')

    # Lokale Entwicklung ohne Token erlauben, aber klar loggen.
    if not expected_auth:
        if current_app.debug or current_app.config.get('ENV') == 'development':
            logger.warning("CRON_AUTH_TOKEN not set; allowing cron request in development mode")
            return True
        logger.error("CRON_AUTH_TOKEN missing in non-development environment")
        return False

    header_token = request.headers.get('X-Cron-Auth')
    bearer_token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    query_token = request.args.get('token')

    return expected_auth in {header_token, bearer_token, query_token}

@bp.route('/cron/3-week-reminders', methods=['POST', 'GET'])
@csrf.exempt
def cron_3_week_reminders():
    """
    Cron-Job Endpoint für 3-Wochen-Erinnerungen
    Railway Cron-Job: curl -X POST https://your-app.railway.app/cron/3-week-reminders
    """
    try:
        if not _is_authorized_cron_request():
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

@bp.route('/cron/status', methods=['GET'])
@csrf.exempt
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

@bp.route('/cron/weekly-reminders', methods=['POST', 'GET'])
@csrf.exempt
def cron_weekly_reminders():
    """
    Cron-Job Endpoint für Wochen-Erinnerungen (Montag vor Event)
    Railway Cron-Job: curl -X POST https://your-app.railway.app/cron/weekly-reminders
    """
    try:
        if not _is_authorized_cron_request():
            logger.warning(f"Unauthorized cron request from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        result = CronService.run_weekly_reminders()
        
        if result['success']:
            logger.info(f"Cron job weekly reminders completed: {result}")
            return jsonify(result)
        else:
            logger.error(f"Cron job weekly reminders failed: {result}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in cron weekly reminders: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cron/rating-reminders', methods=['POST', 'GET'])
@csrf.exempt
def cron_rating_reminders():
    """
    Cron-Job Endpoint für Rating-Erinnerungen (Tag nach Event)
    Railway Cron-Job: curl -X POST https://your-app.railway.app/cron/rating-reminders
    """
    try:
        if not _is_authorized_cron_request():
            logger.warning(f"Unauthorized cron request from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        
        result = CronService.run_rating_reminders()
        
        if result['success']:
            logger.info(f"Cron job rating reminders completed: {result}")
            return jsonify(result)
        else:
            logger.error(f"Cron job rating reminders failed: {result}")
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in cron rating reminders: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cron/test', methods=['POST'])
@csrf.exempt
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
