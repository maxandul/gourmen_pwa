"""Keep paid-club correction drafts without changing the effective settlement."""
from alembic import op
import sqlalchemy as sa

revision = 'u217c1a20261018'
down_revision = 'u217b3b20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('billbro_correction_drafts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('before_json', sa.JSON(), nullable=False),
        sa.Column('proposal_json', sa.JSON(), nullable=False),
        sa.Column('preview_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('status_reason', sa.String(1000)),
        sa.Column('status_actor_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT')),
        sa.Column('status_at', sa.DateTime()),
        sa.CheckConstraint("status IN ('pending','superseded','withdrawn','applied')", name='ck_billbro_draft_status'))
    op.create_index('ix_billbro_drafts_event', 'billbro_correction_drafts', ['event_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM billbro_correction_drafts')).scalar():
        raise RuntimeError('BillBro draft history exists; downgrade refused')
    op.drop_index('ix_billbro_drafts_event', table_name='billbro_correction_drafts')
    op.drop_table('billbro_correction_drafts')
