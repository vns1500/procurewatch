"""initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("gstin", sa.String, unique=True, nullable=True),
        sa.Column("incorporation_date", sa.Date, nullable=True),
        sa.Column("state", sa.String, nullable=True),
        sa.Column("total_wins", sa.Integer, default=0),
        sa.Column("total_value", sa.BigInteger, default=0),
        sa.Column("win_rate", sa.Float, default=0.0),
        sa.Column("risk_level", sa.String, default="low"),
        sa.Column("mca_verified", sa.Boolean, default=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tenders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("gem_id", sa.String, unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("ministry", sa.String, nullable=False),
        sa.Column("state", sa.String, nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False),
        sa.Column("tender_date", sa.Date, nullable=False),
        sa.Column("close_date", sa.Date, nullable=False),
        sa.Column("winner_vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("bid_count", sa.Integer, default=1),
        sa.Column("risk_score", sa.Integer, default=0),
        sa.Column("anomaly_flags", postgresql.ARRAY(sa.String), default=[]),
        sa.Column("raw_json", postgresql.JSONB, nullable=True),
        sa.Column("spec_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenders_risk_score", "tenders", ["risk_score"])

    op.create_table(
        "anomalies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id"), nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("severity", sa.String, nullable=False),
        sa.Column("evidence", postgresql.JSONB, nullable=True),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String, default="open"),
    )
    op.create_index("ix_anomalies_type", "anomalies", ["type"])
    op.create_index("ix_anomalies_severity", "anomalies", ["severity"])

    op.create_table(
        "directors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("din", sa.String, unique=True, nullable=False),
        sa.Column("vendor_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
    )

    op.create_table(
        "price_benchmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("item_name", sa.Text, nullable=False),
        sa.Column("unit", sa.String, nullable=False),
        sa.Column("avg_price", sa.BigInteger, nullable=False),
        sa.Column("min_price", sa.BigInteger, nullable=False),
        sa.Column("max_price", sa.BigInteger, nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("price_benchmarks")
    op.drop_table("directors")
    op.drop_index("ix_anomalies_severity")
    op.drop_index("ix_anomalies_type")
    op.drop_table("anomalies")
    op.drop_index("ix_tenders_risk_score")
    op.drop_table("tenders")
    op.drop_table("vendors")
