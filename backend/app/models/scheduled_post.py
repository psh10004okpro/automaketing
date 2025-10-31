"""
Scheduled Post model
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class PostStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platforms = Column(ARRAY(Text), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500))
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.SCHEDULED)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduledPost {self.id}>"
