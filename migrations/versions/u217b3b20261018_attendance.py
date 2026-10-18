"""Separate actual BillBro attendance from the original RSVP."""
from alembic import op
import sqlalchemy as sa

revision = 'u217b3b20261018'
down_revision = 'u217b220261018'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('participations') as batch:
        batch.alter_column('teilnahme', existing_type=sa.Boolean(), nullable=True)
        batch.add_column(sa.Column('billbro_attendance', sa.Boolean(), nullable=True))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM participations WHERE teilnahme IS NULL OR billbro_attendance IS NOT NULL')).scalar():
        raise RuntimeError('Attendance or unanswered RSVP history exists; downgrade refused')
    with op.batch_alter_table('participations') as batch:
        batch.drop_column('billbro_attendance')
        batch.alter_column('teilnahme', existing_type=sa.Boolean(), nullable=False)
