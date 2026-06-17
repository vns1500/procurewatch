import uuid
from sqlalchemy import Column, String, Text, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    report_type = Column(String(20), default="quick")  # quick | full
    title = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)   # CRITICAL | HIGH | MEDIUM
    status = Column(String, default="generating")     # generating | ready | failed
    sections = Column(JSONB, nullable=True)           # structured parsed content
    raw_markdown = Column(Text, nullable=True)        # raw Claude output
    summary_preview = Column(Text, nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
