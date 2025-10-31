"""
A/B Testing API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.ab_test import ABTest, ABTestStatus, ABTestType, WinnerMetric
from app.services.ab_test import ab_test_service
from app.api.auth import get_current_user
from app.models.user import User


router = APIRouter()


# Pydantic schemas
class VariantData(BaseModel):
    """Data for a test variant"""
    subject: Optional[str] = None  # For email
    content: str
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    from_name: Optional[str] = None


class ABTestCreate(BaseModel):
    """Schema for creating an A/B test"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ABTestType
    variant_a: VariantData
    variant_b: VariantData
    test_percentage: float = Field(default=20.0, ge=5.0, le=50.0)
    variant_split: float = Field(default=50.0, ge=10.0, le=90.0)
    winner_metric: WinnerMetric = WinnerMetric.OPEN_RATE
    wait_time_hours: int = Field(default=24, ge=1, le=168)
    auto_send_winner: bool = True


class ABTestStart(BaseModel):
    """Schema for starting an A/B test"""
    recipient_ids: List[str]


class ABTestUpdate(BaseModel):
    """Schema for updating test metrics"""
    variant: str = Field(..., pattern="^[AB]$")
    metric: str
    increment: int = 1


class ABTestDeclareWinner(BaseModel):
    """Schema for manually declaring a winner"""
    winner_variant: str = Field(..., pattern="^[AB]$")


class ABTestResponse(BaseModel):
    """Response schema for A/B test"""
    id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    variant_a: dict
    variant_b: dict
    test_percentage: float
    variant_split: float
    winner_metric: str
    wait_time_hours: int
    auto_send_winner: bool
    winner_variant: Optional[str]
    winner_confidence: Optional[float]
    variant_a_sent: int
    variant_a_delivered: int
    variant_a_opens: int
    variant_a_clicks: int
    variant_a_conversions: int
    variant_b_sent: int
    variant_b_delivered: int
    variant_b_opens: int
    variant_b_clicks: int
    variant_b_conversions: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    winner_declared_at: Optional[str]

    class Config:
        from_attributes = True


class ABTestStatsResponse(BaseModel):
    """Response schema for A/B test statistics"""
    variant_a: dict
    variant_b: dict
    winner: Optional[str]
    confidence: Optional[float]
    ready_to_declare: bool


