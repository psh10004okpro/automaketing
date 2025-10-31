"""
A/B Test models for campaign optimization
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class ABTestType(str, enum.Enum):
    """Type of A/B test"""
    EMAIL = "email"
    SMS = "sms"


class ABTestStatus(str, enum.Enum):
    """Status of A/B test"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WinnerMetric(str, enum.Enum):
    """Metric used to determine winner"""
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    RESPONSE_RATE = "response_rate"  # For SMS


class ABTest(Base):
    """A/B Test model for campaign optimization"""
    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(ABTestType), nullable=False)
    status = Column(Enum(ABTestStatus), default=ABTestStatus.DRAFT)

    # Test variants (JSON containing subject, content, cta, etc.)
    variant_a = Column(JSON, nullable=False)
    variant_b = Column(JSON, nullable=False)

    # Test configuration
    test_percentage = Column(Float, default=20.0)  # % of total recipients for testing
    variant_split = Column(Float, default=50.0)  # % split between A and B (50 = 50/50)
    winner_metric = Column(Enum(WinnerMetric), default=WinnerMetric.OPEN_RATE)
    wait_time_hours = Column(Integer, default=24)  # Hours to wait before declaring winner
    auto_send_winner = Column(Boolean, default=True)  # Auto send to remaining recipients

    # Winner information
    winner_variant = Column(String(1))  # 'A' or 'B'
    winner_declared_at = Column(DateTime)
    winner_confidence = Column(Float)  # Statistical confidence level

    # Variant A metrics
    variant_a_sent = Column(Integer, default=0)
    variant_a_delivered = Column(Integer, default=0)
    variant_a_opens = Column(Integer, default=0)
    variant_a_clicks = Column(Integer, default=0)
    variant_a_conversions = Column(Integer, default=0)
    variant_a_unsubscribes = Column(Integer, default=0)

    # Variant B metrics
    variant_b_sent = Column(Integer, default=0)
    variant_b_delivered = Column(Integer, default=0)
    variant_b_opens = Column(Integer, default=0)
    variant_b_clicks = Column(Integer, default=0)
    variant_b_conversions = Column(Integer, default=0)
    variant_b_unsubscribes = Column(Integer, default=0)

    # Recipient lists
    test_recipients = Column(JSON)  # List of recipient IDs used for testing
    remaining_recipients = Column(JSON)  # List of recipient IDs for winner

    # Campaign references
    campaign_id = Column(UUID(as_uuid=True))  # Reference to parent campaign
    winner_campaign_id = Column(UUID(as_uuid=True))  # Campaign created for winner

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="ab_tests")


# Add relationship to User model (to be added in user.py)
# ab_tests = relationship("ABTest", back_populates="user")
