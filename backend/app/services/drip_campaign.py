"""
Drip Campaign service for automated email/SMS sequences
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.drip_campaign import (
    DripCampaign,
    DripStep,
    DripSubscriber,
    DripSubscriberProgress,
    DripCampaignStatus,
    StepMessageType,
    StepConditionType,
    SubscriberStatus,
)
from app.models.lead import Lead


class DripCampaignService:
    """Service for managing drip campaigns"""

    def create_campaign(
        self,
        db: Session,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        trigger_type: str = "manual",
        trigger_config: Optional[Dict] = None,
        goal: Optional[str] = None,
    ) -> DripCampaign:
        """Create a new drip campaign"""
        campaign = DripCampaign(
            user_id=user_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config=trigger_config or {},
            goal=goal,
            status=DripCampaignStatus.DRAFT,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    def update_campaign(
        self,
        db: Session,
        campaign_id: str,
        **kwargs,
    ) -> DripCampaign:
        """Update campaign details"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        db.commit()
        db.refresh(campaign)
        return campaign

    def add_step(
        self,
        db: Session,
        campaign_id: str,
        name: str,
        message_type: str,
        content: str,
        delay_days: int = 0,
        delay_hours: int = 0,
        delay_minutes: int = 0,
        subject: Optional[str] = None,
        from_name: Optional[str] = None,
        cta_text: Optional[str] = None,
        cta_url: Optional[str] = None,
        condition_type: str = "always",
        step_order: Optional[int] = None,
    ) -> DripStep:
        """Add a new step to the campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        # If step_order not provided, add to end
        if step_order is None:
            max_order = db.query(DripStep).filter(
                DripStep.campaign_id == campaign_id
            ).count()
            step_order = max_order + 1

        step = DripStep(
            campaign_id=campaign_id,
            step_order=step_order,
            name=name,
            message_type=message_type,
            content=content,
            delay_days=delay_days,
            delay_hours=delay_hours,
            delay_minutes=delay_minutes,
            subject=subject,
            from_name=from_name,
            cta_text=cta_text,
            cta_url=cta_url,
            condition_type=condition_type,
        )
        db.add(step)

        # Update campaign total_steps
        campaign.total_steps = campaign.total_steps + 1

        db.commit()
        db.refresh(step)
        return step

    def update_step(
        self,
        db: Session,
        step_id: str,
        **kwargs,
    ) -> DripStep:
        """Update step details"""
        step = db.query(DripStep).filter(DripStep.id == step_id).first()
        if not step:
            raise ValueError("Step not found")

        for key, value in kwargs.items():
            if hasattr(step, key):
                setattr(step, key, value)

        db.commit()
        db.refresh(step)
        return step

    def delete_step(self, db: Session, step_id: str) -> bool:
        """Delete a step"""
        step = db.query(DripStep).filter(DripStep.id == step_id).first()
        if not step:
            return False

        campaign = step.campaign
        db.delete(step)

        # Update campaign total_steps
        campaign.total_steps = max(0, campaign.total_steps - 1)

        # Reorder remaining steps
        remaining_steps = (
            db.query(DripStep)
            .filter(DripStep.campaign_id == campaign.id)
            .order_by(DripStep.step_order)
            .all()
        )
        for idx, s in enumerate(remaining_steps, start=1):
            s.step_order = idx

        db.commit()
        return True

    def reorder_steps(
        self,
        db: Session,
        campaign_id: str,
        step_orders: List[Dict[str, int]],  # [{"step_id": "...", "order": 1}, ...]
    ) -> List[DripStep]:
        """Reorder steps in a campaign"""
        for item in step_orders:
            step = db.query(DripStep).filter(DripStep.id == item["step_id"]).first()
            if step:
                step.step_order = item["order"]

        db.commit()

        # Return all steps in new order
        steps = (
            db.query(DripStep)
            .filter(DripStep.campaign_id == campaign_id)
            .order_by(DripStep.step_order)
            .all()
        )
        return steps

    def enroll_subscriber(
        self,
        db: Session,
        campaign_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        lead_id: Optional[str] = None,
        custom_fields: Optional[Dict] = None,
    ) -> DripSubscriber:
        """Enroll a subscriber in the campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.status != DripCampaignStatus.ACTIVE:
            raise ValueError("Campaign is not active")

        # Check if already enrolled
        existing = (
            db.query(DripSubscriber)
            .filter(
                and_(
                    DripSubscriber.campaign_id == campaign_id,
                    or_(
                        DripSubscriber.email == email,
                        DripSubscriber.lead_id == lead_id,
                    ),
                )
            )
            .first()
        )
        if existing:
            raise ValueError("Subscriber already enrolled")

        # Calculate first send time
        first_step = (
            db.query(DripStep)
            .filter(DripStep.campaign_id == campaign_id)
            .order_by(DripStep.step_order)
            .first()
        )

        next_send_at = None
        if first_step:
            next_send_at = datetime.utcnow() + timedelta(
                days=first_step.delay_days,
                hours=first_step.delay_hours,
                minutes=first_step.delay_minutes,
            )

        subscriber = DripSubscriber(
            campaign_id=campaign_id,
            lead_id=lead_id,
            email=email,
            phone=phone,
            name=name,
            custom_fields=custom_fields or {},
            status=SubscriberStatus.ACTIVE,
            current_step=0,
            next_send_at=next_send_at,
        )
        db.add(subscriber)

        # Update campaign stats
        campaign.total_subscribers += 1
        campaign.active_subscribers += 1

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def unsubscribe(
        self,
        db: Session,
        subscriber_id: str,
    ) -> DripSubscriber:
        """Unsubscribe a subscriber from the campaign"""
        subscriber = (
            db.query(DripSubscriber).filter(DripSubscriber.id == subscriber_id).first()
        )
        if not subscriber:
            raise ValueError("Subscriber not found")

        subscriber.status = SubscriberStatus.UNSUBSCRIBED
        subscriber.unsubscribed_at = datetime.utcnow()

        # Update campaign stats
        campaign = subscriber.campaign
        campaign.active_subscribers = max(0, campaign.active_subscribers - 1)
        campaign.unsubscribed_count += 1

        db.commit()
        db.refresh(subscriber)
        return subscriber

    def check_step_condition(
        self,
        db: Session,
        subscriber: DripSubscriber,
        step: DripStep,
    ) -> bool:
        """
        Check if step condition is met for sending

        Returns:
            True if step should be sent, False if should be skipped
        """
        if step.condition_type == StepConditionType.ALWAYS:
            return True

        # Get previous step
        previous_step = (
            db.query(DripStep)
            .filter(
                and_(
                    DripStep.campaign_id == step.campaign_id,
                    DripStep.step_order == step.step_order - 1,
                )
            )
            .first()
        )

        if not previous_step:
            return True  # No previous step, send this one

        # Get progress for previous step
        previous_progress = (
            db.query(DripSubscriberProgress)
            .filter(
                and_(
                    DripSubscriberProgress.subscriber_id == subscriber.id,
                    DripSubscriberProgress.step_id == previous_step.id,
                )
            )
            .first()
        )

        if not previous_progress:
            return False  # Previous step not sent yet

        # Check conditions
        if step.condition_type == StepConditionType.OPENED_PREVIOUS:
            return previous_progress.opened

        if step.condition_type == StepConditionType.CLICKED_PREVIOUS:
            return previous_progress.clicked

        if step.condition_type == StepConditionType.NOT_OPENED_PREVIOUS:
            return not previous_progress.opened

        if step.condition_type == StepConditionType.NOT_CLICKED_PREVIOUS:
            return not previous_progress.clicked

        return True

    def process_pending_sends(self, db: Session, limit: int = 100) -> int:
        """
        Process subscribers who are due to receive their next message

        This should be called periodically (e.g., every minute) by a background job

        Returns:
            Number of messages processed
        """
        now = datetime.utcnow()

        # Get subscribers due for next message
        subscribers = (
            db.query(DripSubscriber)
            .filter(
                and_(
                    DripSubscriber.status == SubscriberStatus.ACTIVE,
                    DripSubscriber.next_send_at <= now,
                    DripSubscriber.next_send_at.isnot(None),
                )
            )
            .limit(limit)
            .all()
        )

        processed = 0
        for subscriber in subscribers:
            try:
                self._send_next_step(db, subscriber)
                processed += 1
            except Exception as e:
                print(f"Error processing subscriber {subscriber.id}: {str(e)}")
                continue

        db.commit()
        return processed

    def _send_next_step(self, db: Session, subscriber: DripSubscriber):
        """Send the next step to a subscriber"""
        campaign = subscriber.campaign

        # Get next step
        next_step_order = subscriber.current_step + 1
        next_step = (
            db.query(DripStep)
            .filter(
                and_(
                    DripStep.campaign_id == campaign.id,
                    DripStep.step_order == next_step_order,
                )
            )
            .first()
        )

        if not next_step:
            # No more steps, mark as completed
            subscriber.status = SubscriberStatus.COMPLETED
            subscriber.completed_at = datetime.utcnow()
            subscriber.next_send_at = None
            campaign.active_subscribers = max(0, campaign.active_subscribers - 1)
            campaign.completed_subscribers += 1
            return

        # Check condition
        should_send = self.check_step_condition(db, subscriber, next_step)

        # Create progress record
        progress = DripSubscriberProgress(
            subscriber_id=subscriber.id,
            step_id=next_step.id,
            scheduled_at=subscriber.next_send_at,
        )

        if not should_send:
            # Skip this step
            progress.skipped = True
            next_step.skipped_count += 1
            db.add(progress)
        else:
            # Send message (simulated for now)
            # In production, this would integrate with actual email/SMS services
            try:
                # TODO: Integrate with actual sending service
                # For now, mark as sent
                progress.sent = True
                progress.sent_at = datetime.utcnow()
                progress.delivered = True
                progress.delivered_at = datetime.utcnow()

                # Update step stats
                next_step.sent_count += 1
                next_step.delivered_count += 1

                # Update campaign stats
                campaign.total_sent += 1
                campaign.total_delivered += 1

                subscriber.last_sent_at = datetime.utcnow()

                db.add(progress)

            except Exception as e:
                progress.failed = True
                progress.failed_at = datetime.utcnow()
                progress.error_message = str(e)
                next_step.failed_count += 1
                db.add(progress)
                raise

        # Update subscriber progress
        subscriber.current_step = next_step_order

        # Calculate next send time
        following_step = (
            db.query(DripStep)
            .filter(
                and_(
                    DripStep.campaign_id == campaign.id,
                    DripStep.step_order == next_step_order + 1,
                )
            )
            .first()
        )

        if following_step:
            subscriber.next_send_at = datetime.utcnow() + timedelta(
                days=following_step.delay_days,
                hours=following_step.delay_hours,
                minutes=following_step.delay_minutes,
            )
        else:
            subscriber.next_send_at = None

    def activate_campaign(self, db: Session, campaign_id: str) -> DripCampaign:
        """Activate a campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.total_steps == 0:
            raise ValueError("Campaign has no steps")

        campaign.status = DripCampaignStatus.ACTIVE
        campaign.started_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def pause_campaign(self, db: Session, campaign_id: str) -> DripCampaign:
        """Pause a campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        campaign.status = DripCampaignStatus.PAUSED
        campaign.paused_at = datetime.utcnow()

        db.commit()
        db.refresh(campaign)
        return campaign

    def get_campaign(self, db: Session, campaign_id: str) -> Optional[DripCampaign]:
        """Get a campaign with all steps"""
        return db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()

    def list_campaigns(
        self,
        db: Session,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[DripCampaign]:
        """List campaigns for a user"""
        query = db.query(DripCampaign).filter(DripCampaign.user_id == user_id)

        if status:
            query = query.filter(DripCampaign.status == status)

        return query.order_by(DripCampaign.created_at.desc()).all()

    def get_campaign_stats(self, db: Session, campaign_id: str) -> Dict:
        """Get detailed statistics for a campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            raise ValueError("Campaign not found")

        # Calculate rates
        open_rate = (
            (campaign.total_opens / campaign.total_delivered * 100)
            if campaign.total_delivered > 0
            else 0
        )
        click_rate = (
            (campaign.total_clicks / campaign.total_delivered * 100)
            if campaign.total_delivered > 0
            else 0
        )
        completion_rate = (
            (campaign.completed_subscribers / campaign.total_subscribers * 100)
            if campaign.total_subscribers > 0
            else 0
        )

        # Get step-by-step breakdown
        steps_stats = []
        for step in campaign.steps:
            step_open_rate = (
                (step.opened_count / step.delivered_count * 100)
                if step.delivered_count > 0
                else 0
            )
            step_click_rate = (
                (step.clicked_count / step.delivered_count * 100)
                if step.delivered_count > 0
                else 0
            )

            steps_stats.append({
                "step_order": step.step_order,
                "name": step.name,
                "sent": step.sent_count,
                "delivered": step.delivered_count,
                "opened": step.opened_count,
                "clicked": step.clicked_count,
                "failed": step.failed_count,
                "skipped": step.skipped_count,
                "open_rate": round(step_open_rate, 1),
                "click_rate": round(step_click_rate, 1),
            })

        return {
            "total_subscribers": campaign.total_subscribers,
            "active_subscribers": campaign.active_subscribers,
            "completed_subscribers": campaign.completed_subscribers,
            "unsubscribed_count": campaign.unsubscribed_count,
            "total_sent": campaign.total_sent,
            "total_delivered": campaign.total_delivered,
            "total_opens": campaign.total_opens,
            "total_clicks": campaign.total_clicks,
            "open_rate": round(open_rate, 1),
            "click_rate": round(click_rate, 1),
            "completion_rate": round(completion_rate, 1),
            "steps": steps_stats,
        }

    def delete_campaign(self, db: Session, campaign_id: str) -> bool:
        """Delete a campaign"""
        campaign = db.query(DripCampaign).filter(DripCampaign.id == campaign_id).first()
        if not campaign:
            return False

        db.delete(campaign)
        db.commit()
        return True


# Singleton instance
drip_campaign_service = DripCampaignService()
