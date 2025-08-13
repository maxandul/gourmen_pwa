from datetime import datetime
from enum import Enum
from backend.extensions import db

class Esstyp(Enum):
    SPARSAM = 'sparsam'
    NORMAL = 'normal'
    ALLIN = 'allin'

class Participation(db.Model):
    """Participation model for event attendance and BillBro guesses"""
    __tablename__ = 'participations'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='RESTRICT'), 
                        nullable=False, index=True)
    
    # Participation status
    teilnahme = db.Column(db.Boolean, nullable=False)
    
    # BillBro data
    esstyp = db.Column(db.Enum(Esstyp))
    guess_bill_amount_rappen = db.Column(db.Integer)  # Guess for total bill (without tip)
    diff_amount_rappen = db.Column(db.Integer)        # |guess - actual_bill|
    rank = db.Column(db.Integer)                      # 1 = best guess
    points = db.Column(db.Integer)                    # GGL points earned
    calculated_share_rappen = db.Column(db.Integer)   # Final amount to pay
    
    # Timestamps
    responded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one participation per member per event
    __table_args__ = (
        db.UniqueConstraint('member_id', 'event_id', name='uq_member_event'),
    )
    
    def __repr__(self):
        return f'<Participation {self.member_id} at Event {self.event_id}>'
    
    @property
    def member(self):
        """Get associated member"""
        from backend.models.member import Member
        return Member.query.get(self.member_id)
    
    @property
    def event(self):
        """Get associated event"""
        from backend.models.event import Event
        return Event.query.get(self.event_id)
    
    @property
    def has_guess(self):
        """Check if member has made a guess"""
        return self.guess_bill_amount_rappen is not None
    
    @property
    def has_esstyp(self):
        """Check if member has selected eating type"""
        return self.esstyp is not None
    
    @property
    def is_complete(self):
        """Check if participation is complete (attending + eating type + guess)"""
        return (self.teilnahme and 
                self.has_esstyp and 
                self.has_guess)
    
    @property
    def display_guess(self):
        """Get formatted guess amount"""
        if self.guess_bill_amount_rappen is None:
            return None
        from backend.services.money import MoneyService
        return MoneyService.to_franken(self.guess_bill_amount_rappen)
    
    @property
    def display_share(self):
        """Get formatted share amount"""
        if self.calculated_share_rappen is None:
            return None
        from backend.services.money import MoneyService
        return MoneyService.to_franken(self.calculated_share_rappen)
    
    @property
    def display_diff(self):
        """Get formatted difference amount"""
        if self.diff_amount_rappen is None:
            return None
        from backend.services.money import MoneyService
        return MoneyService.to_franken(self.diff_amount_rappen) 