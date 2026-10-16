"""Add immutable onboarding snapshots and per-attempt delivery state."""
from alembic import op
import sqlalchemy as sa

revision = 'a13920261016'
down_revision = 'f120261016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('auth_tokens', sa.Column('recipient_email', sa.String(254), nullable=True))
    op.add_column('auth_tokens', sa.Column('issued_generation', sa.String(32), nullable=True))
    op.add_column('auth_tokens', sa.Column('delivery_status', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('auth_tokens', 'delivery_status')
    op.drop_column('auth_tokens', 'issued_generation')
    op.drop_column('auth_tokens', 'recipient_email')
