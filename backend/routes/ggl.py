from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from backend.services.ggl_rules import GGLService
from backend.models.member import Member

bp = Blueprint('ggl', __name__)

def _attach_member_to_ranking(ranking):
    """Attach Member object to each ranking entry."""
    for rank_entry in ranking:
        member = Member.query.get(rank_entry['member_id'])
        rank_entry['member'] = member


@bp.route('/')
@login_required
def index():
    """GGL main page with tabs (Aktuell, Tabelle, Rennen, Archiv)."""
    tab = request.args.get('tab', 'aktuell')

    # Get current season
    current_season = GGLService.get_current_season()
    selected_season = request.args.get('season', type=int) or current_season

    # Get available seasons (only past and current, no future seasons)
    available_seasons = GGLService.get_available_seasons()
    available_seasons = [season for season in available_seasons if season <= current_season]

    # Get user's stats for each season
    season_stats = {}
    for season in available_seasons:
        stats = GGLService.get_member_season_stats(current_user.id, season)
        if stats:
            # Calculate rank for this season
            season_ranking_for_stat = GGLService.get_season_ranking(season)
            user_rank = None
            for i, member_stats in enumerate(season_ranking_for_stat):
                if member_stats['member_id'] == current_user.id:
                    user_rank = i + 1
                    break

            # Add rank to stats
            stats['rank'] = user_rank
            season_stats[season] = stats

    current_stats = season_stats.get(selected_season) or season_stats.get(current_season)

    season_ranking = None
    table_selected_season = selected_season
    if tab in ('tabelle', 'aktuell'):
        season_ranking = GGLService.get_season_ranking(selected_season)
        _attach_member_to_ranking(season_ranking)

    progression_data = None
    race_selected_season = selected_season
    if tab == 'rennen':
        progression_data = GGLService.get_season_progression_data(selected_season)

    return render_template(
        'ggl/index.html',
        current_season=current_season,
        selected_season=selected_season,
        available_seasons=available_seasons,
        season_stats=season_stats,
        current_stats=current_stats,
        season_ranking=season_ranking,
        progression_data=progression_data,
        table_selected_season=table_selected_season,
        race_selected_season=race_selected_season,
        active_tab=tab,
        use_v2_design=True
    )

@bp.route('/season/<int:season_year>')
@login_required
def season(season_year):
    """Redirect legacy season view to new index tabs."""
    tab = request.args.get('tab', 'tabelle')
    if tab == 'rennen':
        return redirect(url_for('ggl.index', tab='rennen', race_season=season_year))
    # default to tabelle
    return redirect(url_for('ggl.index', tab='tabelle', table_season=season_year))