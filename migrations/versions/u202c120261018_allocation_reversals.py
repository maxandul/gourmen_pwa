"""Retain withdrawn allocations and bookings as historical evidence."""
from alembic import op
import sqlalchemy as sa

revision = 'u202c120261018'
down_revision = 'u204c220261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bank_allocation_reversals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bank_transaction_id', sa.Integer(), sa.ForeignKey('bank_transactions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('bank_transaction_id', 'version', name='uq_allocation_reversal_version'))
    for table in ('bookings', 'bank_payment_allocations'):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column('reversal_id', sa.Integer()))
            batch.create_foreign_key('fk_' + table + '_reversal', 'bank_allocation_reversals', ['reversal_id'], ['id'], ondelete='RESTRICT')


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM bank_allocation_reversals')).scalar():
        raise RuntimeError('Allocation reversal history exists; downgrade refused')
    for table in ('bank_payment_allocations', 'bookings'):
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint('fk_' + table + '_reversal', type_='foreignkey')
            batch.drop_column('reversal_id')
    op.drop_table('bank_allocation_reversals')
