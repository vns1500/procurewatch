import uuid
from sqlalchemy import Column, String, Integer, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ministries = Column(ARRAY(String), default=[])
    keywords = Column(ARRAY(String), default=[])
    email = Column(String, nullable=False)
    status = Column(String, default="active")  # active | paused
    last_triggered = Column(TIMESTAMP(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
