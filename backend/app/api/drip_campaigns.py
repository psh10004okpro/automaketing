"""
Drip Campaign API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.drip_campaign import (
    DripCampaign,
    DripStep,
    DripSubscriber,
    DripCampaignStatus,
    DripTriggerType,
    StepMessageType,
    StepConditionType,
)
from app.services.drip_campaign import drip_campaign_service
from app.api.auth import get_current_user
from app.models.user import User


router = APIRouter()


# Pydantic schemas
class DripCampaignCreate(BaseModel):
    """Schema for creating a drip campaign"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: DripTriggerType = DripTriggerType.MANUAL
    trigger_config: Optional[dict] = None
    goal: Optional[str] = None


class DripCampaignUpdate(BaseModel):
    """Schema for updating a drip campaign"""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[DripTriggerType] = None
    trigger_config: Optional[dict] = None
    goal: Optional[str] = None


class DripStepCreate(BaseModel):
    """Schema for creating a drip step"""
    name: str = Field(..., min_length=1, max_length=255)
    message_type: StepMessageType
    content: str = Field(..., min_length=1)
    delay_days: int = Field(default=0, ge=0)
    delay_hours: int = Field(default=0, ge=0)
    delay_minutes: int = Field(default=0, ge=0)
    subject: Optional[str] = None
    from_name: Optional[str] = None
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    condition_type: StepConditionType = StepConditionType.ALWAYS
    step_order: Optional[int] = None


class DripStepUpdate(BaseModel):
    """Schema for updating a drip step"""
    name: Optional[str] = None
    content: Optional[str] = None
    delay_days: Optional[int] = None
    delay_hours: Optional[int] = None
    delay_minutes: Optional[int] = None
    subject: Optional[str] = None
    from_name: Optional[str] = None
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    condition_type: Optional[StepConditionType] = None


class SubscriberEnroll(BaseModel):
    """Schema for enrolling a subscriber"""
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    lead_id: Optional[str] = None
    custom_fields: Optional[dict] = None


class DripStepResponse(BaseModel):
    """Response schema for drip step"""
    id: str
    campaign_id: str
    step_order: int
    name: str
    message_type: str
    content: str
    delay_days: int
    delay_hours: int
    delay_minutes: int
    subject: Optional[str]
    from_name: Optional[str]
    cta_text: Optional[str]
    cta_url: Optional[str]
    condition_type: str
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    failed_count: int
    skipped_count: int

    class Config:
        from_attributes = True


class DripCampaignResponse(BaseModel):
    """Response schema for drip campaign"""
    id: str
    name: str
    description: Optional[str]
    status: str
    trigger_type: str
    trigger_config: Optional[dict]
    goal: Optional[str]
    total_steps: int
    total_subscribers: int
    active_subscribers: int
    completed_subscribers: int
    unsubscribed_count: int
    total_sent: int
    total_delivered: int
    total_opens: int
    total_clicks: int
    created_at: str
    started_at: Optional[str]
    steps: List[DripStepResponse] = []

    class Config:
        from_attributes = True


class SubscriberResponse(BaseModel):
    """Response schema for subscriber"""
    id: str
    campaign_id: str
    email: Optional[str]
    phone: Optional[str]
    name: Optional[str]
    status: str
    current_step: int
    enrolled_at: str
    completed_at: Optional[str]
    next_send_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=DripCampaignResponse)
