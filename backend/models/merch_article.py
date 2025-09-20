from datetime import datetime
from backend.extensions import db

class MerchArticle(db.Model):
    """Merch article model - base article information"""
    __tablename__ = 'merch_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    base_supplier_price_rappen = db.Column(db.Integer, nullable=False)  # Price from supplier
    base_member_price_rappen = db.Column(db.Integer, nullable=False)     # Price for members
    image_url = db.Column(db.String(500))  # Path to article image
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    variants = db.relationship('MerchVariant', backref='article', cascade='all, delete-orphan')
    order_items = db.relationship('MerchOrderItem', backref='article')
    
    def __repr__(self):
        return f'<MerchArticle {self.id}: {self.name}>'
    
    @property
    def base_supplier_price_chf(self):
        """Get base supplier price in CHF"""
        return self.base_supplier_price_rappen / 100
    
    @property
    def base_member_price_chf(self):
        """Get base member price in CHF"""
        return self.base_member_price_rappen / 100
    
    @property
    def base_profit_rappen(self):
        """Get base profit in Rappen"""
        return self.base_member_price_rappen - self.base_supplier_price_rappen
    
    @property
    def base_profit_chf(self):
        """Get base profit in CHF"""
        return self.base_profit_rappen / 100
    
    def get_active_variants(self):
        """Get all active variants for this article"""
        return MerchVariant.query.filter_by(article_id=self.id, is_active=True).all()
    
    def get_variant_by_color_size(self, color, size):
        """Get specific variant by color and size"""
        return MerchVariant.query.filter_by(
            article_id=self.id, 
            color=color, 
            size=size, 
            is_active=True
        ).first()
