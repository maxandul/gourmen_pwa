"""Explicit Drive item classification; existing items remain unclassified."""
from alembic import op
import sqlalchemy as sa
revision = 'r04c120261018'
down_revision = 'r04b120261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('document_policies',
        sa.Column('drive_id', sa.String(100), primary_key=True),
        sa.Column('is_folder', sa.Boolean(), nullable=False),
        sa.Column('access_level', sa.String(32), nullable=False),
        sa.Column('maintenance_scope', sa.String(64), nullable=False))
    op.create_table('document_policy_changes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('drive_id', sa.String(100), nullable=False),
        sa.Column('actor_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=False))
    op.create_index('ix_document_policy_changes_drive_id', 'document_policy_changes', ['drive_id'])


def downgrade():
    op.drop_table('document_policy_changes')
    op.drop_table('document_policies')
