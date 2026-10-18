"""Keep correction-related outflows linked to the original claim."""
from alembic import op
import sqlalchemy as sa

revision = 'u217c1b120261018'
down_revision = 'u217c1a20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('claim_refund_payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('claim_id', sa.Integer(), sa.ForeignKey('member_claims.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('correction_id', sa.Integer(), sa.ForeignKey('billbro_corrections.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('allocation_id', sa.Integer(), sa.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True))
    op.create_index('ix_claim_refund_payments_claim_id', 'claim_refund_payments', ['claim_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM claim_refund_payments')).scalar():
        raise RuntimeError('Claim refund history exists; downgrade refused')
    op.drop_index('ix_claim_refund_payments_claim_id', table_name='claim_refund_payments')
    op.drop_table('claim_refund_payments')
