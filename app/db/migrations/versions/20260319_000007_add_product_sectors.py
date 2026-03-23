"""add product_sectors junction table

Revision ID: 20260319_000007
Revises: 20260318_000006
Create Date: 2026-03-19 00:00:07
"""

from alembic import op
import sqlalchemy as sa

revision = "20260319_000007"
down_revision = "20260318_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_sectors",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["sector_id"], ["categories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("product_id", "sector_id"),
    )
    op.create_index(
        "ix_product_sectors_product_id", "product_sectors", ["product_id"]
    )
    op.create_index(
        "ix_product_sectors_sector_id", "product_sectors", ["sector_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_product_sectors_sector_id", table_name="product_sectors")
    op.drop_index("ix_product_sectors_product_id", table_name="product_sectors")
    op.drop_table("product_sectors")
