"""
SMS Campaign Service with Twilio Integration
"""
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.models.sms_campaign import SMSCampaign, SMSCampaignStatus
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Twilio client will be imported only if credentials are available
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio SDK not installed. SMS features will be simulated.")


class SMSCampaignService:
    """Service for managing SMS campaigns"""

    def __init__(self):
        self.twilio_client = None

        if TWILIO_AVAILABLE and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = TwilioClient(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")

    def create_campaign(
        self,
        db: Session,
        user_id: str,
        name: str,
        message: str,
        from_number: Optional[str] = None
    ) -> SMSCampaign:
        """
        Create a new SMS campaign

        Args:
            db: Database session
            user_id: User ID
            name: Campaign name
            message: SMS message content
            from_number: Twilio phone number (optional)

        Returns:
            Created SMS campaign object
        """
        if not from_number:
            from_number = settings.TWILIO_PHONE_NUMBER or "+1234567890"

        campaign = SMSCampaign(
            user_id=user_id,
            name=name,
            message=message,
            from_number=from_number,
            status=SMSCampaignStatus.DRAFT
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
        Send SMS campaign to recipients

        Args:
            db: Database session
            campaign_id: SMS Campaign ID
            recipients: List of recipient dicts with 'phone' and optionally 'name'

        Returns:
            Dictionary with send results
        """
        campaign = db.query(SMSCampaign).filter(SMSCampaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"SMS Campaign {campaign_id} not found")

        if not self.twilio_client:
            logger.warning("Twilio not configured, simulating SMS send")
            return self._simulate_send(db, campaign, recipients)

        campaign.status = SMSCampaignStatus.SENDING
        db.commit()

        sent_count = 0
        delivered_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                phone = recipient.get('phone')
                if not phone:
                    failed_count += 1
                    continue

                # Personalize message
                personalized_message = self._personalize_message(
                    campaign.message,
                    recipient
                )

                # Send via Twilio
                message = self.twilio_client.messages.create(
                    body=personalized_message,
                    from_=campaign.from_number,
                    to=phone
                )

                if message.sid:
                    sent_count += 1
                    if message.status in ['sent', 'delivered']:
                        delivered_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to send SMS to {phone}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending SMS to {recipient.get('phone')}: {str(e)}")

        # Update campaign stats
        campaign.sent_count = sent_count
        campaign.delivered_count = delivered_count
        campaign.failed_count = failed_count
        campaign.status = SMSCampaignStatus.SENT
        campaign.sent_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "sent": sent_count,
            "delivered": delivered_count,
            "failed": failed_count,
            "total": len(recipients)
        }

    def schedule_campaign(
        self,
        db: Session,
        campaign_id: str,
        scheduled_time: datetime
    ) -> SMSCampaign:
        """
        Schedule an SMS campaign for future sending

        Args:
            db: Database session
            campaign_id: SMS Campaign ID
            scheduled_time: When to send the campaign

        Returns:
            Updated campaign
        """
        campaign = db.query(SMSCampaign).filter(SMSCampaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"SMS Campaign {campaign_id} not found")

        campaign.scheduled_at = scheduled_time
        campaign.status = SMSCampaignStatus.SCHEDULED
        db.commit()

        # TODO: Schedule with Celery
        # send_sms_campaign_task.apply_async(
        #     args=[campaign_id],
        #     eta=scheduled_time
        # )

        return campaign

    def get_campaign_status(
        self,
        db: Session,
        campaign_id: str
    ) -> Dict[str, any]:
        """
        Get detailed status of an SMS campaign

        Args:
            db: Database session
            campaign_id: SMS Campaign ID

        Returns:
            Campaign status details
        """
        campaign = db.query(SMSCampaign).filter(SMSCampaign.id == campaign_id).first()

        if not campaign:
            raise ValueError(f"SMS Campaign {campaign_id} not found")

        delivery_rate = 0
        if campaign.sent_count > 0:
            delivery_rate = (campaign.delivered_count / campaign.sent_count) * 100

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "sent_count": campaign.sent_count,
            "delivered_count": campaign.delivered_count,
            "failed_count": campaign.failed_count,
            "delivery_rate": round(delivery_rate, 2),
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "created_at": campaign.created_at.isoformat()
        }

    def _personalize_message(
        self,
        message: str,
        recipient: Dict[str, str]
    ) -> str:
        """
        Personalize SMS message with recipient data

        Args:
            message: SMS message template
            recipient: Recipient data dictionary

        Returns:
            Personalized message
        """
        personalized = message

        # Replace common placeholders
        personalized = personalized.replace("{{name}}", recipient.get("name", ""))
        personalized = personalized.replace("{{phone}}", recipient.get("phone", ""))

        # Add more personalizations as needed
        for key, value in recipient.items():
            personalized = personalized.replace(f"{{{{{key}}}}}", str(value))

        return personalized

    def _simulate_send(
        self,
        db: Session,
        campaign: SMSCampaign,
        recipients: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Simulate sending when Twilio is not configured

        Args:
            db: Database session
            campaign: SMS Campaign object
            recipients: List of recipients

        Returns:
            Simulated results
        """
        logger.info(f"SIMULATED SMS SEND: Campaign '{campaign.name}' to {len(recipients)} recipients")

        # Simulate success for all
        sent_count = len(recipients)
        delivered_count = len(recipients)

        campaign.sent_count = sent_count
        campaign.delivered_count = delivered_count
        campaign.failed_count = 0
        campaign.status = SMSCampaignStatus.SENT
        campaign.sent_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "sent": sent_count,
            "delivered": delivered_count,
            "failed": 0,
            "total": len(recipients),
            "simulated": True
        }

    def validate_phone_number(self, phone: str) -> bool:
        """
        Validate phone number format

        Args:
            phone: Phone number string

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - should start with + and contain only digits
        if not phone or len(phone) < 10:
            return False

        # Remove spaces and dashes
        clean_phone = phone.replace(" ", "").replace("-", "")

        # Should start with + for international format
        if not clean_phone.startswith("+"):
            return False

        # Rest should be digits
        return clean_phone[1:].isdigit()


# Singleton instance
sms_service = SMSCampaignService()
