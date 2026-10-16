"""Record one-time consumption of member creation confirmations."""
from alembic import op
import sqlalchemy as sa

revision = 'f120261016'
down_revision = 'a07720261013'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'action_confirmation_uses',
        sa.Column('nonce_hash', sa.String(64), primary_key=True),
        sa.Column('used_at', sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table('action_confirmation_uses')
