"""Retain links between incoming surplus and actual outgoing allocations."""
from alembic import op
import sqlalchemy as sa

revision = 'u202c2b20261018'
down_revision = 'u202c2a20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bank_refund_payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('confirmation_id', sa.Integer(), sa.ForeignKey('bank_refund_confirmations.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('allocation_id', sa.Integer(), sa.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True))
    op.create_index('ix_bank_refund_payments_confirmation_id', 'bank_refund_payments', ['confirmation_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM bank_refund_payments')).scalar():
        raise RuntimeError('Refund payment history exists; downgrade refused')
    op.drop_table('bank_refund_payments')
