"""
Email Campaign Service
"""
from typing import List, Dict, Optional
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
from app.models.campaign import Campaign, CampaignStatus
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class EmailCampaignService:
    """Service for managing email campaigns"""

    def __init__(self):
        self.sg_client = None
        if settings.SENDGRID_API_KEY:
            self.sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def create_campaign(
        self,
        db: Session,
        user_id: str,
        name: str,
        subject: str,
        from_email: str,
        from_name: str,
        content: str
    ) -> Campaign:
        """
        Create a new email campaign

        Args:
            db: Database session
            user_id: User ID
            name: Campaign name
            subject: Email subject
            from_email: Sender email
            from_name: Sender name
            content: Email HTML content

        Returns:
            Created campaign object
        """
        campaign = Campaign(
            user_id=user_id,
            name=name,
            subject=subject,
            from_email=from_email,
            from_name=from_name,
            content=content,
            status=CampaignStatus.DRAFT
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        return campaign

    def send_campaign(
        self,
        db: Session,
        campaign_id: str,
        recipients: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Send email campaign to recipients

        Args:
            db: Database session
            campaign_id: Campaign ID
            recipients: List of recipient dicts with 'email' and 'name'

        Returns:
            Dictionary with send results
        """
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if not self.sg_client:
            logger.warning("SendGrid not configured, simulating send")
            return self._simulate_send(db, campaign, recipients)

        campaign.status = CampaignStatus.SENDING
        db.commit()

        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                personalized_content = self._personalize_content(
                    campaign.content,
                    recipient
                )

                message = Mail(
                    from_email=Email(campaign.from_email, campaign.from_name),
                    to_emails=To(recipient['email'], recipient.get('name')),
                    subject=campaign.subject,
                    html_content=Content("text/html", personalized_content)
                )

                response = self.sg_client.send(message)

                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to send to {recipient['email']}: {response.body}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending to {recipient['email']}: {str(e)}")

        # Update campaign stats
        campaign.sent_count = sent_count
        campaign.delivered_count = sent_count  # Assuming delivered = sent for now
        campaign.status = CampaignStatus.SENT
        campaign.sent_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "sent": sent_count,
            "failed": failed_count,
            "total": len(recipients)
        }

    def schedule_campaign(
        self,
        db: Session,
        campaign_id: str,
        scheduled_time: datetime
    ) -> Campaign:
        """
        Schedule a campaign for future sending

        Args:
            db: Database session
            campaign_id: Campaign ID
            scheduled_time: When to send the campaign

        Returns:
            Updated campaign
        """
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        campaign.scheduled_at = scheduled_time
        campaign.status = CampaignStatus.SCHEDULED
        db.commit()

        # TODO: Schedule with Celery
        # send_campaign_task.apply_async(
        #     args=[campaign_id],
        #     eta=scheduled_time
        # )

        return campaign

    def track_open(self, db: Session, campaign_id: str):
        """Track email open event"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.open_count += 1
            db.commit()

    def track_click(self, db: Session, campaign_id: str):
        """Track email click event"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.click_count += 1
            db.commit()

    def track_conversion(self, db: Session, campaign_id: str):
        """Track conversion event"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.conversion_count += 1
            db.commit()

    def _personalize_content(
        self,
        content: str,
        recipient: Dict[str, str]
    ) -> str:
        """
        Personalize email content with recipient data

        Args:
            content: Email HTML content
            recipient: Recipient data dictionary

        Returns:
            Personalized content
        """
        personalized = content

        # Replace common placeholders
        personalized = personalized.replace("{{name}}", recipient.get("name", ""))
        personalized = personalized.replace("{{email}}", recipient.get("email", ""))
        personalized = personalized.replace("{{company}}", recipient.get("company", ""))

        # Add more personalizations as needed
        for key, value in recipient.items():
            personalized = personalized.replace(f"{{{{{key}}}}}", str(value))

        return personalized

    def _simulate_send(
        self,
        db: Session,
        campaign: Campaign,
        recipients: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Simulate sending when SendGrid is not configured

        Args:
            db: Database session
            campaign: Campaign object
            recipients: List of recipients

        Returns:
            Simulated results
        """
        logger.info(f"SIMULATED SEND: Campaign '{campaign.name}' to {len(recipients)} recipients")

        campaign.sent_count = len(recipients)
        campaign.delivered_count = len(recipients)
        campaign.status = CampaignStatus.SENT
        campaign.sent_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "sent": len(recipients),
            "failed": 0,
            "total": len(recipients),
            "simulated": True
        }


# Singleton instance
email_service = EmailCampaignService()
