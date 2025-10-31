"""
Campaign Management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.services.email_campaign import email_service
from app.api.schemas import CampaignCreate, CampaignResponse, CampaignUpdate

router = APIRouter()


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email campaign
    """
    try:
        campaign = email_service.create_campaign(
            db=db,
            user_id=str(current_user.id),
            name=campaign_data.name,
            subject=campaign_data.subject,
            from_email=campaign_data.from_email,
            from_name=campaign_data.from_name,
            content=campaign_data.content
        )

        # Schedule if scheduled_at is provided
        if campaign_data.scheduled_at:
            campaign = email_service.schedule_campaign(
                db=db,
                campaign_id=str(campaign.id),
                scheduled_time=campaign_data.scheduled_at
            )

        return campaign

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all campaigns for the current user
    """
    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific campaign
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a campaign
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Update fields
    if campaign_data.name:
        campaign.name = campaign_data.name
    if campaign_data.subject:
        campaign.subject = campaign_data.subject
    if campaign_data.content:
        campaign.content = campaign_data.content
    if campaign_data.scheduled_at:
        campaign.scheduled_at = campaign_data.scheduled_at

    db.commit()
    db.refresh(campaign)

    return campaign


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    recipient_ids: List[str] = [],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a campaign to recipients
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Get recipients
    if recipient_ids:
        recipients = db.query(Lead).filter(
            Lead.id.in_(recipient_ids),
            Lead.user_id == current_user.id
        ).all()
    else:
        # Send to all leads if no specific recipients
        recipients = db.query(Lead).filter(
            Lead.user_id == current_user.id
        ).limit(1000).all()  # Limit for safety

    # Convert to list of dicts
    recipient_list = [
        {
            "email": r.email,
            "name": r.name or "",
            "company": r.company or ""
        }
        for r in recipients
    ]

    # Send campaign
    result = email_service.send_campaign(
        db=db,
        campaign_id=campaign_id,
        recipients=recipient_list
    )

    return {
        "success": True,
        "campaign_id": campaign_id,
        **result
    }


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a campaign
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    db.delete(campaign)
    db.commit()

    return {"success": True, "message": "Campaign deleted"}


@router.post("/{campaign_id}/track/open")
async def track_email_open(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Track email open (called via tracking pixel)
    """
    email_service.track_open(db, campaign_id)
    return {"success": True}


@router.post("/{campaign_id}/track/click")
async def track_email_click(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Track email click (called via tracking links)
    """
    email_service.track_click(db, campaign_id)
    return {"success": True}
