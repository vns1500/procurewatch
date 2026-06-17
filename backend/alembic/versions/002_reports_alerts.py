"""reports and alerts tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tender_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column("status", sa.String, default="generating"),
        sa.Column("sections", postgresql.JSONB, nullable=True),
        sa.Column("summary_preview", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("ministries", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("status", sa.String, default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("reports")
