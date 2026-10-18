"""Record source-file identity without inferring legacy fingerprints."""
from alembic import op
import sqlalchemy as sa

revision='u203b20261018'
down_revision='u202b220261018'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('bank_statement_imports',sa.Column('source_fingerprint',sa.String(64)))
    op.create_index('ix_bank_import_source_fingerprint','bank_statement_imports',['source_fingerprint'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM bank_statement_imports WHERE source_fingerprint IS NOT NULL')).scalar():
        raise RuntimeError('Source fingerprints are in use; downgrade refused')
    op.drop_index('ix_bank_import_source_fingerprint',table_name='bank_statement_imports')
    op.drop_column('bank_statement_imports','source_fingerprint')
