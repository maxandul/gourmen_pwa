from flask import Blueprint, current_app, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.merch_order import MerchLegacyOrderStatus, MerchOrderLegacy
from backend.services.ggl_rules import GGLService
from backend.services.retro_cleanup import RetroCleanupService
from backend.routes.events import hamburg2026_is_visible
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
    season_ranking = GGLService.get_season_ranking(current_season)
    rank_total = len(season_ranking)

    if ggl_stats:
        user_rank = None
        for i, member_stats in enumerate(season_ranking):
            if member_stats['member_id'] == current_user.id:
                user_rank = i + 1
                break

        ggl_stats['rank'] = user_rank
        ggl_stats['points'] = ggl_stats['total_points']
        ggl_stats['rank_total'] = rank_total
    else:
        ggl_stats = {
            'season': current_season,
            'total_points': 0,
            'participation_count': 0,
            'total_events_in_season': 0,
            'rank': None,
            'points': 0,
            'rank_total': rank_total,
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

    rsvp_prompt_event = RetroCleanupService.get_upcoming_rsvp_prompt_event(current_user.id)
    today_billbro_event = RetroCleanupService.get_today_billbro_prompt_event(current_user.id)
    restaurant_due_event = Event.query.filter(
        Event.organisator_id == current_user.id,
        Event.published == True,
        Event.datum >= today,
        Event.datum <= (today + timedelta(days=30)),
        ((Event.restaurant.is_(None)) | (Event.restaurant == ''))
    ).order_by(Event.datum.asc()).first()

    merch_orders = (
        MerchOrderLegacy.query.filter_by(member_id=current_user.id)
        .order_by(MerchOrderLegacy.created_at.desc())
        .all()
    )
    merch_last_order = merch_orders[0] if merch_orders else None
    merch_open_count = sum(
        1
        for o in merch_orders
        if o.status
        in (MerchLegacyOrderStatus.BESTELLT, MerchLegacyOrderStatus.WIRD_GELIEFERT)
    )

    merch_v2_dashboard = None
    if current_app.config.get('MERCH_V2_ENABLED'):
        from backend.models.merch_v2 import MerchOrder, MerchOrderStatus, MerchRoundStatus

        recent_v2 = (
            MerchOrder.query.options(joinedload(MerchOrder.round))
            .filter(
                MerchOrder.member_id == current_user.id,
                MerchOrder.status != MerchOrderStatus.CANCELLED,
            )
            .order_by(MerchOrder.updated_at.desc())
            .limit(24)
            .all()
        )
        line1 = 'Keine offenen Merch-Bestellungen'
        line2 = ''
        round_id = None
        for o in recent_v2:
            if o.status == MerchOrderStatus.PAID and o.picked_up_at:
                continue
            if o.status == MerchOrderStatus.DRAFT and o.round.status == MerchRoundStatus.OPEN:
                line1 = f'Warenkorb offen: «{o.round.title}»'
                line2 = (o.updated_at or o.created_at).strftime('%d.%m.%Y')
                round_id = o.round_id
                break
            if o.status in (
                MerchOrderStatus.CONFIRMED,
                MerchOrderStatus.INVOICED,
                MerchOrderStatus.PICKED_UP,
            ) or (o.status == MerchOrderStatus.PAID and not o.picked_up_at):
                line1 = f'«{o.round.title}»: {o.status.value}'
                if o.member_amount_due_rappen and not o.paid_at:
                    line2 = (
                        f'Offen CHF {"%.2f" % (o.member_amount_due_rappen / 100.0)} — '
                        + (o.updated_at or o.created_at).strftime('%d.%m.%Y')
                    )
                else:
                    line2 = (o.updated_at or o.created_at).strftime('%d.%m.%Y')
                round_id = o.round_id
                break
        merch_v2_dashboard = {'line1': line1, 'line2': line2, 'round_id': round_id}

    return render_template(
        'dashboard/index.html',
        next_event=next_event,
        ggl_stats=ggl_stats,
        current_season=current_season,
        latest_bill_event=latest_bill_event,
        latest_bill_participation=latest_bill_participation,
        rsvp_prompt_event=rsvp_prompt_event,
        today_billbro_event=today_billbro_event,
        restaurant_due_event=restaurant_due_event,
        merch_last_order=merch_last_order,
        merch_open_count=merch_open_count,
        merch_v2_dashboard=merch_v2_dashboard,
        hamburg2026_visible=hamburg2026_is_visible(),
    )

 