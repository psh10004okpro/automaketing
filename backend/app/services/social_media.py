"""
Social Media Management Service
Facebook, Instagram, Twitter/X posting
"""
from typing import List, Dict, Optional
from datetime import datetime
import requests
import logging
from app.core.config import settings
from app.models.scheduled_post import ScheduledPost, PostStatus
from app.models.social_account import SocialAccount
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SocialMediaService:
    """Service for managing social media posts across platforms"""

    def __init__(self):
        self.facebook_app_id = settings.FACEBOOK_APP_ID
        self.facebook_app_secret = settings.FACEBOOK_APP_SECRET

    def post_to_facebook(
        self,
        access_token: str,
        page_id: str,
        content: str,
        image_url: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Post content to Facebook page

        Args:
            access_token: Facebook page access token
            page_id: Facebook page ID
            content: Post content/message
            image_url: Optional image URL

        Returns:
            Post result dictionary
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

            data = {
                "message": content,
                "access_token": access_token
            }

            if image_url:
                data["link"] = image_url

            response = requests.post(url, data=data, timeout=30)

            if response.status_code == 200:
                post_data = response.json()
                return {
                    "success": True,
                    "post_id": post_data.get("id"),
                    "platform": "facebook"
                }
            else:
                logger.error(f"Facebook post failed: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "platform": "facebook"
                }

        except Exception as e:
            logger.error(f"Facebook post exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "facebook"
            }

    def post_to_instagram(
        self,
        access_token: str,
        instagram_account_id: str,
        content: str,
        image_url: str
    ) -> Dict[str, any]:
        """
        Post content to Instagram (requires image)

        Args:
            access_token: Instagram access token
            instagram_account_id: Instagram business account ID
            content: Post caption
            image_url: Image URL (required for Instagram)

        Returns:
            Post result dictionary
        """
        if not image_url:
            return {
                "success": False,
                "error": "Instagram requires an image",
                "platform": "instagram"
            }

        try:
            # Step 1: Create media container
            container_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
            container_data = {
                "image_url": image_url,
                "caption": content,
                "access_token": access_token
            }

            container_response = requests.post(container_url, data=container_data, timeout=30)

            if container_response.status_code != 200:
                logger.error(f"Instagram container creation failed: {container_response.text}")
                return {
                    "success": False,
                    "error": container_response.text,
                    "platform": "instagram"
                }

            creation_id = container_response.json().get("id")

            # Step 2: Publish media
            publish_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
            publish_data = {
                "creation_id": creation_id,
                "access_token": access_token
            }

            publish_response = requests.post(publish_url, data=publish_data, timeout=30)

            if publish_response.status_code == 200:
                post_data = publish_response.json()
                return {
                    "success": True,
                    "post_id": post_data.get("id"),
                    "platform": "instagram"
                }
            else:
                logger.error(f"Instagram publish failed: {publish_response.text}")
                return {
                    "success": False,
                    "error": publish_response.text,
                    "platform": "instagram"
                }

        except Exception as e:
            logger.error(f"Instagram post exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram"
            }

    def post_to_twitter(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        content: str,
        image_url: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Post content to Twitter/X

        Note: Twitter API v2 requires OAuth 2.0 and different approach
        This is a simplified version

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_secret: Twitter access secret
            content: Tweet content
            image_url: Optional image URL

        Returns:
            Post result dictionary
        """
        try:
            # For production, use tweepy or similar library
            # This is a simplified simulation
            logger.info(f"SIMULATED Twitter post: {content[:50]}...")

            return {
                "success": True,
                "post_id": f"twitter_{datetime.now().timestamp()}",
                "platform": "twitter",
                "simulated": True
            }

        except Exception as e:
            logger.error(f"Twitter post exception: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "platform": "twitter"
            }

    def create_scheduled_post(
        self,
        db: Session,
        user_id: str,
        platforms: List[str],
        content: str,
        image_url: Optional[str],
        scheduled_time: datetime
    ) -> ScheduledPost:
        """
        Create a scheduled post

        Args:
            db: Database session
            user_id: User ID
            platforms: List of platforms to post to
            content: Post content
            image_url: Optional image URL
            scheduled_time: When to post

        Returns:
            Created ScheduledPost object
        """
        post = ScheduledPost(
            user_id=user_id,
            platforms=platforms,
            content=content,
            image_url=image_url,
            scheduled_time=scheduled_time,
            status=PostStatus.SCHEDULED
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        # TODO: Schedule with Celery
        # publish_scheduled_post.apply_async(
        #     args=[str(post.id)],
        #     eta=scheduled_time
        # )

        return post

    def publish_post(
        self,
        db: Session,
        post_id: str
    ) -> Dict[str, any]:
        """
        Publish a scheduled post immediately

        Args:
            db: Database session
            post_id: Scheduled post ID

        Returns:
            Publish results
        """
        post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()

        if not post:
            raise ValueError(f"Post {post_id} not found")

        post.status = PostStatus.PUBLISHING
        db.commit()

        results = []

        # Get user's social accounts
        social_accounts = db.query(SocialAccount).filter(
            SocialAccount.user_id == post.user_id
        ).all()

        # Create a map of platforms to accounts
        account_map = {acc.platform: acc for acc in social_accounts}

        for platform in post.platforms:
            if platform not in account_map:
                results.append({
                    "platform": platform,
                    "success": False,
                    "error": f"No {platform} account connected"
                })
                continue

            account = account_map[platform]

            if platform == "facebook":
                result = self.post_to_facebook(
                    access_token=account.access_token,
                    page_id=account.account_id,
                    content=post.content,
                    image_url=post.image_url
                )
            elif platform == "instagram":
                result = self.post_to_instagram(
                    access_token=account.access_token,
                    instagram_account_id=account.account_id,
                    content=post.content,
                    image_url=post.image_url
                )
            elif platform == "twitter":
                # Note: Twitter credentials would be stored differently
                result = self.post_to_twitter(
                    api_key="",  # Would come from settings
                    api_secret="",
                    access_token=account.access_token,
                    access_secret="",  # Would need separate storage
                    content=post.content,
                    image_url=post.image_url
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported platform: {platform}",
                    "platform": platform
                }

            results.append(result)

        # Update post status
        all_successful = all(r.get("success", False) for r in results)
        post.status = PostStatus.PUBLISHED if all_successful else PostStatus.FAILED
        post.published_at = datetime.utcnow()
        db.commit()

        return {
            "post_id": str(post.id),
            "results": results,
            "all_successful": all_successful
        }

    def simulate_post(
        self,
        platforms: List[str],
        content: str
    ) -> Dict[str, any]:
        """
        Simulate posting for demo purposes

        Args:
            platforms: List of platforms
            content: Post content

        Returns:
            Simulated results
        """
        logger.info(f"SIMULATED POST to {', '.join(platforms)}: {content[:50]}...")

        results = []
        for platform in platforms:
            results.append({
                "success": True,
                "post_id": f"{platform}_{datetime.now().timestamp()}",
                "platform": platform,
                "simulated": True
            })

        return {
            "results": results,
            "all_successful": True,
            "simulated": True
        }

    def get_facebook_auth_url(self, redirect_uri: str) -> str:
        """
        Get Facebook OAuth URL for authentication

        Args:
            redirect_uri: Where to redirect after authentication

        Returns:
            Facebook OAuth URL
        """
        if not self.facebook_app_id:
            return ""

        permissions = "pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish"

        auth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={self.facebook_app_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={permissions}&"
            f"response_type=code"
        )

        return auth_url

    def exchange_facebook_code(
        self,
        code: str,
        redirect_uri: str
    ) -> Optional[Dict[str, str]]:
        """
        Exchange Facebook OAuth code for access token

        Args:
            code: OAuth code from Facebook
            redirect_uri: Redirect URI used in auth

        Returns:
            Dictionary with access_token or None
        """
        try:
            url = "https://graph.facebook.com/v18.0/oauth/access_token"

            params = {
                "client_id": self.facebook_app_id,
                "client_secret": self.facebook_app_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Facebook token exchange failed: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Facebook token exchange exception: {str(e)}")
            return None


# Singleton instance
social_media_service = SocialMediaService()
