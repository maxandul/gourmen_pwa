"""Personal display preferences never imply a private payment."""
from alembic import op
import sqlalchemy as sa

revision = 'u30120261021'
down_revision = 'u217c1b120261018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('member_claims', sa.Column('private_reminder_hidden', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('member_claims', sa.Column('private_reminder_changed', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('member_claims', sa.Column('private_reminder_version', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM member_claims WHERE private_reminder_hidden = true OR private_reminder_changed = true OR private_reminder_version <> 0')).scalar():
        raise RuntimeError('Private reminder preferences exist; downgrade refused')
    with op.batch_alter_table('member_claims') as batch:
        batch.drop_column('private_reminder_version')
        batch.drop_column('private_reminder_changed')
        batch.drop_column('private_reminder_hidden')
