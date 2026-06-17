import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Date, ARRAY, TIMESTAMP, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gem_id = Column(String, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    ministry = Column(String, nullable=False)
    state = Column(String, nullable=False)
    value = Column(BigInteger, nullable=False)
    tender_date = Column(Date, nullable=False)
    close_date = Column(Date, nullable=False)
    winner_vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    bid_count = Column(Integer, default=1)
    risk_score = Column(Integer, default=0)
    anomaly_flags = Column(ARRAY(String), default=[])
    raw_json = Column(JSONB, nullable=True)
    spec_text = Column(Text, nullable=True)
    source = Column(String(20), default="GEM")
    # spec_embedding is vector(1536) added via DDL migration; not mapped as Column
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    winner_vendor = relationship("Vendor", back_populates="won_tenders", foreign_keys=[winner_vendor_id])
    anomalies = relationship("Anomaly", back_populates="tender")
