"""Add super deals storage table.

Revision ID: 20260326_000011
Revises: 20260323_000010
Create Date: 2026-03-26 00:00:11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_000011"
down_revision = "20260323_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "super_deals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.String(length=36), nullable=False),
    )
    op.create_index("ix_super_deals_product_id", "super_deals", ["product_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_super_deals_product_id", table_name="super_deals")
    op.drop_table("super_deals")
