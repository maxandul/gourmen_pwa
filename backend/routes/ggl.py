from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from backend.services.ggl_rules import GGLService
from backend.models.member import Member

bp = Blueprint('ggl', __name__)

@bp.route('/')
@login_required
def index():
    """GGL main page"""
    # Get current season
    current_season = GGLService.get_current_season()
    
    # Get available seasons (only past and current, no future seasons)
    available_seasons = GGLService.get_available_seasons()
    available_seasons = [season for season in available_seasons if season <= current_season]
    
    # Get user's stats for each season
    season_stats = {}
    for season in available_seasons:
        stats = GGLService.get_member_season_stats(current_user.id, season)
        if stats:
            # Calculate rank for this season
            season_ranking = GGLService.get_season_ranking(season)
            user_rank = None
            for i, member_stats in enumerate(season_ranking):
                if member_stats['member_id'] == current_user.id:
                    user_rank = i + 1
                    break
            
            # Add rank to stats
            stats['rank'] = user_rank
            season_stats[season] = stats
    
    return render_template('ggl/index.html',
                         current_season=current_season,
                         available_seasons=available_seasons,
                         season_stats=season_stats)

@bp.route('/season/<int:season_year>')
@login_required
def season(season_year):
    """Season ranking"""
    # Get season ranking
    season_ranking = GGLService.get_season_ranking(season_year)
    
    # Get member details for ranking
    for rank_entry in season_ranking:
        member = Member.query.get(rank_entry['member_id'])
        rank_entry['member'] = member
    
    # Get user's stats for this season
    user_stats = GGLService.get_member_season_stats(current_user.id, season_year)
    
    # Get progression data for chart
    progression_data = GGLService.get_season_progression_data(season_year)
    
    return render_template('ggl/season.html',
                         season_year=season_year,
                         season_ranking=season_ranking,
                         user_stats=user_stats,
                         progression_data=progression_data) 