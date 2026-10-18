"""Add allocation journal without interpreting existing payments."""
from alembic import op
import sqlalchemy as sa

revision = 'u202b220261018'
down_revision = 'r05b20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('bank_transactions', sa.Column('allocation_version', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('bank_payment_allocations',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('bank_transaction_id',sa.Integer(),sa.ForeignKey('bank_transactions.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),
        sa.Column('position',sa.Integer(),nullable=False,server_default='0'),
        sa.Column('kind',sa.String(16),nullable=False),
        sa.Column('amount_rappen',sa.Integer(),nullable=False),
        sa.Column('claim_id',sa.Integer(),sa.ForeignKey('member_claims.id',ondelete='RESTRICT')),
        sa.Column('booking_id',sa.Integer(),sa.ForeignKey('bookings.id',ondelete='RESTRICT'),unique=True),
        sa.Column('member_id',sa.Integer(),sa.ForeignKey('members.id',ondelete='RESTRICT')),
        sa.Column('created_by',sa.Integer(),sa.ForeignKey('members.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('created_at',sa.DateTime(),nullable=False),
        sa.CheckConstraint('amount_rappen > 0',name='ck_payment_allocation_positive'),
        sa.CheckConstraint("kind IN ('claim','booking','rounding','refund')",name='ck_payment_allocation_kind'),
        sa.CheckConstraint("(kind = 'refund' AND booking_id IS NULL) OR (kind != 'refund' AND booking_id IS NOT NULL)",name='ck_payment_allocation_booking'),
        sa.UniqueConstraint('bank_transaction_id','version','position',name='uq_payment_allocation_step'))
    op.create_index('ix_payment_allocations_transaction','bank_payment_allocations',['bank_transaction_id'])


def downgrade():
    # Never silently discard a used allocation journal.
    if op.get_bind().execute(sa.text('SELECT count(*) FROM bank_payment_allocations')).scalar():
        raise RuntimeError('Payment allocation journal is not empty; downgrade refused')
    op.drop_index('ix_payment_allocations_transaction',table_name='bank_payment_allocations')
    op.drop_table('bank_payment_allocations')
    op.drop_column('bank_transactions','allocation_version')
