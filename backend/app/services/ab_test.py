"""
A/B Test service for campaign optimization
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.ab_test import ABTest, ABTestStatus, WinnerMetric, ABTestType
from app.models.campaign import Campaign
from app.models.sms_campaign import SMSCampaign


class ABTestService:
    """Service for managing A/B tests"""

    def create_test(
        self,
        db: Session,
        user_id: str,
        name: str,
        test_type: str,
        variant_a: Dict,
        variant_b: Dict,
        test_percentage: float = 20.0,
        variant_split: float = 50.0,
        winner_metric: str = "open_rate",
        wait_time_hours: int = 24,
        auto_send_winner: bool = True,
        description: Optional[str] = None,
    ) -> ABTest:
        """Create a new A/B test"""
        ab_test = ABTest(
            user_id=user_id,
            name=name,
            description=description,
            type=test_type,
            variant_a=variant_a,
            variant_b=variant_b,
            test_percentage=test_percentage,
            variant_split=variant_split,
            winner_metric=winner_metric,
            wait_time_hours=wait_time_hours,
            auto_send_winner=auto_send_winner,
            status=ABTestStatus.DRAFT,
        )
        db.add(ab_test)
        db.commit()
        db.refresh(ab_test)
        return ab_test

    def start_test(
        self,
        db: Session,
        test_id: str,
        all_recipients: List[str],
    ) -> ABTest:
        """
        Start an A/B test by splitting recipients

        Args:
            db: Database session
            test_id: A/B test ID
            all_recipients: List of all recipient IDs

        Returns:
            Updated ABTest object
        """
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            raise ValueError("A/B test not found")

        if ab_test.status != ABTestStatus.DRAFT:
            raise ValueError("Test already started")

        # Calculate recipient counts
        total_count = len(all_recipients)
        test_count = int(total_count * (ab_test.test_percentage / 100))

        # Randomly select test recipients
        random.shuffle(all_recipients)
        test_recipients = all_recipients[:test_count]
        remaining_recipients = all_recipients[test_count:]

        # Split test recipients into A and B
        variant_a_count = int(len(test_recipients) * (ab_test.variant_split / 100))
        variant_a_recipients = test_recipients[:variant_a_count]
        variant_b_recipients = test_recipients[variant_a_count:]

        # Store recipient lists
        ab_test.test_recipients = {
            "variant_a": variant_a_recipients,
            "variant_b": variant_b_recipients,
        }
        ab_test.remaining_recipients = remaining_recipients
        ab_test.status = ABTestStatus.RUNNING
        ab_test.started_at = datetime.utcnow()

        db.commit()
        db.refresh(ab_test)

        return ab_test

    def update_metrics(
        self,
        db: Session,
        test_id: str,
        variant: str,
        metric: str,
        increment: int = 1,
    ) -> ABTest:
        """
        Update metrics for a variant

        Args:
            db: Database session
            test_id: A/B test ID
            variant: 'A' or 'B'
            metric: Metric name (sent, delivered, opens, clicks, conversions)
            increment: Amount to increment by
        """
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            raise ValueError("A/B test not found")

        field_name = f"variant_{variant.lower()}_{metric}"
        current_value = getattr(ab_test, field_name, 0)
        setattr(ab_test, field_name, current_value + increment)

        db.commit()
        db.refresh(ab_test)

        return ab_test

    def calculate_rates(self, ab_test: ABTest) -> Dict[str, Dict[str, float]]:
        """Calculate performance rates for both variants"""
        variant_a_rates = self._calculate_variant_rates(
            ab_test.variant_a_sent,
            ab_test.variant_a_delivered,
            ab_test.variant_a_opens,
            ab_test.variant_a_clicks,
            ab_test.variant_a_conversions,
        )

        variant_b_rates = self._calculate_variant_rates(
            ab_test.variant_b_sent,
            ab_test.variant_b_delivered,
            ab_test.variant_b_opens,
            ab_test.variant_b_clicks,
            ab_test.variant_b_conversions,
        )

        return {
            "variant_a": variant_a_rates,
            "variant_b": variant_b_rates,
        }

    def _calculate_variant_rates(
        self,
        sent: int,
        delivered: int,
        opens: int,
        clicks: int,
        conversions: int,
    ) -> Dict[str, float]:
        """Calculate rates for a single variant"""
        return {
            "delivery_rate": (delivered / sent * 100) if sent > 0 else 0,
            "open_rate": (opens / delivered * 100) if delivered > 0 else 0,
            "click_rate": (clicks / delivered * 100) if delivered > 0 else 0,
            "conversion_rate": (conversions / delivered * 100) if delivered > 0 else 0,
            "response_rate": (clicks / delivered * 100) if delivered > 0 else 0,
        }

    def check_and_declare_winner(
        self,
        db: Session,
        test_id: str,
    ) -> Optional[Tuple[str, float]]:
        """
        Check if test should end and declare winner

        Returns:
            Tuple of (winner_variant, confidence) or None if not ready
        """
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            raise ValueError("A/B test not found")

        if ab_test.status != ABTestStatus.RUNNING:
            return None

        # Check if enough time has passed
        if ab_test.started_at:
            wait_until = ab_test.started_at + timedelta(hours=ab_test.wait_time_hours)
            if datetime.utcnow() < wait_until:
                return None  # Not enough time has passed

        # Calculate rates
        rates = self.calculate_rates(ab_test)
        metric = ab_test.winner_metric.value

        variant_a_rate = rates["variant_a"][metric]
        variant_b_rate = rates["variant_b"][metric]

        # Get sample sizes
        n_a = ab_test.variant_a_delivered
        n_b = ab_test.variant_b_delivered

        # Check minimum sample size
        if n_a < 30 or n_b < 30:
            return None  # Not enough data

        # Calculate statistical significance (z-test for proportions)
        p_a = variant_a_rate / 100
        p_b = variant_b_rate / 100

        # Pooled proportion
        p_pool = ((n_a * p_a) + (n_b * p_b)) / (n_a + n_b)

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * ((1 / n_a) + (1 / n_b)))

        # Z-score
        if se > 0:
            z_score = abs(p_a - p_b) / se
            # Confidence level (two-tailed test)
            # z > 1.96 = 95% confidence, z > 2.58 = 99% confidence
            confidence = self._z_to_confidence(z_score)
        else:
            confidence = 0

        # Determine winner (require at least 90% confidence)
        winner = None
        if confidence >= 90:
            if variant_a_rate > variant_b_rate:
                winner = "A"
            elif variant_b_rate > variant_a_rate:
                winner = "B"

        if winner:
            ab_test.winner_variant = winner
            ab_test.winner_confidence = confidence
            ab_test.winner_declared_at = datetime.utcnow()
            ab_test.status = ABTestStatus.COMPLETED
            ab_test.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(ab_test)

            return (winner, confidence)

        return None

    def _z_to_confidence(self, z_score: float) -> float:
        """Convert z-score to confidence percentage"""
        # Approximate conversion
        if z_score >= 2.58:
            return 99.0
        elif z_score >= 1.96:
            return 95.0
        elif z_score >= 1.65:
            return 90.0
        elif z_score >= 1.28:
            return 80.0
        else:
            return min(z_score * 50, 79.9)  # Rough approximation for lower values

    def manual_declare_winner(
        self,
        db: Session,
        test_id: str,
        winner_variant: str,
    ) -> ABTest:
        """Manually declare a winner"""
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            raise ValueError("A/B test not found")

        ab_test.winner_variant = winner_variant
        ab_test.winner_declared_at = datetime.utcnow()
        ab_test.winner_confidence = 0  # Manual selection
        ab_test.status = ABTestStatus.COMPLETED
        ab_test.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(ab_test)

        return ab_test

    def get_winner_variant_data(self, ab_test: ABTest) -> Optional[Dict]:
        """Get the winning variant's data"""
        if not ab_test.winner_variant:
            return None

        if ab_test.winner_variant == "A":
            return ab_test.variant_a
        else:
            return ab_test.variant_b

    def list_tests(
        self,
        db: Session,
        user_id: str,
        status: Optional[str] = None,
        test_type: Optional[str] = None,
    ) -> List[ABTest]:
        """List A/B tests with optional filters"""
        query = db.query(ABTest).filter(ABTest.user_id == user_id)

        if status:
            query = query.filter(ABTest.status == status)

        if test_type:
            query = query.filter(ABTest.type == test_type)

        return query.order_by(ABTest.created_at.desc()).all()

    def get_test(self, db: Session, test_id: str) -> Optional[ABTest]:
        """Get a single A/B test"""
        return db.query(ABTest).filter(ABTest.id == test_id).first()

    def delete_test(self, db: Session, test_id: str) -> bool:
        """Delete an A/B test"""
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            return False

        db.delete(ab_test)
        db.commit()
        return True

    def cancel_test(self, db: Session, test_id: str) -> ABTest:
        """Cancel a running test"""
        ab_test = db.query(ABTest).filter(ABTest.id == test_id).first()
        if not ab_test:
            raise ValueError("A/B test not found")

        ab_test.status = ABTestStatus.CANCELLED
        ab_test.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(ab_test)

        return ab_test


# Singleton instance
ab_test_service = ABTestService()
