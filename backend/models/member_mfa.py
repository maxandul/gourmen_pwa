from datetime import datetime
from backend.extensions import db

class MemberMFA(db.Model):
    """MFA data for members"""
    __tablename__ = 'member_mfa'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         unique=True, nullable=False, index=True)
    
    # Encrypted TOTP secret
    totp_secret_encrypted = db.Column(db.Text)
    
    # 2FA status
    is_totp_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    activated_at = db.Column(db.DateTime)
    last_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MemberMFA {self.member_id}>' 