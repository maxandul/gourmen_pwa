from datetime import datetime
from backend.extensions import db


class MerchVariantLegacy(db.Model):
    """Alter Vereins-Merch-Shop; Phase 10: Tabelle `merch_variants_legacy`."""

    __tablename__ = 'merch_variants_legacy'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_articles_legacy.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    color = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    supplier_price_rappen = db.Column(db.Integer, nullable=False)
    member_price_rappen = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship('MerchOrderItemLegacy', backref='variant')

    def __repr__(self):
        return f'<MerchVariantLegacy {self.id}: {self.article.name} {self.color} {self.size}>'

    @property
    def supplier_price_chf(self):
        return self.supplier_price_rappen / 100

    @property
    def member_price_chf(self):
        return self.member_price_rappen / 100

    @property
    def profit_rappen(self):
        return self.member_price_rappen - self.supplier_price_rappen

    @property
    def profit_chf(self):
        return self.profit_rappen / 100

    @property
    def display_name(self):
        return f'{self.article.name} {self.color} {self.size}'

    def get_available_colors(self):
        return db.session.query(MerchVariantLegacy.color).filter_by(
            article_id=self.article_id,
            is_active=True,
        ).distinct().all()

    def get_available_sizes(self):
        return db.session.query(MerchVariantLegacy.size).filter_by(
            article_id=self.article_id,
            color=self.color,
            is_active=True,
        ).distinct().all()
