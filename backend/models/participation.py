from datetime import datetime
from enum import Enum
from backend.extensions import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func

class Esstyp(Enum):
    SPARSAM = 'SPARSAM'
    NORMAL = 'NORMAL'
    ALLIN = 'ALLIN'

class Participation(db.Model):
    """Participation model for event attendance and BillBro guesses"""
    __tablename__ = 'participations'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='RESTRICT'), 
                        nullable=False, index=True)
    
    # Participation status
    teilnahme = db.Column(db.Boolean, nullable=True)
    billbro_attendance = db.Column(db.Boolean, nullable=True)
    
    # BillBro data
    esstyp = db.Column(db.Enum(Esstyp))
    guess_bill_amount_rappen = db.Column(db.Integer)  # Guess for total bill (without tip)
    diff_amount_rappen = db.Column(db.Integer)        # |guess - actual_bill|
    rank = db.Column(db.Float)                      # 1 = best guess
    points = db.Column(db.Float)                    # GGL points earned
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
    
    @hybrid_property
    def billbro_attending(self):
        return self.billbro_attendance if self.billbro_attendance is not None else bool(self.teilnahme)

    @billbro_attending.expression
    def billbro_attending(cls):
        return func.coalesce(cls.billbro_attendance, cls.teilnahme, False)

    @property
    def rsvp_label(self):
        return 'Keine Antwort' if self.teilnahme is None else ('Zugesagt' if self.teilnahme else 'Abgesagt')

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
        return (self.billbro_attending and
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

def is_billbro_attending(part):
    """Also accept pure projection objects carrying the legacy boolean."""
    return getattr(part, 'billbro_attending', bool(part.teilnahme))
