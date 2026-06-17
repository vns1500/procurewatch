import uuid
from sqlalchemy import Column, BigInteger, Date, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..core.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    original_value = Column(BigInteger, nullable=False)
    current_value = Column(BigInteger, nullable=False)
    award_date = Column(Date, nullable=True)
    amendments = Column(JSONB, default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
