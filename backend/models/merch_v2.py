"""Merch v2 (Phase 10): neue Tabellen nach Migration `a9c81e2d4f03`.

Legacy bleibt in merch_article / merch_variant / merch_order / merch_order_item.
Specs: docs/capabilities/merch.md Sektion 6.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import UniqueConstraint, event

from backend.extensions import db


class MerchRoundStatus(Enum):
    DRAFT = 'DRAFT'
    OPEN = 'OPEN'
    LOCKED = 'LOCKED'
    ORDERED_AT_SUPPLIER = 'ORDERED_AT_SUPPLIER'
    DELIVERED = 'DELIVERED'
    CLOSED = 'CLOSED'
    CANCELLED = 'CANCELLED'


class MerchOrderStatus(Enum):
    DRAFT = 'DRAFT'
    CONFIRMED = 'CONFIRMED'
    INVOICED = 'INVOICED'
    PICKED_UP = 'PICKED_UP'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class MerchColor(db.Model):
    __tablename__ = 'merch_colors'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    label = db.Column(db.String(160), nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship('MerchVariant', back_populates='color')


class MerchSize(db.Model):
    __tablename__ = 'merch_sizes'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    label = db.Column(db.String(160), nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship('MerchVariant', back_populates='size')


class MerchSupplier(db.Model):
    __tablename__ = 'merch_suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(200))
    website_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    articles = db.relationship('MerchArticle', back_populates='supplier')


class MerchArticle(db.Model):
    __tablename__ = 'merch_articles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_suppliers.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    list_price_rappen = db.Column(db.Integer, nullable=False)
    image_drive_file_id = db.Column(db.String(200))
    variant_schema = db.Column(db.JSON)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('MerchSupplier', back_populates='articles')
    variants = db.relationship(
        'MerchVariant',
        back_populates='article',
        cascade='all, delete-orphan',
    )


class MerchVariant(db.Model):
    __tablename__ = 'merch_variants'
    __table_args__ = (
        UniqueConstraint(
            'article_id',
            'variant_key',
            name='uq_nv2_merch_variants_article_variant_key',
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_articles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    color_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_colors.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
    )
    size_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_sizes.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
    )
    variant_key = db.Column(db.String(128), nullable=False)
    attributes = db.Column(db.JSON, nullable=False)
    list_price_rappen = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    article = db.relationship('MerchArticle', back_populates='variants')
    color = db.relationship('MerchColor', back_populates='variants')
    size = db.relationship('MerchSize', back_populates='variants')


class MerchRound(db.Model):
    __tablename__ = 'merch_rounds'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(
        db.Enum(
            MerchRoundStatus,
            name='merchroundstatus',
            values_callable=_enum_values,
        ),
        default=MerchRoundStatus.DRAFT,
        nullable=False,
        index=True,
    )
    deadline_communicated = db.Column(db.Date)
    subsidy_per_member_rappen = db.Column(db.Integer, default=0, nullable=False)
    supplier_invoice_drive_file_id = db.Column(db.String(200))
    supplier_invoice_total_rappen = db.Column(db.Integer)
    supplier_invoice_completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    marketing_chief_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )

    opened_at = db.Column(db.DateTime)
    locked_at = db.Column(db.DateTime)
    ordered_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    marketing_chief = db.relationship(
        'Member',
        foreign_keys=[marketing_chief_id],
    )
    round_items = db.relationship(
        'MerchRoundItem',
        back_populates='round',
        cascade='all, delete-orphan',
    )
    orders = db.relationship(
        'MerchOrder',
        back_populates='round',
        cascade='all, delete-orphan',
    )


class MerchRoundItem(db.Model):
    __tablename__ = 'merch_round_items'
    __table_args__ = (
        UniqueConstraint('round_id', 'variant_id', name='uq_round_variant'),
    )

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_rounds.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    variant_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_variants.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    list_price_snapshot_rappen = db.Column(db.Integer, nullable=False)
    effective_supplier_price_rappen = db.Column(db.Integer)
    member_price_rappen = db.Column(db.Integer)

    round = db.relationship('MerchRound', back_populates='round_items')
    variant = db.relationship('MerchVariant')


class MerchOrder(db.Model):
    __tablename__ = 'merch_orders'
    __table_args__ = (
        UniqueConstraint('round_id', 'member_id', name='uq_round_member'),
    )

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_rounds.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    member_id = db.Column(
        db.Integer,
        db.ForeignKey('members.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(
            MerchOrderStatus,
            name='merchorderv2status',
            values_callable=_enum_values,
        ),
        default=MerchOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )

    gross_amount_rappen = db.Column(db.Integer)
    subsidy_amount_rappen = db.Column(db.Integer)
    member_amount_due_rappen = db.Column(db.Integer)

    confirmed_at = db.Column(db.DateTime)
    invoiced_at = db.Column(db.DateTime)
    picked_up_at = db.Column(db.DateTime)
    picked_up_by_member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    paid_at = db.Column(db.DateTime)
    paid_by_member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    round = db.relationship('MerchRound', back_populates='orders')
    member = db.relationship(
        'Member',
        foreign_keys=[member_id],
        backref=db.backref('merch_v2_orders', lazy='dynamic'),
    )
    picked_up_by_member = db.relationship(
        'Member',
        foreign_keys=[picked_up_by_member_id],
    )
    paid_by_member = db.relationship(
        'Member',
        foreign_keys=[paid_by_member_id],
    )
    order_items = db.relationship(
        'MerchOrderItem',
        back_populates='order',
        cascade='all, delete-orphan',
    )


class MerchOrderItem(db.Model):
    __tablename__ = 'merch_order_items'
    __table_args__ = (
        UniqueConstraint('order_id', 'round_item_id', name='uq_order_round_item'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    round_item_id = db.Column(
        db.Integer,
        db.ForeignKey('merch_round_items.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_at_confirm_rappen = db.Column(db.Integer, nullable=False)
    unit_price_final_rappen = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship('MerchOrder', back_populates='order_items')
    round_item = db.relationship('MerchRoundItem')


def _merch_variant_ensure_variant_key_before_insert(mapper, connection, target):
    """Tests/Seed ohne expliziten `variant_key` — Fallback aus FKs/attributes."""
    if getattr(target, 'variant_key', None):
        return
    from backend.utils.merch_variant_key import compute_merch_variant_key

    target.variant_key = compute_merch_variant_key(
        color_id=getattr(target, 'color_id', None),
        size_id=getattr(target, 'size_id', None),
        attributes=getattr(target, 'attributes', None) or {},
    )[:126]


event.listen(MerchVariant, 'before_insert', _merch_variant_ensure_variant_key_before_insert)
