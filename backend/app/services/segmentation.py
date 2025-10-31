"""
Segmentation service for advanced audience targeting
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.segment import (
    Segment,
    SegmentMembership,
    SegmentType,
    FilterLogic,
    FilterFieldType,
    FilterOperator,
)
from app.models.lead import Lead


class SegmentationService:
    """Service for managing segments and filtering leads"""

    def create_segment(
        self,
        db: Session,
        user_id: str,
        name: str,
        segment_type: str = "dynamic",
        description: Optional[str] = None,
        filter_logic: str = "and",
        filters: Optional[List[Dict]] = None,
        static_lead_ids: Optional[List[str]] = None,
        auto_update: bool = True,
    ) -> Segment:
        """Create a new segment"""
        segment = Segment(
            user_id=user_id,
            name=name,
            description=description,
            segment_type=segment_type,
            filter_logic=filter_logic,
            filters=filters or [],
            static_lead_ids=static_lead_ids or [],
            auto_update=auto_update,
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)

        # Calculate initial members
        if segment_type == SegmentType.DYNAMIC.value:
            self.calculate_segment_members(db, segment.id)
        elif static_lead_ids:
            self.add_static_members(db, segment.id, static_lead_ids)

        return segment

    def update_segment(
        self,
        db: Session,
        segment_id: str,
        **kwargs,
    ) -> Segment:
        """Update segment details"""
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            raise ValueError("Segment not found")

        # Track if filters changed
        filters_changed = False
        if "filters" in kwargs and kwargs["filters"] != segment.filters:
            filters_changed = True
        if "filter_logic" in kwargs and kwargs["filter_logic"] != segment.filter_logic:
            filters_changed = True

        # Update fields
        for key, value in kwargs.items():
            if hasattr(segment, key):
                setattr(segment, key, value)

        db.commit()
        db.refresh(segment)

        # Recalculate if dynamic and filters changed
        if filters_changed and segment.segment_type == SegmentType.DYNAMIC:
            self.calculate_segment_members(db, segment_id)

        return segment

    def evaluate_filter(
        self,
        db: Session,
        lead: Lead,
        filter_condition: Dict,
    ) -> bool:
        """
        Evaluate a single filter condition against a lead

        Returns:
            True if lead matches the condition, False otherwise
        """
        field_type = filter_condition.get("field_type")
        operator = filter_condition.get("operator")
        value = filter_condition.get("value")

        # Get the actual value from the lead
        actual_value = self._get_lead_value(db, lead, filter_condition)

        # Evaluate the condition
        return self._evaluate_operator(actual_value, operator, value)

    def _get_lead_value(
        self,
        db: Session,
        lead: Lead,
        filter_condition: Dict,
    ) -> Any:
        """Get the value from lead based on filter field type"""
        field_type = filter_condition.get("field_type")
        field_name = filter_condition.get("field_name")

        if field_type == FilterFieldType.LEAD_PROPERTY.value:
            # Direct property (email, name, company, etc.)
            return getattr(lead, field_name, None)

        elif field_type == FilterFieldType.LEAD_SCORE.value:
            return lead.score

        elif field_type == FilterFieldType.LEAD_STATUS.value:
            return lead.status.value if lead.status else None

        elif field_type == FilterFieldType.LEAD_SOURCE.value:
            return lead.source

        elif field_type == FilterFieldType.LEAD_TAG.value:
            # Check if lead has specific tag
            tags = lead.tags or []
            return field_name in tags

        elif field_type == FilterFieldType.CUSTOM_FIELD.value:
            # Check custom fields
            custom_fields = lead.custom_fields or {}
            return custom_fields.get(field_name)

        elif field_type == FilterFieldType.LAST_ACTIVITY_DATE.value:
            return lead.last_activity_at

        elif field_type == FilterFieldType.EMAIL_OPENED.value:
            # Check if lead opened emails
            # This would require tracking email opens - simplified for now
            # In production, you'd query email tracking tables
            return False  # Placeholder

        elif field_type == FilterFieldType.EMAIL_CLICKED.value:
            # Check if lead clicked emails
            return False  # Placeholder

        elif field_type == FilterFieldType.TOTAL_EMAILS_OPENED.value:
            # Count of emails opened
            return 0  # Placeholder

        elif field_type == FilterFieldType.TOTAL_EMAILS_CLICKED.value:
            # Count of emails clicked
            return 0  # Placeholder

        elif field_type == FilterFieldType.ENGAGEMENT_SCORE.value:
            # Custom engagement calculation
            return lead.score  # Using lead score as proxy

        return None

    def _evaluate_operator(
        self,
        actual_value: Any,
        operator: str,
        expected_value: Any,
    ) -> bool:
        """Evaluate an operator condition"""
        if actual_value is None:
            return operator in [
                FilterOperator.IS_EMPTY.value,
                FilterOperator.NOT_EQUALS.value,
            ]

        try:
            if operator == FilterOperator.EQUALS.value:
                return actual_value == expected_value

            elif operator == FilterOperator.NOT_EQUALS.value:
                return actual_value != expected_value

            elif operator == FilterOperator.CONTAINS.value:
                return expected_value.lower() in str(actual_value).lower()

            elif operator == FilterOperator.NOT_CONTAINS.value:
                return expected_value.lower() not in str(actual_value).lower()

            elif operator == FilterOperator.STARTS_WITH.value:
                return str(actual_value).lower().startswith(expected_value.lower())

            elif operator == FilterOperator.ENDS_WITH.value:
                return str(actual_value).lower().endswith(expected_value.lower())

            elif operator == FilterOperator.GREATER_THAN.value:
                return float(actual_value) > float(expected_value)

            elif operator == FilterOperator.LESS_THAN.value:
                return float(actual_value) < float(expected_value)

            elif operator == FilterOperator.GREATER_THAN_OR_EQUAL.value:
                return float(actual_value) >= float(expected_value)

            elif operator == FilterOperator.LESS_THAN_OR_EQUAL.value:
                return float(actual_value) <= float(expected_value)

            elif operator == FilterOperator.IN.value:
                return actual_value in expected_value

            elif operator == FilterOperator.NOT_IN.value:
                return actual_value not in expected_value

            elif operator == FilterOperator.IS_EMPTY.value:
                return actual_value is None or actual_value == ""

            elif operator == FilterOperator.IS_NOT_EMPTY.value:
                return actual_value is not None and actual_value != ""

            elif operator == FilterOperator.BETWEEN.value:
                # expected_value should be [min, max]
                return expected_value[0] <= actual_value <= expected_value[1]

            elif operator == FilterOperator.IN_LAST_DAYS.value:
                # For date fields
                if not isinstance(actual_value, datetime):
                    return False
                cutoff_date = datetime.utcnow() - timedelta(days=int(expected_value))
                return actual_value >= cutoff_date

        except (ValueError, TypeError, AttributeError):
            return False

        return False

    def evaluate_lead_for_segment(
        self,
        db: Session,
        lead: Lead,
        segment: Segment,
    ) -> bool:
        """
        Evaluate if a lead matches all segment conditions

        Returns:
            True if lead matches segment criteria, False otherwise
        """
        if segment.segment_type == SegmentType.STATIC:
            # For static segments, check if lead ID is in the list
            return str(lead.id) in (segment.static_lead_ids or [])

        # Dynamic segment - evaluate filters
        if not segment.filters:
            return False

        results = []
        for filter_condition in segment.filters:
            result = self.evaluate_filter(db, lead, filter_condition)
            results.append(result)

        # Combine results based on logic
        if segment.filter_logic == FilterLogic.AND:
            return all(results)
        else:  # OR
            return any(results)

    def calculate_segment_members(
        self,
        db: Session,
        segment_id: str,
    ) -> int:
        """
        Calculate and update segment membership

        Returns:
            Number of leads in segment
        """
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            raise ValueError("Segment not found")

        # Clear existing memberships
        db.query(SegmentMembership).filter(
            SegmentMembership.segment_id == segment_id
        ).delete()

        # Get all leads for this user
        leads = db.query(Lead).filter(Lead.user_id == segment.user_id).all()

        # Evaluate each lead
        matched_count = 0
        for lead in leads:
            if self.evaluate_lead_for_segment(db, lead, segment):
                membership = SegmentMembership(
                    segment_id=segment_id,
                    lead_id=lead.id,
                )
                db.add(membership)
                matched_count += 1

        # Update segment statistics
        segment.lead_count = matched_count
        segment.last_calculated_at = datetime.utcnow()

        db.commit()
        return matched_count

    def add_static_members(
        self,
        db: Session,
        segment_id: str,
        lead_ids: List[str],
    ):
        """Add leads to a static segment"""
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            raise ValueError("Segment not found")

        if segment.segment_type != SegmentType.STATIC:
            raise ValueError("Can only add static members to static segments")

        # Add to static_lead_ids
        current_ids = set(segment.static_lead_ids or [])
        current_ids.update(lead_ids)
        segment.static_lead_ids = list(current_ids)

        # Create memberships
        for lead_id in lead_ids:
            # Check if already exists
            existing = db.query(SegmentMembership).filter(
                and_(
                    SegmentMembership.segment_id == segment_id,
                    SegmentMembership.lead_id == lead_id,
                )
            ).first()

            if not existing:
                membership = SegmentMembership(
                    segment_id=segment_id,
                    lead_id=lead_id,
                )
                db.add(membership)

        # Update count
        segment.lead_count = len(current_ids)

        db.commit()

    def remove_static_members(
        self,
        db: Session,
        segment_id: str,
        lead_ids: List[str],
    ):
        """Remove leads from a static segment"""
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            raise ValueError("Segment not found")

        if segment.segment_type != SegmentType.STATIC:
            raise ValueError("Can only remove static members from static segments")

        # Remove from static_lead_ids
        current_ids = set(segment.static_lead_ids or [])
        current_ids.difference_update(lead_ids)
        segment.static_lead_ids = list(current_ids)

        # Remove memberships
        db.query(SegmentMembership).filter(
            and_(
                SegmentMembership.segment_id == segment_id,
                SegmentMembership.lead_id.in_(lead_ids),
            )
        ).delete(synchronize_session=False)

        # Update count
        segment.lead_count = len(current_ids)

        db.commit()

    def get_segment_leads(
        self,
        db: Session,
        segment_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Lead]:
        """Get leads in a segment"""
        lead_ids = (
            db.query(SegmentMembership.lead_id)
            .filter(SegmentMembership.segment_id == segment_id)
            .limit(limit)
            .offset(offset)
            .all()
        )

        lead_ids = [lid[0] for lid in lead_ids]

        return db.query(Lead).filter(Lead.id.in_(lead_ids)).all()

    def preview_segment(
        self,
        db: Session,
        user_id: str,
        filters: List[Dict],
        filter_logic: str = "and",
    ) -> Dict:
        """
        Preview how many leads would match the filters without creating segment

        Returns:
            Dict with count and sample leads
        """
        # Create temporary segment object (not saved to DB)
        temp_segment = Segment(
            user_id=user_id,
            name="preview",
            segment_type=SegmentType.DYNAMIC,
            filter_logic=filter_logic,
            filters=filters,
        )

        # Get all leads for this user
        leads = db.query(Lead).filter(Lead.user_id == user_id).all()

        # Evaluate each lead
        matched_leads = []
        for lead in leads:
            if self.evaluate_lead_for_segment(db, lead, temp_segment):
                matched_leads.append(lead)

        return {
            "count": len(matched_leads),
            "sample_leads": matched_leads[:5],  # Return first 5 as sample
        }

    def list_segments(
        self,
        db: Session,
        user_id: str,
        segment_type: Optional[str] = None,
    ) -> List[Segment]:
        """List segments for a user"""
        query = db.query(Segment).filter(Segment.user_id == user_id)

        if segment_type:
            query = query.filter(Segment.segment_type == segment_type)

        return query.order_by(Segment.created_at.desc()).all()

    def get_segment(self, db: Session, segment_id: str) -> Optional[Segment]:
        """Get a single segment"""
        return db.query(Segment).filter(Segment.id == segment_id).first()

    def delete_segment(self, db: Session, segment_id: str) -> bool:
        """Delete a segment"""
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            return False

        db.delete(segment)
        db.commit()
        return True

    def duplicate_segment(
        self,
        db: Session,
        segment_id: str,
        new_name: Optional[str] = None,
    ) -> Segment:
        """Duplicate an existing segment"""
        original = db.query(Segment).filter(Segment.id == segment_id).first()
        if not original:
            raise ValueError("Segment not found")

        duplicate = Segment(
            user_id=original.user_id,
            name=new_name or f"{original.name} (Copy)",
            description=original.description,
            segment_type=original.segment_type,
            filter_logic=original.filter_logic,
            filters=original.filters,
            static_lead_ids=original.static_lead_ids.copy() if original.static_lead_ids else [],
            auto_update=original.auto_update,
        )
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)

        # Calculate members
        if duplicate.segment_type == SegmentType.DYNAMIC:
            self.calculate_segment_members(db, duplicate.id)
        elif duplicate.static_lead_ids:
            self.add_static_members(db, duplicate.id, duplicate.static_lead_ids)

        return duplicate


# Singleton instance
segmentation_service = SegmentationService()
