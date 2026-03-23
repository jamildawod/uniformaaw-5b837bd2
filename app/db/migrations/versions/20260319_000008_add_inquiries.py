"""add inquiries table

Revision ID: 20260319_000008
Revises: 20260319_000007
Create Date: 2026-03-19 00:00:08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260319_000008"
down_revision = "20260319_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inquiries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("org_number", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_inquiries_created_at", "inquiries", ["created_at"])
    op.create_index("ix_inquiries_email", "inquiries", ["email"])


def downgrade() -> None:
    op.drop_index("ix_inquiries_email", table_name="inquiries")
    op.drop_index("ix_inquiries_created_at", table_name="inquiries")
    op.drop_table("inquiries")
