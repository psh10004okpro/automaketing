"""
Lead Management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.lead import Lead
from app.models.activity import Activity
from app.api.schemas import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new lead
    """
    # Check if lead with email already exists
    existing_lead = db.query(Lead).filter(
        Lead.email == lead_data.email,
        Lead.user_id == current_user.id
    ).first()

    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead with this email already exists"
        )

    # Create new lead
    lead = Lead(
        user_id=current_user.id,
        email=lead_data.email,
        name=lead_data.name,
        phone=lead_data.phone,
        company=lead_data.company,
        job_title=lead_data.job_title,
        tags=lead_data.tags,
        custom_fields=lead_data.custom_fields,
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    min_score: Optional[int] = None
):
    """
    List all leads with optional filtering
    """
    query = db.query(Lead).filter(Lead.user_id == current_user.id)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Lead.name.ilike(search_term)) |
            (Lead.email.ilike(search_term)) |
            (Lead.company.ilike(search_term))
        )

    if tag:
        query = query.filter(Lead.tags.contains([tag]))

    if min_score is not None:
        query = query.filter(Lead.score >= min_score)

    # Order by score descending
    leads = query.order_by(Lead.score.desc()).offset(skip).limit(limit).all()

    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    lead_data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a lead
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    # Update fields
    if lead_data.name is not None:
        lead.name = lead_data.name
    if lead_data.phone is not None:
        lead.phone = lead_data.phone
    if lead_data.company is not None:
        lead.company = lead_data.company
    if lead_data.job_title is not None:
        lead.job_title = lead_data.job_title
    if lead_data.tags is not None:
        lead.tags = lead_data.tags
    if lead_data.custom_fields is not None:
        lead.custom_fields = lead_data.custom_fields

    lead.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(lead)

    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a lead
    """
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    db.delete(lead)
    db.commit()

    return {"success": True, "message": "Lead deleted successfully"}


@router.get("/{lead_id}/activities")
async def get_lead_activities(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get activities for a specific lead
    """
    # Verify lead belongs to user
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    activities = db.query(Activity).filter(
        Activity.lead_id == lead_id
    ).order_by(Activity.timestamp.desc()).limit(limit).all()

    return activities


@router.post("/{lead_id}/activities")
async def add_lead_activity(
    lead_id: str,
    activity_type: str,
    metadata: dict = {},
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add an activity to a lead
    """
    # Verify lead belongs to user
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.user_id == current_user.id
    ).first()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )

    activity = Activity(
        lead_id=lead_id,
        activity_type=activity_type,
        metadata=metadata
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    # Update lead score based on activity
    score_updates = {
        "email_open": 5,
        "email_click": 10,
        "website_visit": 3,
        "form_submit": 15,
        "demo_request": 50,
    }

    if activity_type in score_updates:
        lead.score += score_updates[activity_type]
        db.commit()

    return activity


@router.get("/stats/summary")
async def get_leads_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for leads
    """
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()

    hot_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 70
    ).count()

    # Get most common tags
    all_leads = db.query(Lead).filter(Lead.user_id == current_user.id).all()
    tag_counts = {}
    for lead in all_leads:
        for tag in lead.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "hot_leads_percentage": (hot_leads / total_leads * 100) if total_leads > 0 else 0,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags]
    }


@router.post("/import")
async def import_leads(
    leads: List[LeadCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk import leads
    """
    imported = 0
    skipped = 0
    errors = []

    for lead_data in leads:
        try:
            # Check if already exists
            existing = db.query(Lead).filter(
                Lead.email == lead_data.email,
                Lead.user_id == current_user.id
            ).first()

            if existing:
                skipped += 1
                continue

            # Create new lead
            lead = Lead(
                user_id=current_user.id,
                email=lead_data.email,
                name=lead_data.name,
                phone=lead_data.phone,
                company=lead_data.company,
                job_title=lead_data.job_title,
                tags=lead_data.tags,
                custom_fields=lead_data.custom_fields,
            )

            db.add(lead)
            imported += 1

        except Exception as e:
            errors.append({"email": lead_data.email, "error": str(e)})

    db.commit()

    return {
        "success": True,
        "imported": imported,
        "skipped": skipped,
        "errors": errors
    }
