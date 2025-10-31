"""
Drip Campaign models for automated email/SMS sequences
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class DripCampaignStatus(str, enum.Enum):
    """Status of drip campaign"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class DripTriggerType(str, enum.Enum):
    """Trigger types for starting a drip campaign"""
    MANUAL = "manual"  # Manually add subscribers
    SIGNUP = "signup"  # User signs up
    PURCHASE = "purchase"  # User makes a purchase
    TAG_ADDED = "tag_added"  # Specific tag added to lead
    FORM_SUBMITTED = "form_submitted"  # Form submission
    LEAD_CREATED = "lead_created"  # New lead created


class StepMessageType(str, enum.Enum):
    """Type of message for a step"""
    EMAIL = "email"
    SMS = "sms"


class StepConditionType(str, enum.Enum):
    """Condition types for step execution"""
    ALWAYS = "always"  # Always send
    OPENED_PREVIOUS = "opened_previous"  # Previous email was opened
    CLICKED_PREVIOUS = "clicked_previous"  # Previous email was clicked
    NOT_OPENED_PREVIOUS = "not_opened_previous"  # Previous email not opened
    NOT_CLICKED_PREVIOUS = "not_clicked_previous"  # Previous email not clicked


class SubscriberStatus(str, enum.Enum):
    """Status of a subscriber in the drip campaign"""
    ACTIVE = "active"  # Currently in campaign
    COMPLETED = "completed"  # Finished all steps
    UNSUBSCRIBED = "unsubscribed"  # Unsubscribed
    BOUNCED = "bounced"  # Email bounced
    FAILED = "failed"  # Failed to send


class DripCampaign(Base):
    """Drip Campaign model for automated sequences"""
    __tablename__ = "drip_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(DripCampaignStatus), default=DripCampaignStatus.DRAFT)

    # Trigger configuration
    trigger_type = Column(Enum(DripTriggerType), default=DripTriggerType.MANUAL)
    trigger_config = Column(JSON)  # Additional trigger configuration

    # Campaign settings
    goal = Column(String(255))  # Campaign goal (e.g., "Onboard new users")
    total_steps = Column(Integer, default=0)  # Total number of steps

    # Statistics
    total_subscribers = Column(Integer, default=0)
    active_subscribers = Column(Integer, default=0)
    completed_subscribers = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)

    # Performance metrics
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    paused_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="drip_campaigns")
    steps = relationship("DripStep", back_populates="campaign", cascade="all, delete-orphan", order_by="DripStep.step_order")
    subscribers = relationship("DripSubscriber", back_populates="campaign", cascade="all, delete-orphan")


class DripStep(Base):
    """Individual step in a drip campaign sequence"""
    __tablename__ = "drip_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("drip_campaigns.id"), nullable=False)

    # Step configuration
    step_order = Column(Integer, nullable=False)  # Order in sequence (1, 2, 3...)
    name = Column(String(255), nullable=False)

    # Timing
    delay_days = Column(Integer, default=0)  # Days after previous step
    delay_hours = Column(Integer, default=0)  # Hours after previous step
    delay_minutes = Column(Integer, default=0)  # Minutes after previous step

    # Message configuration
    message_type = Column(Enum(StepMessageType), nullable=False)
    subject = Column(String(500))  # For email
    from_name = Column(String(255))  # For email
    content = Column(Text, nullable=False)

    # Call to action
    cta_text = Column(String(255))
    cta_url = Column(String(500))

    # Condition for sending this step
    condition_type = Column(Enum(StepConditionType), default=StepConditionType.ALWAYS)

    # Statistics for this step
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)  # Skipped due to conditions

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("DripCampaign", back_populates="steps")
    subscriber_progresses = relationship("DripSubscriberProgress", back_populates="step", cascade="all, delete-orphan")


class DripSubscriber(Base):
    """Subscriber enrolled in a drip campaign"""
    __tablename__ = "drip_subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("drip_campaigns.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"))

    # Subscriber info
    email = Column(String(255))
    phone = Column(String(50))
    name = Column(String(255))

    # Status
    status = Column(Enum(SubscriberStatus), default=SubscriberStatus.ACTIVE)
    current_step = Column(Integer, default=0)  # Current step number (0 = not started)

    # Metadata
    custom_fields = Column(JSON)  # Custom data for personalization

    # Timestamps
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    unsubscribed_at = Column(DateTime)
    last_sent_at = Column(DateTime)  # Last time a message was sent
    next_send_at = Column(DateTime)  # When next message should be sent

    # Relationships
    campaign = relationship("DripCampaign", back_populates="subscribers")
    lead = relationship("Lead", backref="drip_subscriptions")
    progress = relationship("DripSubscriberProgress", back_populates="subscriber", cascade="all, delete-orphan")


class DripSubscriberProgress(Base):
    """Track progress of each subscriber through each step"""
    __tablename__ = "drip_subscriber_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey("drip_subscribers.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("drip_steps.id"), nullable=False)

    # Status
    sent = Column(Boolean, default=False)
    delivered = Column(Boolean, default=False)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    failed = Column(Boolean, default=False)
    skipped = Column(Boolean, default=False)

    # Message details
    message_id = Column(String(255))  # External message ID (from email/SMS provider)
    error_message = Column(Text)  # Error if failed

    # Timestamps
    scheduled_at = Column(DateTime)  # When it was scheduled to send
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    failed_at = Column(DateTime)

    # Relationships
    subscriber = relationship("DripSubscriber", back_populates="progress")
    step = relationship("DripStep", back_populates="subscriber_progresses")


# Add relationships to User and Lead models (to be added in respective files)
# User.drip_campaigns = relationship("DripCampaign", back_populates="user")
