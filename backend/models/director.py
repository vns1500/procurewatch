import uuid
from sqlalchemy import Column, String, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class Director(Base):
    __tablename__ = "directors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    din = Column(String, unique=True, nullable=False)
    vendor_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
