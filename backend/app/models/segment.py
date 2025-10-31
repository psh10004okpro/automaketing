"""
Segment models for advanced audience targeting
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class SegmentType(str, enum.Enum):
    """Type of segment"""
    STATIC = "static"  # Fixed list of leads
    DYNAMIC = "dynamic"  # Automatically updated based on conditions


class FilterOperator(str, enum.Enum):
    """Operators for filter conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"  # In a list
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    BETWEEN = "between"
    IN_LAST_DAYS = "in_last_days"  # For dates


class FilterLogic(str, enum.Enum):
    """Logic operator for combining filters"""
    AND = "and"
    OR = "or"


class FilterFieldType(str, enum.Enum):
    """Types of fields that can be filtered"""
    # Lead properties
    LEAD_PROPERTY = "lead_property"  # email, name, company, title, etc.
    LEAD_SCORE = "lead_score"
    LEAD_STATUS = "lead_status"
    LEAD_SOURCE = "lead_source"
    LEAD_TAG = "lead_tag"

    # Behavior
    EMAIL_OPENED = "email_opened"  # Opened any/specific email
    EMAIL_CLICKED = "email_clicked"  # Clicked any/specific email
    CAMPAIGN_RECEIVED = "campaign_received"  # Received specific campaign
    LAST_ACTIVITY_DATE = "last_activity_date"

    # Engagement
    TOTAL_EMAILS_OPENED = "total_emails_opened"
    TOTAL_EMAILS_CLICKED = "total_emails_clicked"
    ENGAGEMENT_SCORE = "engagement_score"

    # Custom fields
    CUSTOM_FIELD = "custom_field"


class Segment(Base):
    """Segment model for audience targeting"""
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    segment_type = Column(Enum(SegmentType), default=SegmentType.DYNAMIC)

    # Filter configuration (for dynamic segments)
    filter_logic = Column(Enum(FilterLogic), default=FilterLogic.AND)  # How to combine filters
    filters = Column(JSON)  # List of filter conditions

    # Static segment data
    static_lead_ids = Column(JSON)  # List of lead IDs (for static segments)

    # Statistics
    lead_count = Column(Integer, default=0)  # Cached count
    last_calculated_at = Column(DateTime)  # When count was last calculated

    # Settings
    auto_update = Column(Boolean, default=True)  # Auto update dynamic segments

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="segments")
    memberships = relationship("SegmentMembership", back_populates="segment", cascade="all, delete-orphan")


class SegmentMembership(Base):
    """Junction table tracking which leads are in which segments"""
    __tablename__ = "segment_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)

    # When lead was added to segment
    added_at = Column(DateTime, default=datetime.utcnow)

    # For dynamic segments - when to re-evaluate
    needs_reevaluation = Column(Boolean, default=False)

    # Relationships
    segment = relationship("Segment", back_populates="memberships")
    lead = relationship("Lead", backref="segment_memberships")


# Filter condition structure (stored in JSON):
# {
#     "field_type": "lead_property",
#     "field_name": "email",
#     "operator": "contains",
#     "value": "@gmail.com"
# }
#
# {
#     "field_type": "lead_score",
#     "operator": "greater_than",
#     "value": 50
# }
#
# {
#     "field_type": "email_opened",
#     "campaign_id": "uuid-here",  # Optional: specific campaign
#     "operator": "equals",
#     "value": true
# }
#
# {
#     "field_type": "last_activity_date",
#     "operator": "in_last_days",
#     "value": 30
# }
#
# Multiple filters combined with AND/OR:
# filters = [
#     {
#         "field_type": "lead_score",
#         "operator": "greater_than",
#         "value": 50
#     },
#     {
#         "field_type": "email_opened",
#         "operator": "equals",
#         "value": true
#     }
# ]
# filter_logic = "and"  # Both conditions must be true


# Add relationship to User model (to be added in user.py)
# segments = relationship("Segment", back_populates="user")
