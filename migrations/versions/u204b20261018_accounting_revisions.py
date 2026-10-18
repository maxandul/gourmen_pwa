"""Retain review versions without reconstructing historical snapshots."""
from alembic import op
import sqlalchemy as sa

revision = 'u204b20261018'
down_revision = 'u203b20261018'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('fiscal_years', sa.Column('review_version', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('accounting_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fiscal_year_id', sa.Integer(), sa.ForeignKey('fiscal_years.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON()),
        sa.Column('submitted_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT')),
        sa.Column('reviewer_name', sa.String(255)),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('admin_substitute', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('report_drive_id', sa.String(255)),
        sa.Column('withdrawn_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT')),
        sa.Column('withdrawn_at', sa.DateTime()),
        sa.Column('withdrawal_reason', sa.Text()),
        sa.UniqueConstraint('fiscal_year_id', 'version', name='uq_revision_year_version'))
    with op.batch_alter_table('revision_comments') as batch:
        batch.add_column(sa.Column('revision_id', sa.Integer()))
        batch.add_column(sa.Column('blocking', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column('resolved_by', sa.Integer()))
        batch.add_column(sa.Column('resolved_at', sa.DateTime()))
        batch.create_foreign_key('fk_comment_revision', 'accounting_revisions', ['revision_id'], ['id'], ondelete='RESTRICT')
        batch.create_foreign_key('fk_comment_resolver', 'members', ['resolved_by'], ['id'], ondelete='RESTRICT')


def downgrade():
    if op.get_bind().execute(sa.text('SELECT count(*) FROM accounting_revisions')).scalar():
        raise RuntimeError('Review history exists; downgrade refused')
    if op.get_bind().execute(sa.text('SELECT count(*) FROM revision_comments WHERE blocking = true OR resolved_at IS NOT NULL')).scalar():
        raise RuntimeError('Review annotations exist; downgrade refused')
    with op.batch_alter_table('revision_comments') as batch:
        batch.drop_constraint('fk_comment_resolver', type_='foreignkey')
        batch.drop_constraint('fk_comment_revision', type_='foreignkey')
        for column in ('resolved_at', 'resolved_by', 'blocking', 'revision_id'):
            batch.drop_column(column)
    op.drop_table('accounting_revisions')
    op.drop_column('fiscal_years', 'review_version')
