from datetime import datetime
from backend.extensions import db

class EventRating(db.Model):
    """Event rating model for participant feedback"""
    __tablename__ = 'event_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    
    # Rating scores (1-5)
    food_rating = db.Column(db.Integer, nullable=False)
    drinks_rating = db.Column(db.Integer, nullable=False)
    service_rating = db.Column(db.Integer, nullable=False)
    
    # Optional highlights/notes
    highlights = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', backref='ratings')
    participant = db.relationship('Member', backref='event_ratings')
    
    def __repr__(self):
        return f'<EventRating {self.id}: Event {self.event_id}, Participant {self.participant_id}>'
    
    @property
    def average_rating(self):
        """Calculate average rating from all three categories"""
        return round((self.food_rating + self.drinks_rating + self.service_rating) / 3, 1)
    
    def to_dict(self):
        """Convert rating to dictionary"""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'participant_id': self.participant_id,
            'participant_name': self.participant.full_name if self.participant else None,
            'food_rating': self.food_rating,
            'drinks_rating': self.drinks_rating,
            'service_rating': self.service_rating,
            'average_rating': self.average_rating,
            'highlights': self.highlights,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
