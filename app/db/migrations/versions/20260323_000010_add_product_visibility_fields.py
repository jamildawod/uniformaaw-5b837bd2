"""Add product visibility fields: is_sales_blocked, lifecycle_status

These fields are mapped directly from PIM source data (IsSalesBlocked,
ProductLifeCycleStatus) and used for public product filtering in the repository.

Ingestion stays broad (imports all source rows) while public queries only
return products where is_sales_blocked = false.

Revision ID: 20260323_000010
Revises: 20260319_000009
Create Date: 2026-03-23 00:00:10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260323_000010"
down_revision = "20260319_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # is_sales_blocked: sourced from IsSalesBlocked in PIM CSV.
    # Default false so existing products remain visible until next sync.
    conn.execute(sa.text("""
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS is_sales_blocked BOOLEAN NOT NULL DEFAULT false
    """))

    # lifecycle_status: sourced from ProductLifeCycleStatus in PIM CSV.
    # Stored for visibility and future filtering. NULL = not yet synced.
    conn.execute(sa.text("""
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(64) NULL
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_products_is_sales_blocked
        ON products (is_sales_blocked)
    """))

    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_products_lifecycle_status
        ON products (lifecycle_status)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_products_lifecycle_status"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_products_is_sales_blocked"))
    conn.execute(sa.text("ALTER TABLE products DROP COLUMN IF EXISTS lifecycle_status"))
    conn.execute(sa.text("ALTER TABLE products DROP COLUMN IF EXISTS is_sales_blocked"))
