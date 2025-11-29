"""
Demo Routes for Design System V2
Accessible to all logged-in users for testing
"""
from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('demo', __name__, url_prefix='/demo')

@bp.route('/design-system')
@login_required
def design_system():
    """Design System V2 Demo Page"""
    return render_template('demo/design-system.html')

