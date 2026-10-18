"""Persist report content and idempotent Drive target before upload."""
from alembic import op
import sqlalchemy as sa

revision = 'u204c220261018'
down_revision = 'u204b20261018'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('accounting_revisions') as batch:
        batch.add_column(sa.Column('report_state', sa.String(20), nullable=False, server_default='pending'))
        batch.add_column(sa.Column('report_attempt', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('report_attempted_at', sa.DateTime()))
        batch.add_column(sa.Column('report_payload', sa.LargeBinary()))
        batch.add_column(sa.Column('report_reserved_id', sa.String(255)))
        batch.add_column(sa.Column('report_folder_id', sa.String(255)))
        batch.create_unique_constraint('uq_revision_report_reserved_id', ['report_reserved_id'])
    op.execute("UPDATE accounting_revisions SET report_state='complete' WHERE report_drive_id IS NOT NULL")


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM accounting_revisions WHERE report_attempt > 0 OR report_payload IS NOT NULL OR report_reserved_id IS NOT NULL')).scalar():
        raise RuntimeError('Report recovery data exists; downgrade refused')
    with op.batch_alter_table('accounting_revisions') as batch:
        batch.drop_constraint('uq_revision_report_reserved_id', type_='unique')
        for name in ('report_folder_id', 'report_reserved_id', 'report_payload', 'report_attempted_at', 'report_attempt', 'report_state'):
            batch.drop_column(name)
