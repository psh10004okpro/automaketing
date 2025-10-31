"""
Advanced Reporting API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.database import get_db
from app.models.report import Report, ReportExecution, ReportType, DateRangeType
from app.services.reporting import reporting_service
from app.api.auth import get_current_user
from app.models.user import User


router = APIRouter()


# Pydantic schemas
class ReportCreate(BaseModel):
    """Schema for creating a report"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: ReportType
    config: dict = {}
    date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    compare_enabled: bool = False
    compare_period: Optional[str] = None


class ReportUpdate(BaseModel):
    """Schema for updating a report"""
    name: Optional[str] = None
    description: Optional[str] = None
    date_range_type: Optional[DateRangeType] = None
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    compare_enabled: Optional[bool] = None
    compare_period: Optional[str] = None


class QuickReportRequest(BaseModel):
    """Schema for quick report generation"""
    report_type: ReportType
    date_range_type: DateRangeType = DateRangeType.LAST_30_DAYS
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    compare_enabled: bool = False
    compare_period: Optional[str] = None


class ReportResponse(BaseModel):
    """Response schema for report"""
    id: str
    name: str
    description: Optional[str]
    report_type: str
    config: dict
    date_range_type: str
    custom_start_date: Optional[str]
    custom_end_date: Optional[str]
    compare_enabled: bool
    compare_period: Optional[str]
    last_run_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Response schema for report execution"""
    id: str
    report_id: str
    executed_at: str
    execution_time_ms: int
    start_date: str
    end_date: str
    results_data: dict
    comparison_data: Optional[dict]
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=ReportResponse)
def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new custom report"""
    try:
        report = reporting_service.create_report(
            db=db,
            user_id=str(current_user.id),
            name=report_data.name,
            description=report_data.description,
            report_type=report_data.report_type.value,
            config=report_data.config,
            date_range_type=report_data.date_range_type.value,
            custom_start_date=report_data.custom_start_date,
            custom_end_date=report_data.custom_end_date,
            compare_enabled=report_data.compare_enabled,
            compare_period=report_data.compare_period,
        )
        return _report_to_response(report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create report: {str(e)}",
        )


@router.get("/", response_model=List[ReportResponse])
def list_reports(
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reports"""
    reports = reporting_service.list_reports(
        db=db,
        user_id=str(current_user.id),
        report_type=type_filter,
    )
    return [_report_to_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific report"""
    report = reporting_service.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    return _report_to_response(report)


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a report"""
    report = reporting_service.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    success = reporting_service.delete_report(db, report_id)
    if success:
        return {"message": "Report deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete report",
        )


@router.post("/{report_id}/run", response_model=ExecutionResponse)
def run_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a report"""
    report = reporting_service.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    try:
        execution = reporting_service.execute_report(db, report)
        return _execution_to_response(execution)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute report: {str(e)}",
        )


@router.post("/quick-report", response_model=ExecutionResponse)
def generate_quick_report(
    request: QuickReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a quick report without saving configuration"""
    try:
        # Create temporary report
        temp_report = reporting_service.create_report(
            db=db,
            user_id=str(current_user.id),
            name=f"Quick {request.report_type.value} Report",
            report_type=request.report_type.value,
            config={},
            date_range_type=request.date_range_type.value,
            custom_start_date=request.custom_start_date,
            custom_end_date=request.custom_end_date,
            compare_enabled=request.compare_enabled,
            compare_period=request.compare_period,
        )

        # Execute it
        execution = reporting_service.execute_report(db, temp_report)

        # Delete the temporary report
        reporting_service.delete_report(db, str(temp_report.id))

        return _execution_to_response(execution)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quick report: {str(e)}",
        )


@router.get("/{report_id}/executions", response_model=List[ExecutionResponse])
def list_report_executions(
    report_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List execution history for a report"""
    report = reporting_service.get_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )

    executions = (
        db.query(ReportExecution)
        .filter(ReportExecution.report_id == report_id)
        .order_by(ReportExecution.executed_at.desc())
        .limit(limit)
        .all()
    )

    return [_execution_to_response(e) for e in executions]


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific execution result"""
    execution = (
        db.query(ReportExecution)
        .filter(ReportExecution.id == execution_id)
        .first()
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    report = execution.report
    if str(report.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this execution",
        )

    return _execution_to_response(execution)


def _report_to_response(report: Report) -> dict:
    """Convert Report model to response dict"""
    return {
        "id": str(report.id),
        "name": report.name,
        "description": report.description,
        "report_type": report.report_type.value,
        "config": report.config or {},
        "date_range_type": report.date_range_type.value,
        "custom_start_date": report.custom_start_date.isoformat()
        if report.custom_start_date
        else None,
        "custom_end_date": report.custom_end_date.isoformat()
        if report.custom_end_date
        else None,
        "compare_enabled": report.compare_enabled,
        "compare_period": report.compare_period,
        "last_run_at": report.last_run_at.isoformat() if report.last_run_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


def _execution_to_response(execution: ReportExecution) -> dict:
    """Convert ReportExecution model to response dict"""
    return {
        "id": str(execution.id),
        "report_id": str(execution.report_id),
        "executed_at": execution.executed_at.isoformat() if execution.executed_at else None,
        "execution_time_ms": execution.execution_time_ms,
        "start_date": execution.start_date.isoformat() if execution.start_date else None,
        "end_date": execution.end_date.isoformat() if execution.end_date else None,
        "results_data": execution.results_data or {},
        "comparison_data": execution.comparison_data,
        "status": execution.status,
    }
