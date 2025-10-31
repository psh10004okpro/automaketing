"""
Advanced Reporting models for data analysis and insights
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class ReportType(str, enum.Enum):
    """Type of report"""
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    CHANNEL_COMPARISON = "channel_comparison"
    LEAD_ANALYTICS = "lead_analytics"
    ENGAGEMENT_METRICS = "engagement_metrics"
    ROI_ANALYSIS = "roi_analysis"
    CONVERSION_FUNNEL = "conversion_funnel"
    CUSTOM = "custom"


class ReportFrequency(str, enum.Enum):
    """Frequency for scheduled reports"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DateRangeType(str, enum.Enum):
    """Predefined date range types"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class ExportFormat(str, enum.Enum):
    """Export format options"""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class Report(Base):
    """Custom report configuration"""
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(Enum(ReportType), nullable=False)

    # Configuration
    config = Column(JSON)  # Metrics, dimensions, filters, etc.

    # Date range
    date_range_type = Column(Enum(DateRangeType), default=DateRangeType.LAST_30_DAYS)
    custom_start_date = Column(DateTime)
    custom_end_date = Column(DateTime)

    # Comparison settings
    compare_enabled = Column(Boolean, default=False)
    compare_period = Column(String(50))  # previous_period, previous_year, etc.

    # Scheduling
    is_scheduled = Column(Boolean, default=False)
    schedule_frequency = Column(Enum(ReportFrequency))
    schedule_time = Column(String(10))  # HH:MM format
    schedule_day_of_week = Column(Integer)  # 0-6 for weekly
    schedule_day_of_month = Column(Integer)  # 1-31 for monthly
    recipients = Column(JSON)  # List of email addresses

    # Last run info
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reports")
    executions = relationship("ReportExecution", back_populates="report", cascade="all, delete-orphan")


class ReportExecution(Base):
    """Record of report executions"""
    __tablename__ = "report_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)

    # Execution info
    executed_at = Column(DateTime, default=datetime.utcnow)
    execution_time_ms = Column(Integer)  # How long it took

    # Date range used
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Results (cached for quick access)
    results_data = Column(JSON)  # The actual report data

    # Comparison results if enabled
    comparison_data = Column(JSON)

    # Export info
    exported = Column(Boolean, default=False)
    export_format = Column(Enum(ExportFormat))
    export_file_path = Column(String(500))

    # Status
    status = Column(String(50), default="completed")  # completed, failed, running
    error_message = Column(Text)

    # Relationships
    report = relationship("Report", back_populates="executions")


# Report configuration structure (stored in JSON):
# {
#     "metrics": [
#         "total_sent",
#         "open_rate",
#         "click_rate",
#         "conversion_rate",
#         "roi"
#     ],
#     "dimensions": [
#         "campaign",
#         "channel",
#         "segment"
#     ],
#     "filters": [
#         {
#             "field": "campaign_status",
#             "operator": "equals",
#             "value": "sent"
#         }
#     ],
#     "visualization": {
#         "chart_type": "line",  # line, bar, pie, area, table
#         "group_by": "date"
#     }
# }

# Add relationship to User model (to be added in user.py)
# reports = relationship("Report", back_populates="user")
