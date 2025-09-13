"""
Push Subscription Model für Web Push Notifications
Speichert Push-Subscriptions der Mitglieder für echte Push-Benachrichtigungen
"""

from datetime import datetime
from backend.extensions import db

class PushSubscription(db.Model):
    """Push Subscription model für Web Push Notifications"""
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='CASCADE'), 
                         nullable=False, index=True)
    
    # Push subscription data
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    
    # User agent for debugging
    user_agent = db.Column(db.Text)
    
    # Subscription status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    
    # Relationships
    member = db.relationship('Member', backref='push_subscriptions')
    
    def __repr__(self):
        return f'<PushSubscription {self.member_id}: {self.endpoint[:50]}...>'
    
    @property
    def subscription_data(self):
        """Get subscription data in the format expected by pywebpush"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh_key,
                'auth': self.auth_key
            }
        }
    
    def mark_used(self):
        """Mark subscription as used (update last_used_at)"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()
