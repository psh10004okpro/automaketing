"""
Analytics and Reporting API routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.activity import Activity

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get overview analytics for dashboard
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total leads
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()

    # New leads in period
    new_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).count()

    # Campaign metrics
    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id,
        Campaign.sent_at >= start_date
    ).all()

    total_sent = sum(c.sent_count for c in campaigns)
    total_opens = sum(c.open_count for c in campaigns)
    total_clicks = sum(c.click_count for c in campaigns)
    total_conversions = sum(c.conversion_count for c in campaigns)

    open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicks / total_sent * 100) if total_sent > 0 else 0
    conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

    # Hot leads
    hot_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 70
    ).count()

    return {
        "period_days": days,
        "leads": {
            "total": total_leads,
            "new": new_leads,
            "hot": hot_leads
        },
        "campaigns": {
            "total_sent": total_sent,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "conversion_rate": round(conversion_rate, 2)
        },
        "engagement": {
            "total_opens": total_opens,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions
        }
    }


@router.get("/campaigns/performance")
async def get_campaign_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get detailed campaign performance metrics
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id,
        Campaign.sent_at >= start_date
    ).order_by(Campaign.sent_at.desc()).all()

    campaign_data = []
    for campaign in campaigns:
        open_rate = (campaign.open_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        click_rate = (campaign.click_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        conversion_rate = (campaign.conversion_count / campaign.click_count * 100) if campaign.click_count > 0 else 0

        campaign_data.append({
            "id": str(campaign.id),
            "name": campaign.name,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "sent_count": campaign.sent_count,
            "open_count": campaign.open_count,
            "click_count": campaign.click_count,
            "conversion_count": campaign.conversion_count,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "conversion_rate": round(conversion_rate, 2)
        })

    return {
        "campaigns": campaign_data,
        "total_campaigns": len(campaign_data)
    }


@router.get("/campaigns/timeline")
async def get_campaign_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get campaign metrics over time for charting
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id,
        Campaign.sent_at >= start_date
    ).order_by(Campaign.sent_at).all()

    # Group by date
    daily_metrics = {}
    for campaign in campaigns:
        if campaign.sent_at:
            date_key = campaign.sent_at.date().isoformat()

            if date_key not in daily_metrics:
                daily_metrics[date_key] = {
                    "date": date_key,
                    "sent": 0,
                    "opens": 0,
                    "clicks": 0,
                    "conversions": 0
                }

            daily_metrics[date_key]["sent"] += campaign.sent_count
            daily_metrics[date_key]["opens"] += campaign.open_count
            daily_metrics[date_key]["clicks"] += campaign.click_count
            daily_metrics[date_key]["conversions"] += campaign.conversion_count

    # Fill in missing dates with zeros
    timeline = []
    current_date = start_date.date()
    end_date = datetime.utcnow().date()

    while current_date <= end_date:
        date_key = current_date.isoformat()
        if date_key in daily_metrics:
            timeline.append(daily_metrics[date_key])
        else:
            timeline.append({
                "date": date_key,
                "sent": 0,
                "opens": 0,
                "clicks": 0,
                "conversions": 0
            })
        current_date += timedelta(days=1)

    return {
        "timeline": timeline,
        "period_days": days
    }


@router.get("/leads/growth")
async def get_leads_growth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get lead growth over time
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get leads created in period
    leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at >= start_date
    ).order_by(Lead.created_at).all()

    # Group by date
    daily_leads = {}
    for lead in leads:
        date_key = lead.created_at.date().isoformat()
        daily_leads[date_key] = daily_leads.get(date_key, 0) + 1

    # Create timeline
    timeline = []
    current_date = start_date.date()
    end_date = datetime.utcnow().date()
    cumulative = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.created_at < start_date
    ).count()

    while current_date <= end_date:
        date_key = current_date.isoformat()
        new_leads = daily_leads.get(date_key, 0)
        cumulative += new_leads

        timeline.append({
            "date": date_key,
            "new_leads": new_leads,
            "total_leads": cumulative
        })

        current_date += timedelta(days=1)

    return {
        "timeline": timeline,
        "period_days": days
    }


@router.get("/activities/recent")
async def get_recent_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, description="Number of activities to return")
):
    """
    Get recent lead activities
    """
    # Get user's leads
    lead_ids = db.query(Lead.id).filter(Lead.user_id == current_user.id).all()
    lead_ids = [lid[0] for lid in lead_ids]

    activities = db.query(Activity).filter(
        Activity.lead_id.in_(lead_ids)
    ).order_by(Activity.timestamp.desc()).limit(limit).all()

    activity_data = []
    for activity in activities:
        lead = db.query(Lead).filter(Lead.id == activity.lead_id).first()
        activity_data.append({
            "id": str(activity.id),
            "type": activity.activity_type,
            "timestamp": activity.timestamp.isoformat(),
            "metadata": activity.metadata,
            "lead": {
                "id": str(lead.id),
                "name": lead.name,
                "email": lead.email
            } if lead else None
        })

    return {
        "activities": activity_data,
        "count": len(activity_data)
    }


@router.get("/engagement/heatmap")
async def get_engagement_heatmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get engagement heatmap by day of week and hour
    """
    # Get activities from last 90 days
    start_date = datetime.utcnow() - timedelta(days=90)

    lead_ids = db.query(Lead.id).filter(Lead.user_id == current_user.id).all()
    lead_ids = [lid[0] for lid in lead_ids]

    activities = db.query(Activity).filter(
        Activity.lead_id.in_(lead_ids),
        Activity.timestamp >= start_date,
        Activity.activity_type.in_(["email_open", "email_click"])
    ).all()

    # Create heatmap data
    heatmap = {}
    for day in range(7):  # 0 = Monday, 6 = Sunday
        heatmap[day] = {hour: 0 for hour in range(24)}

    for activity in activities:
        day = activity.timestamp.weekday()
        hour = activity.timestamp.hour
        heatmap[day][hour] += 1

    # Convert to list format
    heatmap_data = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in range(7):
        for hour in range(24):
            heatmap_data.append({
                "day": day_names[day],
                "hour": hour,
                "engagement": heatmap[day][hour]
            })

    # Find best time
    max_engagement = 0
    best_day = ""
    best_hour = 0

    for day in range(7):
        for hour in range(24):
            if heatmap[day][hour] > max_engagement:
                max_engagement = heatmap[day][hour]
                best_day = day_names[day]
                best_hour = hour

    return {
        "heatmap": heatmap_data,
        "best_time": {
            "day": best_day,
            "hour": best_hour,
            "engagement": max_engagement
        }
    }


