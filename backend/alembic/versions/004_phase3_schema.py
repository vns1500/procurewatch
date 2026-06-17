"""Phase 3 schema: users table, report enhancements, alert enhancements.

Revision ID: 004
Revises: 003
Create Date: 2026-06-16 00:00:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR NOT NULL,
            plan VARCHAR DEFAULT 'free',
            reports_used_this_month INTEGER DEFAULT 0,
            stripe_customer_id VARCHAR,
            api_key VARCHAR NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_api_key ON users (api_key)")

    # reports table enhancements
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS report_type VARCHAR(20) DEFAULT 'quick'")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS title TEXT")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20)")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS raw_markdown TEXT")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")

    # alerts table enhancements
    op.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS last_triggered TIMESTAMPTZ")
    op.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS trigger_count INTEGER DEFAULT 0")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS report_type")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS title")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS risk_level")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS raw_markdown")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS last_triggered")
    op.execute("ALTER TABLE alerts DROP COLUMN IF EXISTS trigger_count")
