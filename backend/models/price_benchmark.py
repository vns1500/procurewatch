import uuid
from sqlalchemy import Column, String, Text, BigInteger, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.database import Base


class PriceBenchmark(Base):
    __tablename__ = "price_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_name = Column(Text, nullable=False)
    unit = Column(String, nullable=False)
    avg_price = Column(BigInteger, nullable=False)
    min_price = Column(BigInteger, nullable=False)
    max_price = Column(BigInteger, nullable=False)
    source = Column(String, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
