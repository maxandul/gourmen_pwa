"""Retain order descriptions without inventing historical originals."""
from alembic import op
import sqlalchemy as sa

revision = 'u21420261018'
down_revision = 'u202c2b20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('merch_order_items', sa.Column('description_snapshot', sa.String(300), nullable=True))
    op.add_column('merch_order_items', sa.Column('description_snapshot_source', sa.String(20), nullable=True))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM merch_order_items WHERE description_snapshot IS NOT NULL OR description_snapshot_source IS NOT NULL')).scalar():
        raise RuntimeError('Order description history exists; downgrade refused')
    with op.batch_alter_table('merch_order_items') as batch:
        batch.drop_column('description_snapshot_source')
        batch.drop_column('description_snapshot')
