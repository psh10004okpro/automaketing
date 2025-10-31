"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ===== User Schemas =====
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None
    company_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    company_name: Optional[str]
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ===== Lead Schemas =====
class LeadCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    score: int
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Campaign Schemas =====
class CampaignCreate(BaseModel):
    name: str
    subject: str
    from_email: EmailStr
    from_name: str
    content: str
    recipient_ids: List[UUID] = []
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    subject: str
    from_email: str
    from_name: str
    status: str
    sent_count: int
    open_count: int
    click_count: int
    conversion_count: int
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


# ===== AI Content Generator Schemas =====
class AIContentRequest(BaseModel):
    content_type: str  # email, social, blog, ad
    target_audience: str
    main_message: str
    tone: str  # professional, friendly, humorous
    platform: str = "openai"  # openai or anthropic


class AIContentResponse(BaseModel):
    content: str
    suggestions: Optional[List[str]] = None
    metadata: Dict[str, Any] = {}


class SubjectLineOptimizeRequest(BaseModel):
    subject_line: str


class SubjectLineOptimizeResponse(BaseModel):
    suggestions: List[str]
    analysis: str


# ===== Workflow Schemas =====
class WorkflowStepSchema(BaseModel):
    type: str  # send_email, wait, condition, add_tag, etc.
    config: Dict[str, Any]


class WorkflowCreate(BaseModel):
    name: str
    trigger_type: str  # new_signup, form_submit, purchase, etc.
    steps: List[WorkflowStepSchema]


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    steps: Optional[List[WorkflowStepSchema]] = None


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    trigger_type: str
    steps: List[Dict[str, Any]]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Social Media Schemas =====
class SocialPostCreate(BaseModel):
    platforms: List[str]  # facebook, instagram, twitter
    content: str
    image_url: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class SocialPostResponse(BaseModel):
    id: UUID
    platforms: List[str]
    content: str
    image_url: Optional[str]
    scheduled_time: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Analytics Schemas =====
class CampaignMetrics(BaseModel):
    total_sent: int
    total_delivered: int
    total_opens: int
    total_clicks: int
    total_conversions: int
    open_rate: float
    click_rate: float
    conversion_rate: float
    revenue: float


class ChannelPerformance(BaseModel):
    channel: str
    cost: float
    revenue: float
    roi: float


class AnalyticsResponse(BaseModel):
    campaign_metrics: CampaignMetrics
    channel_performance: List[ChannelPerformance]
    best_send_time: str
    ai_suggestions: List[str]


# ===== Chatbot Schemas =====
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    metadata: Dict[str, Any] = {}
