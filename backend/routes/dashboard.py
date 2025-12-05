from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.models.event import Event
from backend.models.participation import Participation
from backend.services.ggl_rules import GGLService
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard main page"""
    # Get next upcoming event
    # An event is "upcoming" until the day AFTER the event date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    next_event = Event.query.filter(
        Event.datum >= today,
        Event.published == True
    ).order_by(Event.datum.asc()).first()
    
    # Get current season GGL stats for user
    current_season = GGLService.get_current_season()
    ggl_stats = GGLService.get_member_season_stats(current_user.id, current_season)
    
    # If user has GGL stats, calculate their rank
    if ggl_stats:
        season_ranking = GGLService.get_season_ranking(current_season)
        user_rank = None
        for i, member_stats in enumerate(season_ranking):
            if member_stats['member_id'] == current_user.id:
                user_rank = i + 1
                break
        
        # Add rank and points to ggl_stats
        ggl_stats['rank'] = user_rank
        ggl_stats['points'] = ggl_stats['total_points']
    else:
        # If no GGL stats, create empty stats for display
        ggl_stats = {
            'season': current_season,
            'total_points': 0,
            'participation_count': 0,
            'total_events_in_season': 0,
            'rank': None,
            'points': 0
        }
    
    # Get latest event with bill for current user
    latest_bill_event = Event.query.join(Participation).filter(
        Participation.member_id == current_user.id,
        Participation.calculated_share_rappen.isnot(None),
        Participation.calculated_share_rappen > 0
    ).order_by(Event.datum.desc()).first()
    
    # Get participation details for the latest bill event
    latest_bill_participation = None
    if latest_bill_event:
        latest_bill_participation = Participation.query.filter_by(
            member_id=current_user.id,
            event_id=latest_bill_event.id
        ).first()
    
    return render_template('dashboard/index.html', 
                         next_event=next_event, 
                         ggl_stats=ggl_stats,
                         current_season=current_season,
                         latest_bill_event=latest_bill_event,
                         latest_bill_participation=latest_bill_participation,
                         use_v2_design=True)

 