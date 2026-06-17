import uuid
from sqlalchemy import Column, String, Text, Integer, BigInteger, Float, Boolean, Date, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    gstin = Column(String, unique=True, nullable=True)
    registration_date = Column(Date, nullable=True)  # for shell_vendor detection
    incorporation_date = Column(Date, nullable=True)
    state = Column(String, nullable=True)
    total_wins = Column(Integer, default=0)
    total_value = Column(BigInteger, default=0)
    win_rate = Column(Float, default=0.0)
    risk_level = Column(String, default="low")
    mca_verified = Column(Boolean, default=False)
    cin = Column(Text, nullable=True)
    director_network_json = Column(JSONB, nullable=True, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    won_tenders = relationship("Tender", back_populates="winner_vendor", foreign_keys="Tender.winner_vendor_id")
