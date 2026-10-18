"""Unique normalized primary addresses; reject collisions without rewriting accounts."""
from alembic import op
import sqlalchemy as sa
revision = 'r05b20261018'
down_revision = 'r04c320261018'
branch_labels = None
depends_on = None
TRIM_CHARS = ' \t\r\n\v\f'


def upgrade():
    members = sa.table('members',sa.column('email',sa.String()))
    normalized = sa.func.lower(sa.func.trim(members.c.email,TRIM_CHARS))
    collisions = op.get_bind().execute(sa.select(sa.func.count()).select_from(
        sa.select(normalized).group_by(normalized).having(sa.func.count()>1).subquery())).scalar()
    if collisions:
        raise RuntimeError('Primary email normalization conflicts: reconcile explicitly before migration; no accounts changed.')
    op.create_index('uq_members_primary_email_normalized','members',
        [sa.func.lower(sa.func.trim(sa.column('email'),TRIM_CHARS))],unique=True)


def downgrade():
    op.drop_index('uq_members_primary_email_normalized',table_name='members')
