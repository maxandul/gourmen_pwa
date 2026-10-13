"""Add server-side authentication generation; legacy cookies require login."""
from alembic import op
import sqlalchemy as sa

revision = 'a07720261013'
down_revision = 'a08920261012'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('members', sa.Column('auth_generation', sa.String(32),
                                     nullable=False, server_default='0'))


def downgrade():
    op.drop_column('members', 'auth_generation')