@router.post("/", response_model=ABTestResponse)
def create_ab_test(
    test_data: ABTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new A/B test"""
    try:
        ab_test = ab_test_service.create_test(
            db=db,
            user_id=str(current_user.id),
            name=test_data.name,
            description=test_data.description,
            test_type=test_data.type.value,
            variant_a=test_data.variant_a.dict(),
            variant_b=test_data.variant_b.dict(),
            test_percentage=test_data.test_percentage,
            variant_split=test_data.variant_split,
            winner_metric=test_data.winner_metric.value,
            wait_time_hours=test_data.wait_time_hours,
            auto_send_winner=test_data.auto_send_winner,
        )

        return _ab_test_to_response(ab_test)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create A/B test: {str(e)}",
        )


@router.get("/", response_model=List[ABTestResponse])
def list_ab_tests(
    status_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all A/B tests"""
    tests = ab_test_service.list_tests(
        db=db,
        user_id=str(current_user.id),
        status=status_filter,
        test_type=type_filter,
    )
    return [_ab_test_to_response(test) for test in tests]


@router.get("/{test_id}", response_model=ABTestResponse)
def get_ab_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific A/B test"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    return _ab_test_to_response(ab_test)


@router.post("/{test_id}/start", response_model=ABTestResponse)
def start_ab_test(
    test_id: str,
    start_data: ABTestStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an A/B test with recipient list"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    try:
        updated_test = ab_test_service.start_test(
            db=db,
            test_id=test_id,
            all_recipients=start_data.recipient_ids,
        )
        return _ab_test_to_response(updated_test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{test_id}/metrics", response_model=ABTestResponse)
def update_test_metrics(
    test_id: str,
    metrics_data: ABTestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update metrics for a test variant"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    try:
        updated_test = ab_test_service.update_metrics(
            db=db,
            test_id=test_id,
            variant=metrics_data.variant,
            metric=metrics_data.metric,
            increment=metrics_data.increment,
        )
        return _ab_test_to_response(updated_test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{test_id}/stats", response_model=ABTestStatsResponse)
def get_test_stats(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get statistics and performance metrics for an A/B test"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    rates = ab_test_service.calculate_rates(ab_test)

    return {
        "variant_a": {
            **rates["variant_a"],
            "sent": ab_test.variant_a_sent,
            "delivered": ab_test.variant_a_delivered,
            "opens": ab_test.variant_a_opens,
            "clicks": ab_test.variant_a_clicks,
            "conversions": ab_test.variant_a_conversions,
        },
        "variant_b": {
            **rates["variant_b"],
            "sent": ab_test.variant_b_sent,
            "delivered": ab_test.variant_b_delivered,
            "opens": ab_test.variant_b_opens,
            "clicks": ab_test.variant_b_clicks,
            "conversions": ab_test.variant_b_conversions,
        },
        "winner": ab_test.winner_variant,
        "confidence": ab_test.winner_confidence,
        "ready_to_declare": ab_test.status == ABTestStatus.RUNNING
        and ab_test.variant_a_delivered >= 30
        and ab_test.variant_b_delivered >= 30,
    }


@router.post("/{test_id}/check-winner")
def check_and_declare_winner(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if test is ready and declare winner if applicable"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    result = ab_test_service.check_and_declare_winner(db, test_id)

    if result:
        winner, confidence = result
        return {
            "winner_declared": True,
            "winner_variant": winner,
            "confidence": confidence,
        }
    else:
        return {
            "winner_declared": False,
            "message": "Not enough data or time to declare winner yet",
        }


@router.post("/{test_id}/declare-winner", response_model=ABTestResponse)
def manual_declare_winner(
    test_id: str,
    winner_data: ABTestDeclareWinner,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually declare a winner"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    try:
        updated_test = ab_test_service.manual_declare_winner(
            db=db,
            test_id=test_id,
            winner_variant=winner_data.winner_variant,
        )
        return _ab_test_to_response(updated_test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{test_id}/cancel", response_model=ABTestResponse)
def cancel_ab_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running A/B test"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    try:
        updated_test = ab_test_service.cancel_test(db, test_id)
        return _ab_test_to_response(updated_test)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{test_id}")
def delete_ab_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an A/B test"""
    ab_test = ab_test_service.get_test(db, test_id)
    if not ab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/B test not found",
        )

    if str(ab_test.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this test",
        )

    success = ab_test_service.delete_test(db, test_id)
    if success:
        return {"message": "A/B test deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete A/B test",
        )


def _ab_test_to_response(ab_test: ABTest) -> dict:
    """Convert ABTest model to response dict"""
    return {
        "id": str(ab_test.id),
        "name": ab_test.name,
        "description": ab_test.description,
        "type": ab_test.type.value,
        "status": ab_test.status.value,
        "variant_a": ab_test.variant_a,
        "variant_b": ab_test.variant_b,
        "test_percentage": ab_test.test_percentage,
        "variant_split": ab_test.variant_split,
        "winner_metric": ab_test.winner_metric.value,
        "wait_time_hours": ab_test.wait_time_hours,
        "auto_send_winner": ab_test.auto_send_winner,
        "winner_variant": ab_test.winner_variant,
        "winner_confidence": ab_test.winner_confidence,
        "variant_a_sent": ab_test.variant_a_sent,
        "variant_a_delivered": ab_test.variant_a_delivered,
        "variant_a_opens": ab_test.variant_a_opens,
        "variant_a_clicks": ab_test.variant_a_clicks,
        "variant_a_conversions": ab_test.variant_a_conversions,
        "variant_b_sent": ab_test.variant_b_sent,
        "variant_b_delivered": ab_test.variant_b_delivered,
        "variant_b_opens": ab_test.variant_b_opens,
        "variant_b_clicks": ab_test.variant_b_clicks,
        "variant_b_conversions": ab_test.variant_b_conversions,
        "created_at": ab_test.created_at.isoformat() if ab_test.created_at else None,
        "started_at": ab_test.started_at.isoformat() if ab_test.started_at else None,
        "completed_at": ab_test.completed_at.isoformat() if ab_test.completed_at else None,
        "winner_declared_at": ab_test.winner_declared_at.isoformat()
        if ab_test.winner_declared_at
        else None,
    }