@router.get("/insights")
async def get_ai_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered insights and recommendations
    """
    insights = []

    # Analyze campaign performance
    recent_campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id,
        Campaign.sent_at >= datetime.utcnow() - timedelta(days=30)
    ).all()

    if recent_campaigns:
        avg_open_rate = sum(
            (c.open_count / c.sent_count * 100) if c.sent_count > 0 else 0
            for c in recent_campaigns
        ) / len(recent_campaigns)

        if avg_open_rate < 20:
            insights.append({
                "type": "warning",
                "title": "Low Open Rate",
                "message": f"Your average open rate is {avg_open_rate:.1f}%. Try A/B testing subject lines or sending at different times.",
                "priority": "high"
            })
        elif avg_open_rate > 30:
            insights.append({
                "type": "success",
                "title": "Great Open Rate",
                "message": f"Your average open rate of {avg_open_rate:.1f}% is excellent! Keep up the good work.",
                "priority": "low"
            })

    # Check lead engagement
    total_leads = db.query(Lead).filter(Lead.user_id == current_user.id).count()
    hot_leads = db.query(Lead).filter(
        Lead.user_id == current_user.id,
        Lead.score >= 70
    ).count()

    if total_leads > 0:
        hot_percentage = (hot_leads / total_leads) * 100
        if hot_percentage > 20:
            insights.append({
                "type": "success",
                "title": "High Quality Leads",
                "message": f"{hot_percentage:.0f}% of your leads are highly engaged. Consider reaching out with special offers.",
                "priority": "medium"
            })

    # Activity-based insights
    lead_ids = db.query(Lead.id).filter(Lead.user_id == current_user.id).all()
    lead_ids = [lid[0] for lid in lead_ids]

    recent_activities = db.query(Activity).filter(
        Activity.lead_id.in_(lead_ids),
        Activity.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()

    if recent_activities < 10 and total_leads > 50:
        insights.append({
            "type": "warning",
            "title": "Low Recent Activity",
            "message": "Your leads haven't been very active lately. Consider sending a re-engagement campaign.",
            "priority": "medium"
        })

    # Generic tip
    insights.append({
        "type": "tip",
        "title": "Best Practice",
        "message": "Tuesday and Wednesday mornings typically have the highest email open rates. Schedule your campaigns accordingly.",
        "priority": "low"
    })

    return {
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat()
    }
