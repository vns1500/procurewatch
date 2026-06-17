import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    evidence = Column(JSONB, nullable=True)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    status = Column(String, default="open")

    tender = relationship("Tender", back_populates="anomalies")
