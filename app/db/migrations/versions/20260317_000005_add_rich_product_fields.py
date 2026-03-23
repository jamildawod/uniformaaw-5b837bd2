"""add rich product fields

Revision ID: 20260317_000005
Revises: 20260312_000004
Create Date: 2026-03-17 00:00:05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260317_000005"
down_revision = "20260312_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("material", sa.String(length=255), nullable=True))
    op.add_column(
        "products",
        sa.Column("care_instructions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("products", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "products",
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("products", sa.Column("qr_code", sa.String(length=1024), nullable=True))
    op.add_column(
        "products",
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "attributes")
    op.drop_column("products", "qr_code")
    op.drop_column("products", "certifications")
    op.drop_column("products", "tags")
    op.drop_column("products", "care_instructions")
    op.drop_column("products", "material")
