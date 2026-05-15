from datetime import datetime
from backend.extensions import db


class MerchOrderItemLegacy(db.Model):
    """Alter Vereins-Merch-Shop; Phase 10: Tabelle `merch_order_items_legacy`."""

    __tablename__ = 'merch_order_items_legacy'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_orders_legacy.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_articles_legacy.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_variants_legacy.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_member_price_rappen = db.Column(db.Integer, nullable=False)
    unit_supplier_price_rappen = db.Column(db.Integer, nullable=False)
    total_member_price_rappen = db.Column(db.Integer, nullable=False)
    total_supplier_price_rappen = db.Column(db.Integer, nullable=False)
    total_profit_rappen = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f'<MerchOrderItemLegacy {self.id}: {self.quantity}x '
            f'{self.article.name} {self.variant.color} {self.variant.size}>'
        )

    @property
    def unit_member_price_chf(self):
        return self.unit_member_price_rappen / 100

    @property
    def unit_supplier_price_chf(self):
        return self.unit_supplier_price_rappen / 100

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
    def display_name(self):
        return f'{self.article.name} {self.variant.color} {self.variant.size}'

    def calculate_totals(self):
        self.total_member_price_rappen = (
            self.quantity * self.unit_member_price_rappen
        )
        self.total_supplier_price_rappen = (
            self.quantity * self.unit_supplier_price_rappen
        )
        self.total_profit_rappen = (
            self.total_member_price_rappen - self.total_supplier_price_rappen
        )

    def set_prices_from_variant(self):
        if self.variant:
            self.unit_member_price_rappen = self.variant.member_price_rappen
            self.unit_supplier_price_rappen = self.variant.supplier_price_rappen
            self.calculate_totals()
