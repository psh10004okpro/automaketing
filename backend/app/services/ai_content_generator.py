"""
AI Content Generator Service
"""
from typing import Optional, List, Dict
import json
from openai import OpenAI
from anthropic import Anthropic
from app.core.config import settings


class AIContentGenerator:
    """Service for generating marketing content using AI"""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None

        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate_content(
        self,
        content_type: str,
        target_audience: str,
        main_message: str,
        tone: str,
        platform: str = "openai"
    ) -> str:
        """
        Generate marketing content using AI

        Args:
            content_type: Type of content (email, social, blog, ad)
            target_audience: Target audience description
            main_message: Main message to convey
            tone: Tone of the content (professional, friendly, humorous)
            platform: AI platform to use (openai or anthropic)

        Returns:
            Generated content as string
        """
        prompt = f"""You are an expert marketing copywriter.

Content Type: {content_type}
Target Audience: {target_audience}
Main Message: {main_message}
Tone: {tone}

Based on the above information, create effective marketing content that is:
- Clear and persuasive
- Includes a strong call-to-action (CTA)
- Uses appropriate emojis sparingly
- Optimized for {content_type}

Write only the content, no explanations."""

        if platform == "openai" and self.openai_client:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert marketing copywriter."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content

        elif platform == "anthropic" and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        else:
            # Fallback if no API key is configured
            return self._generate_fallback_content(content_type, main_message)

    def optimize_subject_line(self, subject_line: str) -> Dict[str, any]:
        """
        Optimize email subject line using AI

        Args:
            subject_line: Original subject line

        Returns:
            Dictionary with suggestions and analysis
        """
        prompt = f"""Analyze this email subject line and provide 3 improved versions:

Original: {subject_line}

Each suggestion should:
1. Be shorter and more impactful
2. Create curiosity
3. Include personalization elements where appropriate

Respond in JSON format:
{{
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
    "analysis": "Brief analysis of the original and improvements"
}}"""

        if self.openai_client:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        elif self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON from response
            try:
                return json.loads(response.content[0].text)
            except:
                return {
                    "suggestions": [subject_line],
                    "analysis": "Could not generate suggestions"
                }

        return {
            "suggestions": [subject_line],
            "analysis": "AI service not configured"
        }

    def generate_social_captions(
        self,
        topic: str,
        platform: str,
        count: int = 3
    ) -> List[str]:
        """
        Generate multiple social media captions

        Args:
            topic: Topic or theme
            platform: Social platform (facebook, instagram, twitter)
            count: Number of captions to generate

        Returns:
            List of caption suggestions
        """
        platform_specs = {
            "facebook": "engaging, conversational, 100-150 words",
            "instagram": "short, hashtag-friendly, emoji-rich, under 125 characters",
            "twitter": "concise, witty, under 280 characters"
        }

        spec = platform_specs.get(platform, "engaging and appropriate")

        prompt = f"""Generate {count} different {platform} captions about: {topic}

Each caption should be {spec}.

Return only the captions, numbered 1-{count}, no additional explanation."""

        if self.openai_client:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )

            content = response.choices[0].message.content
            # Split by numbers
            captions = [c.strip() for c in content.split('\n') if c.strip() and not c.strip()[0].isdigit()]
            return captions[:count]

        return [f"Sample caption for {topic}"]

    def _generate_fallback_content(self, content_type: str, message: str) -> str:
        """
        Generate basic content when AI is not available

        Args:
            content_type: Type of content
            message: Main message

        Returns:
            Basic formatted content
        """
        templates = {
            "email": f"""Subject: {message}

Hi there!

{message}

We're excited to share this with you.

Best regards,
The Team""",
            "social": f"🚀 {message}\n\nLearn more and join us today!",
            "blog": f"# {message}\n\n{message}\n\nRead more to discover how this can benefit you.",
            "ad": f"{message}\n\n✨ Limited time offer - Act now!"
        }

        return templates.get(content_type, message)


# Singleton instance
ai_generator = AIContentGenerator()
