import uuid
from sqlalchemy import Column, String, Text, BigInteger, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..core.database import Base


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ministry = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(BigInteger, nullable=True)
    irregularity_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    tender_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
