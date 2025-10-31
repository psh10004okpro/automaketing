"""
AI Content Generation API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from app.api.auth import get_current_user
from app.models.user import User
from app.services.ai_content_generator import ai_generator
from app.api.schemas import (
    AIContentRequest,
    AIContentResponse,
    SubjectLineOptimizeRequest,
    SubjectLineOptimizeResponse
)

router = APIRouter()


@router.post("/generate", response_model=AIContentResponse)
async def generate_content(
    request: AIContentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate marketing content using AI

    This endpoint uses OpenAI or Anthropic to generate marketing content
    based on the provided parameters.
    """
    try:
        content = ai_generator.generate_content(
            content_type=request.content_type,
            target_audience=request.target_audience,
            main_message=request.main_message,
            tone=request.tone,
            platform=request.platform
        )

        return AIContentResponse(
            content=content,
            metadata={
                "content_type": request.content_type,
                "platform": request.platform,
                "tone": request.tone
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.post("/optimize-subject", response_model=SubjectLineOptimizeResponse)
async def optimize_subject_line(
    request: SubjectLineOptimizeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Optimize email subject line using AI

    Returns 3 improved versions of the subject line along with analysis.
    """
    try:
        result = ai_generator.optimize_subject_line(request.subject_line)

        return SubjectLineOptimizeResponse(
            suggestions=result.get("suggestions", []),
            analysis=result.get("analysis", "")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/social-captions")
async def generate_social_captions(
    topic: str,
    platform: str,
    count: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Generate multiple social media captions

    Args:
        topic: Topic or theme
        platform: Social platform (facebook, instagram, twitter)
        count: Number of captions to generate (default: 3)
    """
    try:
        captions = ai_generator.generate_social_captions(
            topic=topic,
            platform=platform,
            count=count
        )

        return {
            "captions": captions,
            "platform": platform,
            "count": len(captions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")
