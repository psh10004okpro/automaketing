"""
Social Media Management API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.scheduled_post import ScheduledPost
from app.models.social_account import SocialAccount
from app.services.social_media import social_media_service

router = APIRouter()


# Schemas
class SocialPostCreate(BaseModel):
    platforms: List[str]
    content: str
    image_url: Optional[str] = None
    scheduled_time: Optional[datetime] = None


class SocialPostResponse(BaseModel):
    id: str
    platforms: List[str]
    content: str
    image_url: Optional[str]
    scheduled_time: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SocialAccountConnect(BaseModel):
    platform: str
    account_id: str
    account_name: str
    access_token: str
    refresh_token: Optional[str] = None


@router.post("/posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_social_post(
    post_data: SocialPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create and optionally schedule a social media post
    """
    try:
        if post_data.scheduled_time:
            # Schedule for later
            post = social_media_service.create_scheduled_post(
                db=db,
                user_id=str(current_user.id),
                platforms=post_data.platforms,
                content=post_data.content,
                image_url=post_data.image_url,
                scheduled_time=post_data.scheduled_time
            )
        else:
            # Post immediately
            post = social_media_service.create_scheduled_post(
                db=db,
                user_id=str(current_user.id),
                platforms=post_data.platforms,
                content=post_data.content,
                image_url=post_data.image_url,
                scheduled_time=datetime.utcnow()
            )

            # Publish immediately
            result = social_media_service.publish_post(db, str(post.id))

            if not result.get("all_successful"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to post to some platforms: {result.get('results')}"
                )

        return post

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create social post: {str(e)}"
        )


@router.get("/posts", response_model=List[SocialPostResponse])
async def list_social_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    skip: int = 0,
    limit: int = 100
):
    """
    List all scheduled/posted social media posts
    """
    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user.id)

    if status_filter:
        query = query.filter(ScheduledPost.status == status_filter)

    posts = query.order_by(ScheduledPost.created_at.desc()).offset(skip).limit(limit).all()

    return posts


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
async def get_social_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific social media post
    """
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return post


@router.delete("/posts/{post_id}")
async def delete_social_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a scheduled social media post
    """
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    db.delete(post)
    db.commit()

    return {"success": True, "message": "Post deleted"}


@router.post("/posts/{post_id}/publish")
async def publish_post_now(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Publish a scheduled post immediately
    """
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    result = social_media_service.publish_post(db, post_id)

    return result


@router.post("/accounts/connect")
async def connect_social_account(
    account_data: SocialAccountConnect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect a social media account
    """
    # Check if account already exists
    existing = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.platform == account_data.platform,
        SocialAccount.account_id == account_data.account_id
    ).first()

    if existing:
        # Update existing
        existing.access_token = account_data.access_token
        existing.refresh_token = account_data.refresh_token
        existing.account_name = account_data.account_name
        db.commit()
        return {"success": True, "message": "Account updated", "account_id": str(existing.id)}

    # Create new
    account = SocialAccount(
        user_id=current_user.id,
        platform=account_data.platform,
        account_id=account_data.account_id,
        account_name=account_data.account_name,
        access_token=account_data.access_token,
        refresh_token=account_data.refresh_token
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return {"success": True, "message": "Account connected", "account_id": str(account.id)}


@router.get("/accounts")
async def list_connected_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all connected social media accounts
    """
    accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id
    ).all()

    return {
        "accounts": [
            {
                "id": str(acc.id),
                "platform": acc.platform,
                "account_id": acc.account_id,
                "account_name": acc.account_name,
                "connected_at": acc.created_at.isoformat()
            }
            for acc in accounts
        ]
    }


@router.delete("/accounts/{account_id}")
async def disconnect_social_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a social media account
    """
    account = db.query(SocialAccount).filter(
        SocialAccount.id == account_id,
        SocialAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    db.delete(account)
    db.commit()

    return {"success": True, "message": "Account disconnected"}


@router.get("/auth/facebook/url")
async def get_facebook_auth_url(
    redirect_uri: str = Query(..., description="Redirect URI after authentication"),
    current_user: User = Depends(get_current_user)
):
    """
    Get Facebook OAuth URL for connecting account
    """
    auth_url = social_media_service.get_facebook_auth_url(redirect_uri)

    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Facebook integration not configured"
        )

    return {"auth_url": auth_url}


@router.post("/auth/facebook/callback")
async def facebook_auth_callback(
    code: str = Query(..., description="OAuth code from Facebook"),
    redirect_uri: str = Query(..., description="Redirect URI used in auth"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle Facebook OAuth callback
    """
    token_data = social_media_service.exchange_facebook_code(code, redirect_uri)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange OAuth code"
        )

    access_token = token_data.get("access_token")

    # Get user's Facebook pages
    # This would require additional API calls in production

    return {
        "success": True,
        "message": "Facebook authenticated successfully",
        "access_token": access_token
    }


@router.post("/test-post")
async def test_social_post(
    platforms: List[str],
    content: str,
    current_user: User = Depends(get_current_user)
):
    """
    Test posting without actually posting (simulation mode)
    """
    result = social_media_service.simulate_post(platforms, content)

    return result
