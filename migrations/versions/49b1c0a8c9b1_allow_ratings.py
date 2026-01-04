"""Add allow_ratings flag to events

Revision ID: 49b1c0a8c9b1
Revises: 
Create Date: 2025-01-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '49b1c0a8c9b1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('allow_ratings', sa.Boolean(), nullable=False, server_default=sa.true()))
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        op.alter_column('events', 'allow_ratings', server_default=None)


def downgrade():
    op.drop_column('events', 'allow_ratings')
