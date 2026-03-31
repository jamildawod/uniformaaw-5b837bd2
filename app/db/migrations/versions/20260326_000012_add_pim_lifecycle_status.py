"""Add PIM lifecycle status table for super deal filtering.

Revision ID: 20260326_000012
Revises: 20260326_000011
Create Date: 2026-03-26 00:00:12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_000012"
down_revision = "20260326_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pim_lifecycle_status",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_no", sa.String(length=128), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("source_file_name", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_pim_lifecycle_status_item_no",
        "pim_lifecycle_status",
        ["item_no"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_pim_lifecycle_status_item_no", table_name="pim_lifecycle_status")
    op.drop_table("pim_lifecycle_status")
