from flask import Blueprint, render_template
from flask_login import login_required
from backend.models.event import Event
from backend.models.participation import Participation
from backend.models.member import Member
from backend.extensions import db

bp = Blueprint('stats', __name__)

@bp.route('/')
@login_required
def index():
    """Statistics page"""
    # Get basic stats
    total_events = Event.query.count()
    total_members = Member.query.filter_by(is_active=True).count()
    total_participations = Participation.query.filter_by(teilnahme=True).count()
    
    # Get events by type
    events_by_type = db.session.query(
        Event.event_typ,
        db.func.count(Event.id)
    ).group_by(Event.event_typ).all()
    
    # Get participation stats
    participation_stats = db.session.query(
        db.func.count(Participation.id).label('total'),
        db.func.sum(db.case([(Participation.teilnahme == True, 1)], else_=0)).label('attending')
    ).first()
    
    return render_template('stats/index.html',
                         total_events=total_events,
                         total_members=total_members,
                         total_participations=total_participations,
                         events_by_type=events_by_type,
                         participation_stats=participation_stats) 