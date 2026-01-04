from datetime import datetime
from enum import Enum
from backend.extensions import db

class OrderStatus(Enum):
    BESTELLT = 'BESTELLT'
    WIRD_GELIEFERT = 'WIRD_GELIEFERT'
    GELIEFERT = 'GELIEFERT'

class MerchOrder(db.Model):
    """Merch order model - customer orders"""
    __tablename__ = 'merch_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id', ondelete='RESTRICT'), 
                         nullable=False, index=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.BESTELLT, nullable=False)
    total_member_price_rappen = db.Column(db.Integer, nullable=False)  # Total price for member
    total_supplier_price_rappen = db.Column(db.Integer, nullable=False)  # Total price for supplier
    total_profit_rappen = db.Column(db.Integer, nullable=False)  # Total profit for association
    notes = db.Column(db.Text)  # Order notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)  # When order was delivered
    
    # Relationships
    member = db.relationship('Member', backref='merch_orders')
    order_items = db.relationship('MerchOrderItem', backref='order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MerchOrder {self.id}: {self.order_number} - {self.status.value}>'
    
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
    def status_display(self):
        """Get display name for status"""
        status_names = {
            OrderStatus.BESTELLT: 'Offen',
            OrderStatus.WIRD_GELIEFERT: 'Bestellt',
            OrderStatus.GELIEFERT: 'Geliefert'
        }
        return status_names.get(self.status, self.status.value)
    
    @property
    def is_delivered(self):
        """Check if order is delivered"""
        return self.status == OrderStatus.GELIEFERT
    
    @property
    def is_in_progress(self):
        """Check if order is in progress"""
        return self.status == OrderStatus.WIRD_GELIEFERT
    
    @property
    def is_pending(self):
        """Check if order is pending"""
        return self.status == OrderStatus.BESTELLT
    
    def calculate_totals(self):
        """Calculate totals from order items"""
        self.total_member_price_rappen = sum(item.total_member_price_rappen for item in self.order_items)
        self.total_supplier_price_rappen = sum(item.total_supplier_price_rappen for item in self.order_items)
        self.total_profit_rappen = sum(item.total_profit_rappen for item in self.order_items)
    
    def get_item_count(self):
        """Get total number of items in this order"""
        return sum(item.quantity for item in self.order_items)
    
    def get_unique_articles_count(self):
        """Get number of unique articles in this order"""
        return len(set(item.article_id for item in self.order_items))
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        import uuid
        return f"MERCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

