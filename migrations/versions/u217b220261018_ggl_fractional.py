"""Keep fractional GGL results and tolerate the legacy missing points column."""
from alembic import op
import sqlalchemy as sa

revision = 'u217b220261018'
down_revision = 'u217b120261018'
branch_labels = None
depends_on = None


def upgrade():
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('participations')}
    with op.batch_alter_table('participations') as batch:
        batch.alter_column('rank', existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=True)
        if 'points' in columns:
            batch.alter_column('points', existing_type=sa.Integer(), type_=sa.Float(), existing_nullable=True)
        else:
            batch.add_column(sa.Column('points', sa.Float(), nullable=True))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM participations WHERE rank != CAST(rank AS INTEGER) OR points != CAST(points AS INTEGER)')).scalar():
        raise RuntimeError('Fractional GGL history exists; downgrade refused')
    # Retain points: the preceding application already uses this legacy column.
    with op.batch_alter_table('participations') as batch:
        batch.alter_column('rank', existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=True)
        batch.alter_column('points', existing_type=sa.Float(), type_=sa.Integer(), existing_nullable=True)
