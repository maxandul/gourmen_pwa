"""add auth_tokens table

Revision ID: 6f9a2d1c4b7e
Revises: 7550d61228f7
Create Date: 2026-04-27 11:52:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f9a2d1c4b7e"
down_revision = "7550d61228f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum(
                "PASSWORD_RESET",
                "MFA_RESET",
                "ONBOARDING",
                "MAGIC_LINK",
                name="authtokenpurpose",
            ),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("request_ip", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_tokens_member_id", "auth_tokens", ["member_id"], unique=False)
    op.create_index("ix_auth_tokens_token_hash", "auth_tokens", ["token_hash"], unique=True)
    op.create_index("ix_auth_tokens_purpose", "auth_tokens", ["purpose"], unique=False)
    op.create_index("ix_auth_tokens_expires_at", "auth_tokens", ["expires_at"], unique=False)
    op.create_index(
        "ix_auth_tokens_member_purpose_used_at",
        "auth_tokens",
        ["member_id", "purpose", "used_at"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_auth_tokens_member_purpose_used_at", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_expires_at", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_purpose", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_token_hash", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_member_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    sa.Enum(name="authtokenpurpose").drop(op.get_bind(), checkfirst=True)
