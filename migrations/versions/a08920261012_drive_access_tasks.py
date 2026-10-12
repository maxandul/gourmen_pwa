"""Durable Drive access tasks; additive, no external calls or backfill."""
from alembic import op
import sqlalchemy as sa

revision = 'a08920261012'
down_revision = 'a4b7c2d9e015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'drive_access_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('member_id', sa.Integer(),
                  sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('email', sa.String(254), nullable=False),
        sa.Column('drive_id', sa.String(100)),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('error_code', sa.String(40)),
        sa.Column('last_attempt_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime()),
        sa.CheckConstraint("action IN ('revoke', 'invite')", name='ck_drive_access_action'),
        sa.CheckConstraint("status IN ('pending', 'failed', 'done', 'cancelled')",
                           name='ck_drive_access_status'),
    )
    op.create_index('ix_drive_access_member_status', 'drive_access_tasks', ['member_id', 'status'])


def downgrade():
    op.drop_index('ix_drive_access_member_status', table_name='drive_access_tasks')
    op.drop_table('drive_access_tasks')
