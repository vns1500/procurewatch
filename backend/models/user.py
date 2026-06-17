import uuid
import secrets
from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    plan = Column(String, default="free")  # free | pro | enterprise
    reports_used_this_month = Column(Integer, default=0)
    stripe_customer_id = Column(String, nullable=True)
    api_key = Column(String, unique=True, nullable=False, index=True,
                     default=lambda: f"pw_{secrets.token_urlsafe(32)}")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
