from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.models.event import Event
from backend.services.ggl_rules import GGLService

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard main page"""
    # Get next upcoming event
    next_event = Event.query.filter(
        Event.datum > datetime.utcnow(),
        Event.published == True
    ).order_by(Event.datum.asc()).first()
    
    # Get current season GGL stats for user
    current_season = GGLService.get_current_season()
    ggl_stats = GGLService.get_member_season_stats(current_user.id, current_season)
    
    return render_template('dashboard/index.html', 
                         next_event=next_event, 
                         ggl_stats=ggl_stats,
                         current_season=current_season)

# Import here to avoid circular imports
from datetime import datetime 