"""
Lead model
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    phone = Column(String(50))
    company = Column(String(255))
    job_title = Column(String(255))
    score = Column(Integer, default=0)
    tags = Column(ARRAY(Text), default=[])
    custom_fields = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lead {self.email}>"
