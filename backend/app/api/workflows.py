"""
Workflow Management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.workflow import Workflow
from app.services.workflow_engine import workflow_engine
from app.api.schemas import WorkflowCreate, WorkflowUpdate, WorkflowResponse

router = APIRouter()


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new workflow
    """
    workflow = workflow_engine.create_workflow(
        db=db,
        user_id=str(current_user.id),
        name=workflow_data.name,
        trigger_type=workflow_data.trigger_type,
        steps=workflow_data.steps
    )

    return workflow


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """
    List all workflows for the current user
    """
    query = db.query(Workflow).filter(Workflow.user_id == current_user.id)

    if active_only:
        query = query.filter(Workflow.active == True)

    workflows = query.offset(skip).limit(limit).all()

    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific workflow
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a workflow
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Update fields
    if workflow_data.name is not None:
        workflow.name = workflow_data.name
    if workflow_data.active is not None:
        workflow.active = workflow_data.active
    if workflow_data.steps is not None:
        workflow.steps = workflow_data.steps

    db.commit()
    db.refresh(workflow)

    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a workflow
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    db.delete(workflow)
    db.commit()

    return {"success": True, "message": "Workflow deleted"}


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate a workflow
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    workflow.active = True
    db.commit()

    return {"success": True, "message": "Workflow activated"}


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a workflow
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    workflow.active = False
    db.commit()

    return {"success": True, "message": "Workflow deactivated"}


@router.post("/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    trigger_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a workflow execution
    """
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Execute workflow asynchronously
    import asyncio
    asyncio.create_task(
        workflow_engine.execute_workflow(
            db=db,
            workflow_id=workflow_id,
            trigger_data=trigger_data
        )
    )

    return {
        "success": True,
        "message": "Workflow triggered successfully",
        "workflow_id": workflow_id
    }


@router.get("/templates/list")
async def list_workflow_templates(current_user: User = Depends(get_current_user)):
    """
    Get list of pre-built workflow templates
    """
    templates = [
        {
            "id": "welcome_series",
            "name": "Welcome Email Series",
            "description": "Send a series of welcome emails to new subscribers",
            "trigger_type": "new_signup",
            "steps": [
                {
                    "type": "wait",
                    "config": {"duration": 300}  # 5 minutes
                },
                {
                    "type": "send_email",
                    "config": {
                        "subject": "Welcome to {{company_name}}!",
                        "content": "Thank you for joining us, {{name}}!"
                    }
                },
                {
                    "type": "wait",
                    "config": {"duration": 86400}  # 24 hours
                },
                {
                    "type": "send_email",
                    "config": {
                        "subject": "Getting Started Guide",
                        "content": "Here's how to make the most of our platform..."
                    }
                }
            ]
        },
        {
            "id": "abandoned_cart",
            "name": "Abandoned Cart Recovery",
            "description": "Follow up with users who abandoned their cart",
            "trigger_type": "cart_abandoned",
            "steps": [
                {
                    "type": "wait",
                    "config": {"duration": 3600}  # 1 hour
                },
                {
                    "type": "send_email",
                    "config": {
                        "subject": "You left something behind!",
                        "content": "Complete your purchase and get 10% off..."
                    }
                },
                {
                    "type": "wait",
                    "config": {"duration": 86400}  # 24 hours
                },
                {
                    "type": "condition",
                    "config": {
                        "condition": {"field": "cart_completed", "operator": "equals", "value": False},
                        "true_path": [],
                        "false_path": [
                            {
                                "type": "send_email",
                                "config": {
                                    "subject": "Last chance - Your cart expires soon!",
                                    "content": "Don't miss out on these items..."
                                }
                            }
                        ]
                    }
                }
            ]
        },
        {
            "id": "re_engagement",
            "name": "Re-engagement Campaign",
            "description": "Win back inactive subscribers",
            "trigger_type": "inactive_30_days",
            "steps": [
                {
                    "type": "send_email",
                    "config": {
                        "subject": "We miss you!",
                        "content": "It's been a while. Here's what you've been missing..."
                    }
                },
                {
                    "type": "wait",
                    "config": {"duration": 604800}  # 7 days
                },
                {
                    "type": "condition",
                    "config": {
                        "condition": {"field": "email_opened", "operator": "equals", "value": False},
                        "true_path": [
                            {
                                "type": "send_email",
                                "config": {
                                    "subject": "Exclusive offer just for you",
                                    "content": "Get 20% off your next purchase..."
                                }
                            }
                        ],
                        "false_path": [
                            {
                                "type": "add_tag",
                                "config": {"tag": "re-engaged"}
                            }
                        ]
                    }
                }
            ]
        }
    ]

    return {"templates": templates}
