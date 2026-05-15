from datetime import datetime
from backend.extensions import db


class MerchArticleLegacy(db.Model):
    """Alter Vereins-Merch-Shop; Phase 10: Tabelle `merch_articles_legacy`."""

    __tablename__ = 'merch_articles_legacy'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    base_supplier_price_rappen = db.Column(db.Integer, nullable=False)
    base_member_price_rappen = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship(
        'MerchVariantLegacy',
        backref='article',
        cascade='all, delete-orphan',
    )
    order_items = db.relationship('MerchOrderItemLegacy', backref='article')

    def __repr__(self):
        return f'<MerchArticleLegacy {self.id}: {self.name}>'

    @property
    def base_supplier_price_chf(self):
        return self.base_supplier_price_rappen / 100

    @property
    def base_member_price_chf(self):
        return self.base_member_price_rappen / 100

    @property
    def base_profit_rappen(self):
        return self.base_member_price_rappen - self.base_supplier_price_rappen

    @property
    def base_profit_chf(self):
        return self.base_profit_rappen / 100

    def get_active_variants(self):
        return MerchVariantLegacy.query.filter_by(
            article_id=self.id, is_active=True
        ).all()

    def get_variant_by_color_size(self, color, size):
        return MerchVariantLegacy.query.filter_by(
            article_id=self.id,
            color=color,
            size=size,
            is_active=True,
        ).first()
