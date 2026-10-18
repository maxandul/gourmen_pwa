"""Retain before/after evidence for explicitly confirmed BillBro corrections."""
from alembic import op
import sqlalchemy as sa

revision = 'u217b120261018'
down_revision = 'u21420261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('billbro_corrections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reason', sa.String(1000), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('before_json', sa.JSON(), nullable=False),
        sa.Column('after_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_index('ix_billbro_corrections_event_id', 'billbro_corrections', ['event_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM billbro_corrections')).scalar():
        raise RuntimeError('BillBro correction history exists; downgrade refused')
    op.drop_index('ix_billbro_corrections_event_id', table_name='billbro_corrections')
    op.drop_table('billbro_corrections')
