from datetime import datetime
from backend.extensions import db

class MerchVariant(db.Model):
    """Merch variant model - specific color/size combinations"""
    __tablename__ = 'merch_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('merch_articles.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    color = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    supplier_price_rappen = db.Column(db.Integer, nullable=False)  # Price from supplier
    member_price_rappen = db.Column(db.Integer, nullable=False)     # Price for members
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('MerchOrderItem', backref='variant')
    
    def __repr__(self):
        return f'<MerchVariant {self.id}: {self.article.name} {self.color} {self.size}>'
    
    @property
    def supplier_price_chf(self):
        """Get supplier price in CHF"""
        return self.supplier_price_rappen / 100
    
    @property
    def member_price_chf(self):
        """Get member price in CHF"""
        return self.member_price_rappen / 100
    
    @property
    def profit_rappen(self):
        """Get profit in Rappen"""
        return self.member_price_rappen - self.supplier_price_rappen
    
    @property
    def profit_chf(self):
        """Get profit in CHF"""
        return self.profit_rappen / 100
    
    @property
    def display_name(self):
        """Get display name for this variant"""
        return f"{self.article.name} {self.color} {self.size}"
    
    def get_available_colors(self):
        """Get all available colors for this article"""
        return db.session.query(MerchVariant.color).filter_by(
            article_id=self.article_id, 
            is_active=True
        ).distinct().all()
    
    def get_available_sizes(self):
        """Get all available sizes for this article and color"""
        return db.session.query(MerchVariant.size).filter_by(
            article_id=self.article_id, 
            color=self.color, 
            is_active=True
        ).distinct().all()

