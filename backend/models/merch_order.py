from datetime import datetime
from enum import Enum
from backend.extensions import db


class MerchLegacyOrderStatus(Enum):
    BESTELLT = 'BESTELLT'
    WIRD_GELIEFERT = 'WIRD_GELIEFERT'
    GELIEFERT = 'GELIEFERT'


class MerchOrderLegacy(db.Model):
    """Alter Vereins-Merch-Shop; Phase 10: Tabelle `merch_orders_legacy`."""

    __tablename__ = 'merch_orders_legacy'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(
        db.Enum(MerchLegacyOrderStatus),
        default=MerchLegacyOrderStatus.BESTELLT,
        nullable=False,
    )
    total_member_price_rappen = db.Column(db.Integer, nullable=False)
    total_supplier_price_rappen = db.Column(db.Integer, nullable=False)
    total_profit_rappen = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)

    member = db.relationship('Member', backref='merch_orders')
    order_items = db.relationship(
        'MerchOrderItemLegacy',
        backref='order',
        cascade='all, delete-orphan',
    )

    def __repr__(self):
        return f'<MerchOrderLegacy {self.id}: {self.order_number} - {self.status.value}>'

    @property
    def total_member_price_chf(self):
        return self.total_member_price_rappen / 100

    @property
    def total_supplier_price_chf(self):
        return self.total_supplier_price_rappen / 100

    @property
    def total_profit_chf(self):
        return self.total_profit_rappen / 100

    @property
    def status_display(self):
        status_names = {
            MerchLegacyOrderStatus.BESTELLT: 'Offen',
            MerchLegacyOrderStatus.WIRD_GELIEFERT: 'Bestellt',
            MerchLegacyOrderStatus.GELIEFERT: 'Geliefert',
        }
        return status_names.get(self.status, self.status.value)

    @property
    def is_delivered(self):
        return self.status == MerchLegacyOrderStatus.GELIEFERT

    @property
    def is_in_progress(self):
        return self.status == MerchLegacyOrderStatus.WIRD_GELIEFERT

    @property
    def is_pending(self):
        return self.status == MerchLegacyOrderStatus.BESTELLT

    def calculate_totals(self):
        self.total_member_price_rappen = sum(
            item.total_member_price_rappen for item in self.order_items
        )
        self.total_supplier_price_rappen = sum(
            item.total_supplier_price_rappen for item in self.order_items
        )
        self.total_profit_rappen = sum(
            item.total_profit_rappen for item in self.order_items
        )

    def get_item_count(self):
        return sum(item.quantity for item in self.order_items)

    def get_unique_articles_count(self):
        return len({item.article_id for item in self.order_items})

    @staticmethod
    def generate_order_number():
        import uuid

        return (
            f'MERCH-{datetime.now().strftime("%Y%m%d")}-'
            f'{str(uuid.uuid4())[:8].upper()}'
        )
