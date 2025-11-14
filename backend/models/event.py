from datetime import datetime
from enum import Enum
from backend.extensions import db

class EventType(Enum):
    MONATSESSEN = 'MONATSESSEN'
    AUSFLUG = 'AUSFLUG'
    GENERALVERSAMMLUNG = 'GENERALVERSAMMLUNG'

class Event(db.Model):
    """Event model for association events"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    organisator_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                              nullable=False, index=True)
    
    # Event details
    datum = db.Column(db.DateTime, nullable=False, index=True)
    event_typ = db.Column(db.Enum(EventType), nullable=False)
    restaurant = db.Column(db.String(200))
    kueche = db.Column(db.String(100))
    
    # Google Places data
    place_id = db.Column(db.String(255), index=True)  # Google Place ID
    place_name = db.Column(db.String(200))  # Full restaurant name
    place_address = db.Column(db.String(500))  # Formatted address
    place_lat = db.Column(db.Float)  # Latitude
    place_lng = db.Column(db.Float)  # Longitude
    place_types = db.Column(db.JSON)  # Array of place types
    place_website = db.Column(db.String(500))  # Restaurant website
    place_maps_url = db.Column(db.String(500))  # Google Maps URL
    place_price_level = db.Column(db.Integer)  # Price level (0-4)
    
    # Address components
    place_street_number = db.Column(db.String(20))
    place_route = db.Column(db.String(200))
    place_postal_code = db.Column(db.String(20))
    place_locality = db.Column(db.String(100))
    place_country = db.Column(db.String(100))
    
    # Additional event details
    website = db.Column(db.String(200))
    notizen = db.Column(db.Text)
    
    # Season (year of event date)
    season = db.Column(db.Integer, nullable=False)
    
    # Financial data (in Rappen)
    rechnungsbetrag_rappen = db.Column(db.Integer)
    gesamtbetrag_rappen = db.Column(db.Integer)
    trinkgeld_rappen = db.Column(db.Integer)
    
    # Share amounts (in Rappen)
    betrag_sparsam_rappen = db.Column(db.Integer)
    betrag_normal_rappen = db.Column(db.Integer)
    betrag_allin_rappen = db.Column(db.Integer)
    
    # BillBro configuration
    weights_used_json = db.Column(db.JSON, default={
        "sparsam": 0.7,
        "normal": 1.0,
        "allin": 1.3
    })
    tip_rule = db.Column(db.String(50), default="7pct_round10")
    rounding_rule = db.Column(db.String(50), default="ceil_10")
    billbro_closed = db.Column(db.Boolean, default=False, nullable=False)
    
    # Publication status
    published = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participations = db.relationship('Participation', backref='event', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='event')
    
    def __repr__(self):
        event_type = self.event_typ.value if hasattr(self.event_typ, 'value') else str(self.event_typ)
        return f'<Event {self.id}: {event_type} am {self.datum.date()}>'
    
    @property
    def organisator(self):
        """Get event organizer"""
        from backend.models.member import Member
        return Member.query.get(self.organisator_id)
    
    @property
    def is_past(self):
        """Check if event is in the past"""
        return self.datum < datetime.utcnow()
    
    @property
    def is_today(self):
        """Check if event is today"""
        today = datetime.utcnow().date()
        return self.datum.date() == today
    
    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.datum > datetime.utcnow()
    
    @property
    def display_date(self):
        """Get formatted date for display"""
        return self.datum.strftime('%d.%m.%Y')
    
    @property
    def display_time(self):
        """Get formatted time for display"""
        return self.datum.strftime('%H:%M')
    
    @property
    def display_datetime(self):
        """Get formatted date and time for display"""
        return self.datum.strftime('%d.%m.%Y %H:%M')
    
    def get_participation_count(self):
        """Get number of participants"""
        return sum(1 for p in self.participations if p.teilnahme)
    
    def get_total_participants(self):
        """Get total number of participants (including non-attendees)"""
        return len(self.participations)
    
    def get_total_members_count(self):
        """Get total number of all members in the system"""
        from backend.models.member import Member
        return Member.query.count()
    
    @property
    def billbro_sparsam_weight(self):
        """Get sparsam weight for BillBro calculations"""
        return self.weights_used_json.get('sparsam', 0.7)
    
    @property
    def billbro_normal_weight(self):
        """Get normal weight for BillBro calculations"""
        return self.weights_used_json.get('normal', 1.0)
    
    @property
    def billbro_allin_weight(self):
        """Get all-in weight for BillBro calculations"""
        return self.weights_used_json.get('allin', 1.3)
    
    # Rating methods
    def get_ratings(self):
        """Get all ratings for this event"""
        from backend.models.rating import EventRating
        return EventRating.query.filter_by(event_id=self.id).all()
    
    def get_average_ratings(self):
        """Get average ratings for this event"""
        from backend.models.rating import EventRating
        ratings = EventRating.query.filter_by(event_id=self.id).all()
        
        if not ratings:
            return {
                'food': 0,
                'drinks': 0,
                'service': 0,
                'overall': 0,
                'count': 0
            }
        
        food_avg = sum(r.food_rating for r in ratings) / len(ratings)
        drinks_avg = sum(r.drinks_rating for r in ratings) / len(ratings)
        service_avg = sum(r.service_rating for r in ratings) / len(ratings)
        overall_avg = sum(r.average_rating for r in ratings) / len(ratings)
        
        return {
            'food': round(food_avg, 1),
            'drinks': round(drinks_avg, 1),
            'service': round(service_avg, 1),
            'overall': round(overall_avg, 1),
            'count': len(ratings)
        }
    
    def has_rating_from_participant(self, participant_id):
        """Check if participant has already rated this event"""
        from backend.models.rating import EventRating
        return EventRating.query.filter_by(
            event_id=self.id, 
            participant_id=participant_id
        ).first() is not None 