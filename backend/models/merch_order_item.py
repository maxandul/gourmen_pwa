from datetime import datetime
from backend.extensions import db

class MerchOrderItem(db.Model):
    """Merch order item model - individual items in an order"""
    __tablename__ = 'merch_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('merch_orders.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('merch_articles.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('merch_variants.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_member_price_rappen = db.Column(db.Integer, nullable=False)  # Price per unit for member
    unit_supplier_price_rappen = db.Column(db.Integer, nullable=False)  # Price per unit for supplier
    total_member_price_rappen = db.Column(db.Integer, nullable=False)  # Total price for member
    total_supplier_price_rappen = db.Column(db.Integer, nullable=False)  # Total price for supplier
    total_profit_rappen = db.Column(db.Integer, nullable=False)  # Total profit for this item
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<MerchOrderItem {self.id}: {self.quantity}x {self.article.name} {self.variant.color} {self.variant.size}>'
    
    @property
    def unit_member_price_chf(self):
        """Get unit member price in CHF"""
        return self.unit_member_price_rappen / 100
    
    @property
    def unit_supplier_price_chf(self):
        """Get unit supplier price in CHF"""
        return self.unit_supplier_price_rappen / 100
    
    @property
    def total_member_price_chf(self):
        """Get total member price in CHF"""
        return self.total_member_price_rappen / 100
    
    @property
    def total_supplier_price_chf(self):
        """Get total supplier price in CHF"""
        return self.total_supplier_price_rappen / 100
    
    @property
    def total_profit_chf(self):
        """Get total profit in CHF"""
        return self.total_profit_rappen / 100
    
    @property
    def display_name(self):
        """Get display name for this item"""
        return f"{self.article.name} {self.variant.color} {self.variant.size}"
    
    def calculate_totals(self):
        """Calculate totals for this item"""
        self.total_member_price_rappen = self.quantity * self.unit_member_price_rappen
        self.total_supplier_price_rappen = self.quantity * self.unit_supplier_price_rappen
        self.total_profit_rappen = self.total_member_price_rappen - self.total_supplier_price_rappen
    
    def set_prices_from_variant(self):
        """Set prices from the associated variant"""
        if self.variant:
            self.unit_member_price_rappen = self.variant.member_price_rappen
            self.unit_supplier_price_rappen = self.variant.supplier_price_rappen
            self.calculate_totals()

