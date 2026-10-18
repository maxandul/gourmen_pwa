"""Durable local deletion intent; no existing documents or Drive changes."""
from alembic import op
import sqlalchemy as sa
revision = 'r04c320261018'
down_revision = 'r04c120261018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('document_deletion_requests',
        sa.Column('drive_file_id',sa.String(100),primary_key=True),
        sa.Column('document_id',sa.Integer(),nullable=False),
        sa.Column('actor_id',sa.Integer(),sa.ForeignKey('members.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('filename',sa.String(255),nullable=False),
        sa.Column('reason',sa.String(500),nullable=False),
        sa.Column('requested_at',sa.DateTime(),nullable=False),
        sa.Column('completed_at',sa.DateTime(),nullable=True),
        sa.Column('status',sa.String(32),nullable=False))


def downgrade():
    op.drop_table('document_deletion_requests')
