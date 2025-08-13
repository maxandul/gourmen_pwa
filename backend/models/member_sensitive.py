from datetime import datetime
from backend.extensions import db

class MemberSensitive(db.Model):
    """Sensitive member data - encrypted"""
    __tablename__ = 'member_sensitive'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         unique=True, nullable=False, index=True)
    
    # Encrypted JSON payload containing sensitive data
    payload_encrypted = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MemberSensitive {self.member_id}>'
    
    @property
    def member(self):
        """Get associated member"""
        from backend.models.member import Member
        return Member.query.get(self.member_id) 