"""
SMS Campaign API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.sms_campaign import SMSCampaign
from app.models.lead import Lead
from app.services.sms_campaign import sms_service

router = APIRouter()


# Schemas
class SMSCampaignCreate(BaseModel):
    name: str
    message: str = Field(..., max_length=1600)  # SMS character limit
    from_number: str = None
    recipient_ids: List[str] = []
    scheduled_at: datetime = None


class SMSCampaignUpdate(BaseModel):
    name: str = None
    message: str = None
    scheduled_at: datetime = None


class SMSCampaignResponse(BaseModel):
    id: str
    name: str
    message: str
    from_number: str
    status: str
    sent_count: int
    delivered_count: int
    failed_count: int
    created_at: datetime
    sent_at: datetime = None

    class Config:
        from_attributes = True


@router.post("/", response_model=SMSCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_sms_campaign(
    campaign_data: SMSCampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new SMS campaign
    """
    try:
        campaign = sms_service.create_campaign(
            db=db,
            user_id=str(current_user.id),
            name=campaign_data.name,
            message=campaign_data.message,
            from_number=campaign_data.from_number
        )

        # Schedule if scheduled_at is provided
        if campaign_data.scheduled_at:
            campaign = sms_service.schedule_campaign(
                db=db,
                campaign_id=str(campaign.id),
                scheduled_time=campaign_data.scheduled_at
            )

        return campaign

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SMS campaign: {str(e)}"
        )


@router.get("/", response_model=List[SMSCampaignResponse])
async def list_sms_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all SMS campaigns for the current user
    """
    campaigns = db.query(SMSCampaign).filter(
        SMSCampaign.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return campaigns


@router.get("/{campaign_id}", response_model=SMSCampaignResponse)
async def get_sms_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific SMS campaign
    """
    campaign = db.query(SMSCampaign).filter(
        SMSCampaign.id == campaign_id,
        SMSCampaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMS Campaign not found"
        )

    return campaign


@router.put("/{campaign_id}", response_model=SMSCampaignResponse)
async def update_sms_campaign(
    campaign_id: str,
    campaign_data: SMSCampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an SMS campaign
    """
    campaign = db.query(SMSCampaign).filter(
        SMSCampaign.id == campaign_id,
        SMSCampaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMS Campaign not found"
        )

    # Update fields
    if campaign_data.name:
        campaign.name = campaign_data.name
    if campaign_data.message:
        campaign.message = campaign_data.message
    if campaign_data.scheduled_at:
        campaign.scheduled_at = campaign_data.scheduled_at

    db.commit()
    db.refresh(campaign)

    return campaign


@router.post("/{campaign_id}/send")
async def send_sms_campaign(
    campaign_id: str,
    recipient_ids: List[str] = [],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an SMS campaign to recipients
    """
    campaign = db.query(SMSCampaign).filter(
        SMSCampaign.id == campaign_id,
        SMSCampaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMS Campaign not found"
        )

    # Get recipients
    if recipient_ids:
        recipients = db.query(Lead).filter(
            Lead.id.in_(recipient_ids),
            Lead.user_id == current_user.id
        ).all()
    else:
        # Send to all leads with phone numbers if no specific recipients
        recipients = db.query(Lead).filter(
            Lead.user_id == current_user.id,
            Lead.phone.isnot(None)
        ).limit(1000).all()  # Limit for safety

    # Validate recipients have phone numbers
    valid_recipients = []
    for recipient in recipients:
        if recipient.phone:
            valid_recipients.append({
                "phone": recipient.phone,
                "name": recipient.name or "",
                "email": recipient.email
            })

    if not valid_recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients with valid phone numbers found"
        )

    # Send campaign
    result = sms_service.send_campaign(
        db=db,
        campaign_id=campaign_id,
        recipients=valid_recipients
    )

    return {
        "success": True,
        "campaign_id": campaign_id,
        **result
    }


@router.delete("/{campaign_id}")
async def delete_sms_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an SMS campaign
    """
    campaign = db.query(SMSCampaign).filter(
        SMSCampaign.id == campaign_id,
        SMSCampaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMS Campaign not found"
        )

    db.delete(campaign)
    db.commit()

    return {"success": True, "message": "SMS Campaign deleted"}


@router.get("/{campaign_id}/status")
async def get_sms_campaign_status(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed status of an SMS campaign
    """
    campaign = db.query(SMSCampaign).filter(
        SMSCampaign.id == campaign_id,
        SMSCampaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SMS Campaign not found"
        )

    return sms_service.get_campaign_status(db, campaign_id)


@router.post("/validate-phone")
async def validate_phone_number(
    phone: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate a phone number format
    """
    is_valid = sms_service.validate_phone_number(phone)

    return {
        "phone": phone,
        "is_valid": is_valid,
        "message": "Phone number is valid" if is_valid else "Invalid phone number format. Use international format (e.g., +1234567890)"
    }
