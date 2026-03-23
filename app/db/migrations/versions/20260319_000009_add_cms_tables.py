"""add cms tables: site_content, media_files, publish_logs

Revision ID: 20260319_000009
Revises: 20260319_000008
Create Date: 2026-03-19 00:00:09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260319_000009"
down_revision = "20260319_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())

    if "site_content" not in existing:
        op.create_table(
            "site_content",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("key", sa.String(128), nullable=False),
            sa.Column("value", JSONB(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_site_content_key", "site_content", ["key"], unique=True)

    if "media_files" not in existing:
        op.create_table(
            "media_files",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("filename", sa.String(512), nullable=False),
            sa.Column("original_name", sa.String(512), nullable=False),
            sa.Column("mime_type", sa.String(128), nullable=False),
            sa.Column("size", sa.Integer(), nullable=False),
            sa.Column("width", sa.Integer(), nullable=True),
            sa.Column("height", sa.Integer(), nullable=True),
            sa.Column("storage_path", sa.String(1024), nullable=False),
            sa.Column("public_url", sa.String(1024), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_media_files_filename", "media_files", ["filename"], unique=True)
        op.create_index("ix_media_files_created_at", "media_files", ["created_at"])

    if "publish_logs" not in existing:
        op.create_table(
            "publish_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("message", sa.Text(), nullable=False, server_default=""),
            sa.Column("files_uploaded", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_publish_logs_created_at", "publish_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_publish_logs_created_at", table_name="publish_logs")
    op.drop_table("publish_logs")
    op.drop_index("ix_media_files_created_at", table_name="media_files")
    op.drop_index("ix_media_files_filename", table_name="media_files")
    op.drop_table("media_files")
    op.drop_index("ix_site_content_key", table_name="site_content")
    op.drop_table("site_content")
