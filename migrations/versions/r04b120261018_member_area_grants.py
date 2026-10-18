"""Add scoped member grants; no existing permissions or rows are changed."""
from alembic import op
import sqlalchemy as sa
revision = 'r04b120261018'
down_revision = 'a13920261016'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('member_area_grants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('scope', sa.String(64), nullable=False),
        sa.Column('granted_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_by', sa.Integer(), sa.ForeignKey('members.id', ondelete='RESTRICT')),
        sa.Column('revoked_at', sa.DateTime()))
    op.create_index('ix_member_area_grants_member_id','member_area_grants',['member_id'])
    op.create_index('uq_member_area_grant_active','member_area_grants',['member_id','scope'],unique=True,
                    sqlite_where=sa.text('revoked_at IS NULL'),postgresql_where=sa.text('revoked_at IS NULL'))


def downgrade():
    op.drop_table('member_area_grants')
