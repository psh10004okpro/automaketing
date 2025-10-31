"""
Advanced Reporting service for data analysis and insights
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.report import Report, ReportExecution, ReportType, DateRangeType
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.sms_campaign import SMSCampaign
from app.models.ab_test import ABTest
from app.models.drip_campaign import DripCampaign


class ReportingService:
    """Service for advanced reporting and analytics"""

    def create_report(
        self,
        db: Session,
        user_id: str,
        name: str,
        report_type: str,
        config: Dict,
        date_range_type: str = "last_30_days",
        custom_start_date: Optional[datetime] = None,
        custom_end_date: Optional[datetime] = None,
        compare_enabled: bool = False,
        compare_period: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Report:
        """Create a new custom report"""
        report = Report(
            user_id=user_id,
            name=name,
            description=description,
            report_type=report_type,
            config=config,
            date_range_type=date_range_type,
            custom_start_date=custom_start_date,
            custom_end_date=custom_end_date,
            compare_enabled=compare_enabled,
            compare_period=compare_period,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def get_date_range(
        self,
        date_range_type: str,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None,
    ) -> Tuple[datetime, datetime]:
        """Calculate date range based on type"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if date_range_type == DateRangeType.TODAY.value:
            return today_start, now

        elif date_range_type == DateRangeType.YESTERDAY.value:
            yesterday_start = today_start - timedelta(days=1)
            yesterday_end = today_start
            return yesterday_start, yesterday_end

        elif date_range_type == DateRangeType.LAST_7_DAYS.value:
            start = today_start - timedelta(days=7)
            return start, now

        elif date_range_type == DateRangeType.LAST_30_DAYS.value:
            start = today_start - timedelta(days=30)
            return start, now

        elif date_range_type == DateRangeType.LAST_90_DAYS.value:
            start = today_start - timedelta(days=90)
            return start, now

        elif date_range_type == DateRangeType.THIS_MONTH.value:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return month_start, now

        elif date_range_type == DateRangeType.LAST_MONTH.value:
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = month_start
            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            return last_month_start, last_month_end

        elif date_range_type == DateRangeType.THIS_YEAR.value:
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return year_start, now

        elif date_range_type == DateRangeType.CUSTOM.value:
            if custom_start and custom_end:
                return custom_start, custom_end

        # Default to last 30 days
        start = today_start - timedelta(days=30)
        return start, now

    def get_comparison_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        compare_period: str,
    ) -> Tuple[datetime, datetime]:
        """Calculate comparison date range"""
        duration = end_date - start_date

        if compare_period == "previous_period":
            comp_end = start_date
            comp_start = comp_end - duration
            return comp_start, comp_end

        elif compare_period == "previous_year":
            comp_start = start_date - timedelta(days=365)
            comp_end = end_date - timedelta(days=365)
            return comp_start, comp_end

        elif compare_period == "previous_month":
            # Go back one month
            comp_end = start_date
            comp_start = comp_end - timedelta(days=30)
            return comp_start, comp_end

        return start_date, end_date

    def generate_campaign_performance_report(
        self,
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate campaign performance report"""
        # Email campaigns
        email_campaigns = (
            db.query(Campaign)
            .filter(
                and_(
                    Campaign.user_id == user_id,
                    Campaign.created_at >= start_date,
                    Campaign.created_at <= end_date,
                )
            )
            .all()
        )

        # SMS campaigns
        sms_campaigns = (
            db.query(SMSCampaign)
            .filter(
                and_(
                    SMSCampaign.user_id == user_id,
                    SMSCampaign.created_at >= start_date,
                    SMSCampaign.created_at <= end_date,
                )
            )
            .all()
        )

        # Calculate metrics
        total_sent = sum(c.sent_count or 0 for c in email_campaigns) + sum(
            c.sent_count or 0 for c in sms_campaigns
        )
        total_delivered = sum(c.delivered_count or 0 for c in email_campaigns) + sum(
            c.delivered_count or 0 for c in sms_campaigns
        )
        total_opens = sum(c.opened_count or 0 for c in email_campaigns)
        total_clicks = sum(c.clicked_count or 0 for c in email_campaigns)

        # Calculate rates
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        open_rate = (total_opens / total_delivered * 100) if total_delivered > 0 else 0
        click_rate = (total_clicks / total_delivered * 100) if total_delivered > 0 else 0

        # Campaign list
        campaigns_data = []
        for campaign in email_campaigns:
            campaigns_data.append({
                "id": str(campaign.id),
                "name": campaign.name,
                "type": "email",
                "sent": campaign.sent_count or 0,
                "delivered": campaign.delivered_count or 0,
                "opens": campaign.opened_count or 0,
                "clicks": campaign.clicked_count or 0,
                "open_rate": (campaign.opened_count / campaign.delivered_count * 100)
                if campaign.delivered_count
                else 0,
                "click_rate": (campaign.clicked_count / campaign.delivered_count * 100)
                if campaign.delivered_count
                else 0,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            })

        for campaign in sms_campaigns:
            campaigns_data.append({
                "id": str(campaign.id),
                "name": campaign.name,
                "type": "sms",
                "sent": campaign.sent_count or 0,
                "delivered": campaign.delivered_count or 0,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            })

        return {
            "summary": {
                "total_campaigns": len(email_campaigns) + len(sms_campaigns),
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_opens": total_opens,
                "total_clicks": total_clicks,
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
            },
            "campaigns": campaigns_data,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def generate_channel_comparison_report(
        self,
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate channel comparison report"""
        # Email stats
        email_campaigns = (
            db.query(Campaign)
            .filter(
                and_(
                    Campaign.user_id == user_id,
                    Campaign.created_at >= start_date,
                    Campaign.created_at <= end_date,
                )
            )
            .all()
        )

        email_sent = sum(c.sent_count or 0 for c in email_campaigns)
        email_delivered = sum(c.delivered_count or 0 for c in email_campaigns)
        email_opens = sum(c.opened_count or 0 for c in email_campaigns)
        email_clicks = sum(c.clicked_count or 0 for c in email_campaigns)

        # SMS stats
        sms_campaigns = (
            db.query(SMSCampaign)
            .filter(
                and_(
                    SMSCampaign.user_id == user_id,
                    SMSCampaign.created_at >= start_date,
                    SMSCampaign.created_at <= end_date,
                )
            )
            .all()
        )

        sms_sent = sum(c.sent_count or 0 for c in sms_campaigns)
        sms_delivered = sum(c.delivered_count or 0 for c in sms_campaigns)

        # Drip campaigns
        drip_campaigns = (
            db.query(DripCampaign)
            .filter(
                and_(
                    DripCampaign.user_id == user_id,
                    DripCampaign.created_at >= start_date,
                    DripCampaign.created_at <= end_date,
                )
            )
            .all()
        )

        drip_sent = sum(c.total_sent or 0 for c in drip_campaigns)
        drip_delivered = sum(c.total_delivered or 0 for c in drip_campaigns)
        drip_opens = sum(c.total_opens or 0 for c in drip_campaigns)
        drip_clicks = sum(c.total_clicks or 0 for c in drip_campaigns)

        return {
            "channels": [
                {
                    "name": "Email",
                    "sent": email_sent,
                    "delivered": email_delivered,
                    "opens": email_opens,
                    "clicks": email_clicks,
                    "delivery_rate": (email_delivered / email_sent * 100) if email_sent > 0 else 0,
                    "open_rate": (email_opens / email_delivered * 100)
                    if email_delivered > 0
                    else 0,
                    "click_rate": (email_clicks / email_delivered * 100)
                    if email_delivered > 0
                    else 0,
                },
                {
                    "name": "SMS",
                    "sent": sms_sent,
                    "delivered": sms_delivered,
                    "delivery_rate": (sms_delivered / sms_sent * 100) if sms_sent > 0 else 0,
                },
                {
                    "name": "Drip Campaigns",
                    "sent": drip_sent,
                    "delivered": drip_delivered,
                    "opens": drip_opens,
                    "clicks": drip_clicks,
                    "delivery_rate": (drip_delivered / drip_sent * 100) if drip_sent > 0 else 0,
                    "open_rate": (drip_opens / drip_delivered * 100)
                    if drip_delivered > 0
                    else 0,
                    "click_rate": (drip_clicks / drip_delivered * 100)
                    if drip_delivered > 0
                    else 0,
                },
            ],
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def generate_lead_analytics_report(
        self,
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate lead analytics report"""
        # New leads in period
        new_leads = (
            db.query(Lead)
            .filter(
                and_(
                    Lead.user_id == user_id,
                    Lead.created_at >= start_date,
                    Lead.created_at <= end_date,
                )
            )
            .all()
        )

        # All leads for the user
        total_leads = db.query(Lead).filter(Lead.user_id == user_id).count()

        # Leads by status
        status_breakdown = {}
        for lead in new_leads:
            status = lead.status.value if lead.status else "new"
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        # Leads by source
        source_breakdown = {}
        for lead in new_leads:
            source = lead.source or "unknown"
            source_breakdown[source] = source_breakdown.get(source, 0) + 1

        # Average score
        avg_score = sum(lead.score for lead in new_leads) / len(new_leads) if new_leads else 0

        # Score distribution
        score_ranges = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0,
        }
        for lead in new_leads:
            score = lead.score
            if score <= 20:
                score_ranges["0-20"] += 1
            elif score <= 40:
                score_ranges["21-40"] += 1
            elif score <= 60:
                score_ranges["41-60"] += 1
            elif score <= 80:
                score_ranges["61-80"] += 1
            else:
                score_ranges["81-100"] += 1

        return {
            "summary": {
                "total_leads": total_leads,
                "new_leads": len(new_leads),
                "average_score": round(avg_score, 2),
            },
            "status_breakdown": status_breakdown,
            "source_breakdown": source_breakdown,
            "score_distribution": score_ranges,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def generate_engagement_metrics_report(
        self,
        db: Session,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict:
        """Generate engagement metrics report"""
        # Get all campaigns
        campaigns = (
            db.query(Campaign)
            .filter(
                and_(
                    Campaign.user_id == user_id,
                    Campaign.created_at >= start_date,
                    Campaign.created_at <= end_date,
                )
            )
            .all()
        )

        total_sent = sum(c.sent_count or 0 for c in campaigns)
        total_delivered = sum(c.delivered_count or 0 for c in campaigns)
        total_opens = sum(c.opened_count or 0 for c in campaigns)
        total_clicks = sum(c.clicked_count or 0 for c in campaigns)
        total_unsubscribes = sum(c.unsubscribed_count or 0 for c in campaigns)

        # Calculate engagement rates
        open_rate = (total_opens / total_delivered * 100) if total_delivered > 0 else 0
        click_rate = (total_clicks / total_delivered * 100) if total_delivered > 0 else 0
        unsubscribe_rate = (total_unsubscribes / total_delivered * 100) if total_delivered > 0 else 0
        click_to_open_rate = (total_clicks / total_opens * 100) if total_opens > 0 else 0

        # Timeline data (daily aggregation)
        timeline = self._generate_timeline_data(campaigns, start_date, end_date)

        return {
            "summary": {
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_opens": total_opens,
                "total_clicks": total_clicks,
                "total_unsubscribes": total_unsubscribes,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "unsubscribe_rate": round(unsubscribe_rate, 2),
                "click_to_open_rate": round(click_to_open_rate, 2),
            },
            "timeline": timeline,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def _generate_timeline_data(
        self,
        campaigns: List[Campaign],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Generate daily timeline data"""
        # Group campaigns by date
        daily_data = {}
        current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        while current <= end_date:
            date_key = current.strftime("%Y-%m-%d")
            daily_data[date_key] = {
                "date": date_key,
                "sent": 0,
                "delivered": 0,
                "opens": 0,
                "clicks": 0,
            }
            current += timedelta(days=1)

        # Aggregate campaign data by date
        for campaign in campaigns:
            if campaign.created_at:
                date_key = campaign.created_at.strftime("%Y-%m-%d")
                if date_key in daily_data:
                    daily_data[date_key]["sent"] += campaign.sent_count or 0
                    daily_data[date_key]["delivered"] += campaign.delivered_count or 0
                    daily_data[date_key]["opens"] += campaign.opened_count or 0
                    daily_data[date_key]["clicks"] += campaign.clicked_count or 0

        return list(daily_data.values())

    def execute_report(
        self,
        db: Session,
        report: Report,
    ) -> ReportExecution:
        """Execute a report and save the results"""
        start_time = datetime.utcnow()

        # Get date range
        start_date, end_date = self.get_date_range(
            report.date_range_type.value,
            report.custom_start_date,
            report.custom_end_date,
        )

        # Generate report data based on type
        results_data = None
        comparison_data = None

        if report.report_type == ReportType.CAMPAIGN_PERFORMANCE:
            results_data = self.generate_campaign_performance_report(
                db, str(report.user_id), start_date, end_date
            )
        elif report.report_type == ReportType.CHANNEL_COMPARISON:
            results_data = self.generate_channel_comparison_report(
                db, str(report.user_id), start_date, end_date
            )
        elif report.report_type == ReportType.LEAD_ANALYTICS:
            results_data = self.generate_lead_analytics_report(
                db, str(report.user_id), start_date, end_date
            )
        elif report.report_type == ReportType.ENGAGEMENT_METRICS:
            results_data = self.generate_engagement_metrics_report(
                db, str(report.user_id), start_date, end_date
            )

        # Generate comparison data if enabled
        if report.compare_enabled and report.compare_period:
            comp_start, comp_end = self.get_comparison_date_range(
                start_date, end_date, report.compare_period
            )

            if report.report_type == ReportType.CAMPAIGN_PERFORMANCE:
                comparison_data = self.generate_campaign_performance_report(
                    db, str(report.user_id), comp_start, comp_end
                )
            elif report.report_type == ReportType.CHANNEL_COMPARISON:
                comparison_data = self.generate_channel_comparison_report(
                    db, str(report.user_id), comp_start, comp_end
                )
            elif report.report_type == ReportType.LEAD_ANALYTICS:
                comparison_data = self.generate_lead_analytics_report(
                    db, str(report.user_id), comp_start, comp_end
                )
            elif report.report_type == ReportType.ENGAGEMENT_METRICS:
                comparison_data = self.generate_engagement_metrics_report(
                    db, str(report.user_id), comp_start, comp_end
                )

        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Create execution record
        execution = ReportExecution(
            report_id=report.id,
            executed_at=end_time,
            execution_time_ms=execution_time_ms,
            start_date=start_date,
            end_date=end_date,
            results_data=results_data,
            comparison_data=comparison_data,
            status="completed",
        )
        db.add(execution)

        # Update report last run
        report.last_run_at = end_time

        db.commit()
        db.refresh(execution)

        return execution

    def list_reports(
        self,
        db: Session,
        user_id: str,
        report_type: Optional[str] = None,
    ) -> List[Report]:
        """List reports for a user"""
        query = db.query(Report).filter(Report.user_id == user_id)

        if report_type:
            query = query.filter(Report.report_type == report_type)

        return query.order_by(Report.created_at.desc()).all()

    def get_report(self, db: Session, report_id: str) -> Optional[Report]:
        """Get a single report"""
        return db.query(Report).filter(Report.id == report_id).first()

    def delete_report(self, db: Session, report_id: str) -> bool:
        """Delete a report"""
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return False

        db.delete(report)
        db.commit()
        return True


# Singleton instance
reporting_service = ReportingService()
