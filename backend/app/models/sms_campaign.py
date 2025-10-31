"""
SMS Campaign model
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class SMSCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SMSCampaign(Base):
    __tablename__ = "sms_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    from_number = Column(String(50))
    status = Column(Enum(SMSCampaignStatus), default=SMSCampaignStatus.DRAFT)

    # Metrics
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)

    # Timestamps
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SMSCampaign {self.name}>"
