from datetime import datetime
from backend.extensions import db

class MFABackupCode(db.Model):
    """MFA backup codes"""
    __tablename__ = 'mfa_backup_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    
    # Hashed backup code
    code_hash = db.Column(db.Text, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    used_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('member_id', 'code_hash', name='uq_member_backup_code'),
    )
    
    def __repr__(self):
        return f'<MFABackupCode {self.member_id}>'
    
    @property
    def member(self):
        """Get associated member"""
        from backend.models.member import Member
        return Member.query.get(self.member_id)
    
    @property
    def is_used(self):
        """Check if code has been used"""
        return self.used_at is not None
    
    @property
    def is_revoked(self):
        """Check if code has been revoked"""
        return self.revoked_at is not None
    
    @property
    def is_valid(self):
        """Check if code is still valid"""
        return not self.is_used and not self.is_revoked