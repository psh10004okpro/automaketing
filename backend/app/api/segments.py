"""
Segment API endpoints for advanced audience targeting
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.segment import Segment, SegmentType, FilterLogic
from app.services.segmentation import segmentation_service
from app.api.auth import get_current_user
from app.models.user import User


router = APIRouter()


# Pydantic schemas
class FilterCondition(BaseModel):
    """Schema for a single filter condition"""
    field_type: str
    field_name: Optional[str] = None
    operator: str
    value: any  # Can be string, number, boolean, list, etc.
    campaign_id: Optional[str] = None  # For campaign-specific filters


class SegmentCreate(BaseModel):
    """Schema for creating a segment"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_logic: FilterLogic = FilterLogic.AND
    filters: List[FilterCondition] = []
    static_lead_ids: List[str] = []
    auto_update: bool = True


class SegmentUpdate(BaseModel):
    """Schema for updating a segment"""
    name: Optional[str] = None
    description: Optional[str] = None
    filter_logic: Optional[FilterLogic] = None
    filters: Optional[List[FilterCondition]] = None
    auto_update: Optional[bool] = None


class SegmentPreview(BaseModel):
    """Schema for previewing segment results"""
    filter_logic: FilterLogic = FilterLogic.AND
    filters: List[FilterCondition]


class AddLeadsToSegment(BaseModel):
    """Schema for adding leads to static segment"""
    lead_ids: List[str]


class SegmentResponse(BaseModel):
    """Response schema for segment"""
    id: str
    name: str
    description: Optional[str]
    segment_type: str
    filter_logic: str
    filters: List[dict]
    static_lead_ids: List[str]
    lead_count: int
    auto_update: bool
    created_at: str
    updated_at: str
    last_calculated_at: Optional[str]

    class Config:
        from_attributes = True


class LeadSummary(BaseModel):
    """Summary of a lead for preview"""
    id: str
    email: str
    name: Optional[str]
    company: Optional[str]
    score: int
    status: str


class SegmentPreviewResponse(BaseModel):
    """Response for segment preview"""
    count: int
    sample_leads: List[LeadSummary]


@router.post("/", response_model=SegmentResponse)
def create_segment(
    segment_data: SegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new segment"""
    try:
        # Convert filters to dict
        filters_dict = [f.dict() for f in segment_data.filters]

        segment = segmentation_service.create_segment(
            db=db,
            user_id=str(current_user.id),
            name=segment_data.name,
            description=segment_data.description,
            segment_type=segment_data.segment_type.value,
            filter_logic=segment_data.filter_logic.value,
            filters=filters_dict,
            static_lead_ids=segment_data.static_lead_ids,
            auto_update=segment_data.auto_update,
        )
        return _segment_to_response(segment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create segment: {str(e)}",
        )


@router.get("/", response_model=List[SegmentResponse])
def list_segments(
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all segments"""
    segments = segmentation_service.list_segments(
        db=db,
        user_id=str(current_user.id),
        segment_type=type_filter,
    )
    return [_segment_to_response(s) for s in segments]


@router.get("/{segment_id}", response_model=SegmentResponse)
def get_segment(
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    return _segment_to_response(segment)


@router.put("/{segment_id}", response_model=SegmentResponse)
def update_segment(
    segment_id: str,
    segment_data: SegmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    try:
        update_data = segment_data.dict(exclude_unset=True)

        # Convert filters if provided
        if "filters" in update_data and update_data["filters"]:
            update_data["filters"] = [f.dict() for f in segment_data.filters]

        # Convert enums to values
        if "filter_logic" in update_data:
            update_data["filter_logic"] = update_data["filter_logic"].value

        updated = segmentation_service.update_segment(
            db=db,
            segment_id=segment_id,
            **update_data,
        )
        return _segment_to_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{segment_id}")
def delete_segment(
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    success = segmentation_service.delete_segment(db, segment_id)
    if success:
        return {"message": "Segment deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete segment",
        )


@router.post("/{segment_id}/calculate")
def calculate_segment(
    segment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate segment membership"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    if segment.segment_type != SegmentType.DYNAMIC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only calculate dynamic segments",
        )

    try:
        count = segmentation_service.calculate_segment_members(db, segment_id)
        return {
            "message": "Segment calculated successfully",
            "lead_count": count,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{segment_id}/duplicate", response_model=SegmentResponse)
def duplicate_segment(
    segment_id: str,
    new_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duplicate a segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    try:
        duplicate = segmentation_service.duplicate_segment(
            db=db,
            segment_id=segment_id,
            new_name=new_name,
        )
        return _segment_to_response(duplicate)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/preview", response_model=SegmentPreviewResponse)
def preview_segment(
    preview_data: SegmentPreview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview segment results without creating it"""
    try:
        # Convert filters to dict
        filters_dict = [f.dict() for f in preview_data.filters]

        result = segmentation_service.preview_segment(
            db=db,
            user_id=str(current_user.id),
            filters=filters_dict,
            filter_logic=preview_data.filter_logic.value,
        )

        # Convert sample leads to summary format
        sample_leads = [
            {
                "id": str(lead.id),
                "email": lead.email,
                "name": lead.name,
                "company": lead.company,
                "score": lead.score,
                "status": lead.status.value if lead.status else "new",
            }
            for lead in result["sample_leads"]
        ]

        return {
            "count": result["count"],
            "sample_leads": sample_leads,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to preview segment: {str(e)}",
        )


@router.get("/{segment_id}/leads")
def get_segment_leads(
    segment_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get leads in a segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    leads = segmentation_service.get_segment_leads(
        db=db,
        segment_id=segment_id,
        limit=limit,
        offset=offset,
    )

    return {
        "segment_id": segment_id,
        "total_count": segment.lead_count,
        "leads": [
            {
                "id": str(lead.id),
                "email": lead.email,
                "name": lead.name,
                "company": lead.company,
                "score": lead.score,
                "status": lead.status.value if lead.status else "new",
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
            }
            for lead in leads
        ],
    }


@router.post("/{segment_id}/leads", response_model=SegmentResponse)
def add_leads_to_segment(
    segment_id: str,
    data: AddLeadsToSegment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add leads to a static segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    try:
        segmentation_service.add_static_members(
            db=db,
            segment_id=segment_id,
            lead_ids=data.lead_ids,
        )
        # Refresh segment
        db.refresh(segment)
        return _segment_to_response(segment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{segment_id}/leads")
def remove_leads_from_segment(
    segment_id: str,
    data: AddLeadsToSegment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove leads from a static segment"""
    segment = segmentation_service.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segment not found",
        )

    if str(segment.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this segment",
        )

    try:
        segmentation_service.remove_static_members(
            db=db,
            segment_id=segment_id,
            lead_ids=data.lead_ids,
        )
        return {"message": "Leads removed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def _segment_to_response(segment: Segment) -> dict:
    """Convert Segment model to response dict"""
    return {
        "id": str(segment.id),
        "name": segment.name,
        "description": segment.description,
        "segment_type": segment.segment_type.value,
        "filter_logic": segment.filter_logic.value,
        "filters": segment.filters or [],
        "static_lead_ids": segment.static_lead_ids or [],
        "lead_count": segment.lead_count,
        "auto_update": segment.auto_update,
        "created_at": segment.created_at.isoformat() if segment.created_at else None,
        "updated_at": segment.updated_at.isoformat() if segment.updated_at else None,
        "last_calculated_at": segment.last_calculated_at.isoformat()
        if segment.last_calculated_at
        else None,
    }