def create_drip_campaign(
    campaign_data: DripCampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new drip campaign"""
    try:
        campaign = drip_campaign_service.create_campaign(
            db=db,
            user_id=str(current_user.id),
            name=campaign_data.name,
            description=campaign_data.description,
            trigger_type=campaign_data.trigger_type.value,
            trigger_config=campaign_data.trigger_config,
            goal=campaign_data.goal,
        )
        return _campaign_to_response(campaign)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create drip campaign: {str(e)}",
        )


@router.get("/", response_model=List[DripCampaignResponse])
def list_drip_campaigns(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all drip campaigns"""
    campaigns = drip_campaign_service.list_campaigns(
        db=db,
        user_id=str(current_user.id),
        status=status_filter,
    )
    return [_campaign_to_response(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=DripCampaignResponse)
def get_drip_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    return _campaign_to_response(campaign)


@router.put("/{campaign_id}", response_model=DripCampaignResponse)
def update_drip_campaign(
    campaign_id: str,
    campaign_data: DripCampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        update_data = campaign_data.dict(exclude_unset=True)
        if "trigger_type" in update_data:
            update_data["trigger_type"] = update_data["trigger_type"].value

        updated = drip_campaign_service.update_campaign(
            db=db,
            campaign_id=campaign_id,
            **update_data,
        )
        return _campaign_to_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{campaign_id}")
def delete_drip_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    success = drip_campaign_service.delete_campaign(db, campaign_id)
    if success:
        return {"message": "Drip campaign deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete drip campaign",
        )


@router.post("/{campaign_id}/steps", response_model=DripStepResponse)
def add_step_to_campaign(
    campaign_id: str,
    step_data: DripStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new step to a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        step = drip_campaign_service.add_step(
            db=db,
            campaign_id=campaign_id,
            name=step_data.name,
            message_type=step_data.message_type.value,
            content=step_data.content,
            delay_days=step_data.delay_days,
            delay_hours=step_data.delay_hours,
            delay_minutes=step_data.delay_minutes,
            subject=step_data.subject,
            from_name=step_data.from_name,
            cta_text=step_data.cta_text,
            cta_url=step_data.cta_url,
            condition_type=step_data.condition_type.value,
            step_order=step_data.step_order,
        )
        return _step_to_response(step)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/steps/{step_id}", response_model=DripStepResponse)
def update_step(
    step_id: str,
    step_data: DripStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a drip campaign step"""
    step = db.query(DripStep).filter(DripStep.id == step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    campaign = step.campaign
    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        update_data = step_data.dict(exclude_unset=True)
        if "condition_type" in update_data:
            update_data["condition_type"] = update_data["condition_type"].value

        updated = drip_campaign_service.update_step(
            db=db,
            step_id=step_id,
            **update_data,
        )
        return _step_to_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/steps/{step_id}")
def delete_step(
    step_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a drip campaign step"""
    step = db.query(DripStep).filter(DripStep.id == step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    campaign = step.campaign
    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    success = drip_campaign_service.delete_step(db, step_id)
    if success:
        return {"message": "Step deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete step",
        )


@router.post("/{campaign_id}/activate", response_model=DripCampaignResponse)
def activate_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        activated = drip_campaign_service.activate_campaign(db, campaign_id)
        return _campaign_to_response(activated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{campaign_id}/pause", response_model=DripCampaignResponse)
def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        paused = drip_campaign_service.pause_campaign(db, campaign_id)
        return _campaign_to_response(paused)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{campaign_id}/enroll", response_model=SubscriberResponse)
def enroll_subscriber(
    campaign_id: str,
    subscriber_data: SubscriberEnroll,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enroll a subscriber in a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        subscriber = drip_campaign_service.enroll_subscriber(
            db=db,
            campaign_id=campaign_id,
            email=subscriber_data.email,
            phone=subscriber_data.phone,
            name=subscriber_data.name,
            lead_id=subscriber_data.lead_id,
            custom_fields=subscriber_data.custom_fields,
        )
        return _subscriber_to_response(subscriber)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{campaign_id}/subscribers/{subscriber_id}/unsubscribe")
def unsubscribe_subscriber(
    campaign_id: str,
    subscriber_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unsubscribe a subscriber from a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        subscriber = drip_campaign_service.unsubscribe(db, subscriber_id)
        return {"message": "Subscriber unsubscribed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{campaign_id}/stats")
def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed statistics for a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    try:
        stats = drip_campaign_service.get_campaign_stats(db, campaign_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{campaign_id}/subscribers", response_model=List[SubscriberResponse])
def list_subscribers(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all subscribers in a drip campaign"""
    campaign = drip_campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drip campaign not found",
        )

    if str(campaign.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this campaign",
        )

    subscribers = (
        db.query(DripSubscriber)
        .filter(DripSubscriber.campaign_id == campaign_id)
        .order_by(DripSubscriber.enrolled_at.desc())
        .all()
    )

    return [_subscriber_to_response(s) for s in subscribers]


def _campaign_to_response(campaign: DripCampaign) -> dict:
    """Convert DripCampaign model to response dict"""
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "description": campaign.description,
        "status": campaign.status.value,
        "trigger_type": campaign.trigger_type.value,
        "trigger_config": campaign.trigger_config,
        "goal": campaign.goal,
        "total_steps": campaign.total_steps,
        "total_subscribers": campaign.total_subscribers,
        "active_subscribers": campaign.active_subscribers,
        "completed_subscribers": campaign.completed_subscribers,
        "unsubscribed_count": campaign.unsubscribed_count,
        "total_sent": campaign.total_sent,
        "total_delivered": campaign.total_delivered,
        "total_opens": campaign.total_opens,
        "total_clicks": campaign.total_clicks,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
        "steps": [_step_to_response(step) for step in campaign.steps],
    }


def _step_to_response(step: DripStep) -> dict:
    """Convert DripStep model to response dict"""
    return {
        "id": str(step.id),
        "campaign_id": str(step.campaign_id),
        "step_order": step.step_order,
        "name": step.name,
        "message_type": step.message_type.value,
        "content": step.content,
        "delay_days": step.delay_days,
        "delay_hours": step.delay_hours,
        "delay_minutes": step.delay_minutes,
        "subject": step.subject,
        "from_name": step.from_name,
        "cta_text": step.cta_text,
        "cta_url": step.cta_url,
        "condition_type": step.condition_type.value,
        "sent_count": step.sent_count,
        "delivered_count": step.delivered_count,
        "opened_count": step.opened_count,
        "clicked_count": step.clicked_count,
        "failed_count": step.failed_count,
        "skipped_count": step.skipped_count,
    }


def _subscriber_to_response(subscriber: DripSubscriber) -> dict:
    """Convert DripSubscriber model to response dict"""
    return {
        "id": str(subscriber.id),
        "campaign_id": str(subscriber.campaign_id),
        "email": subscriber.email,
        "phone": subscriber.phone,
        "name": subscriber.name,
        "status": subscriber.status.value,
        "current_step": subscriber.current_step,
        "enrolled_at": subscriber.enrolled_at.isoformat() if subscriber.enrolled_at else None,
        "completed_at": subscriber.completed_at.isoformat() if subscriber.completed_at else None,
        "next_send_at": subscriber.next_send_at.isoformat() if subscriber.next_send_at else None,
    }
