"""Phase 2b schema additions: audit_findings, contracts, new columns on tenders/vendors.

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend vendors table
    op.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS cin TEXT")
    op.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS director_network_json JSONB DEFAULT '{}'")
    op.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS registration_date DATE")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendors_risk_level ON vendors (risk_level)")

    # Extend tenders table - source column
    op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'GEM'")

    # spec_embedding column using pgvector - must use raw DDL
    op.execute("ALTER TABLE tenders ADD COLUMN IF NOT EXISTS spec_embedding vector(1536)")
    # ivfflat index requires data; skip if table is empty, will be created lazily
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM tenders LIMIT 1) THEN "
        "CREATE INDEX IF NOT EXISTS ix_tenders_spec_embedding "
        "ON tenders USING ivfflat (spec_embedding vector_cosine_ops) WITH (lists = 50); "
        "END IF; "
        "END $$;"
    )

    # audit_findings table
    op.create_table(
        "audit_findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("ministry", sa.String(200), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=True),
        sa.Column("irregularity_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("tender_id", UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("raw_json", JSONB(), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_findings_ministry", "audit_findings", ["ministry"])
    op.create_index("ix_audit_findings_year", "audit_findings", ["year"])
    op.create_index("ix_audit_findings_type", "audit_findings", ["irregularity_type"])

    # contracts table
    op.create_table(
        "contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tender_id", UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_value", sa.BigInteger(), nullable=False),
        sa.Column("current_value", sa.BigInteger(), nullable=False),
        sa.Column("award_date", sa.Date(), nullable=False),
        sa.Column("amendments", JSONB(), nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contracts_tender_id", "contracts", ["tender_id"])
    op.create_index("ix_contracts_vendor_id", "contracts", ["vendor_id"])

    # price_benchmarks: add source column if not already present
    op.execute(
        "ALTER TABLE price_benchmarks ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'market_survey_2024'"
    )


def downgrade() -> None:
    op.drop_table("contracts")
    op.drop_table("audit_findings")
    op.execute("ALTER TABLE vendors DROP COLUMN IF EXISTS cin")
    op.execute("ALTER TABLE vendors DROP COLUMN IF EXISTS director_network_json")
    op.execute("ALTER TABLE vendors DROP COLUMN IF EXISTS registration_date")
    op.execute("DROP INDEX IF EXISTS ix_vendors_risk_level")
    op.execute("ALTER TABLE tenders DROP COLUMN IF EXISTS source")
    op.execute("ALTER TABLE tenders DROP COLUMN IF EXISTS spec_embedding")
    # source was pre-existing, leave it
