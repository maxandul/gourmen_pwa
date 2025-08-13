"""Add event detail fields

Revision ID: 5c8e2b9f3a12
Revises: 4b01776b2e01
Create Date: 2024-12-19 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c8e2b9f3a12'
down_revision = '4b01776b2e01'
branch_labels = None
depends_on = None


def upgrade():
    # Add new event detail fields
    op.add_column('events', sa.Column('website', sa.String(length=200), nullable=True))
    op.add_column('events', sa.Column('notizen', sa.Text(), nullable=True))


def downgrade():
    # Remove event detail fields
    op.drop_column('events', 'notizen')
    op.drop_column('events', 'website')
