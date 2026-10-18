"""Record explicitly confirmed surplus income, without fabricating an outgoing payment."""
from alembic import op
import sqlalchemy as sa

revision = 'u202c2a20261018'
down_revision = 'u202c120261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bank_refund_confirmations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('allocation_id', sa.Integer(), sa.ForeignKey('bank_payment_allocations.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('booking_id', sa.Integer(), sa.ForeignKey('bookings.id', ondelete='RESTRICT'), nullable=False, unique=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM bank_refund_confirmations')).scalar():
        raise RuntimeError('Refund confirmation history exists; downgrade refused')
    op.drop_table('bank_refund_confirmations')
