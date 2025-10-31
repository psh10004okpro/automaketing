"""
Workflow Automation Engine
"""
from typing import Dict, List, Any
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session
from app.models.workflow import Workflow
from app.services.email_campaign import email_service

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Engine for executing automated workflows"""

    def __init__(self):
        self.running_workflows = {}

    def create_workflow(
        self,
        db: Session,
        user_id: str,
        name: str,
        trigger_type: str,
        steps: List[Dict[str, Any]]
    ) -> Workflow:
        """
        Create a new workflow

        Args:
            db: Database session
            user_id: User ID
            name: Workflow name
            trigger_type: Type of trigger (new_signup, form_submit, etc.)
            steps: List of workflow steps

        Returns:
            Created workflow
        """
        workflow = Workflow(
            user_id=user_id,
            name=name,
            trigger_type=trigger_type,
            steps=steps,
            active=True
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        return workflow

    async def execute_workflow(
        self,
        db: Session,
        workflow_id: str,
        trigger_data: Dict[str, Any]
    ):
        """
        Execute a workflow

        Args:
            db: Database session
            workflow_id: Workflow ID
            trigger_data: Data from the trigger event
        """
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.active == True
        ).first()

        if not workflow:
            logger.warning(f"Workflow {workflow_id} not found or inactive")
            return

        execution_id = f"{workflow_id}_{datetime.utcnow().timestamp()}"
        self.running_workflows[execution_id] = {
            "workflow_id": workflow_id,
            "started_at": datetime.utcnow(),
            "status": "running"
        }

        context = {
            "user": trigger_data.get("user", {}),
            "trigger_data": trigger_data,
            "variables": {}
        }

        try:
            for step in workflow.steps:
                await self._execute_step(db, step, context)

            self.running_workflows[execution_id]["status"] = "completed"
            logger.info(f"Workflow {workflow_id} completed successfully")

        except Exception as e:
            self.running_workflows[execution_id]["status"] = "failed"
            self.running_workflows[execution_id]["error"] = str(e)
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")

    async def _execute_step(
        self,
        db: Session,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """
        Execute a single workflow step

        Args:
            db: Database session
            step: Step configuration
            context: Execution context
        """
        step_type = step.get("type")
        config = step.get("config", {})

        logger.info(f"Executing step: {step_type}")

        if step_type == "send_email":
            await self._execute_send_email(db, config, context)

        elif step_type == "wait":
            await self._execute_wait(config)

        elif step_type == "condition":
            await self._execute_condition(db, config, context)

        elif step_type == "add_tag":
            await self._execute_add_tag(db, config, context)

        elif step_type == "webhook":
            await self._execute_webhook(config, context)

        else:
            logger.warning(f"Unknown step type: {step_type}")

    async def _execute_send_email(
        self,
        db: Session,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Execute send email action"""
        # Get email template or content
        subject = config.get("subject", "")
        content = config.get("content", "")

        # Personalize with context
        user = context.get("user", {})
        subject = self._render_template(subject, context)
        content = self._render_template(content, context)

        # Send email (simplified - would normally use campaign system)
        logger.info(f"Sending email to {user.get('email')}: {subject}")

        # Simulate sending
        await asyncio.sleep(0.1)

    async def _execute_wait(self, config: Dict[str, Any]):
        """Execute wait action"""
        duration = config.get("duration", 60)  # seconds
        logger.info(f"Waiting for {duration} seconds")
        await asyncio.sleep(duration)

    async def _execute_condition(
        self,
        db: Session,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Execute conditional branching"""
        condition = config.get("condition", {})
        condition_met = self._evaluate_condition(condition, context)

        if condition_met:
            logger.info("Condition met, executing true path")
            for step in config.get("true_path", []):
                await self._execute_step(db, step, context)
        else:
            logger.info("Condition not met, executing false path")
            for step in config.get("false_path", []):
                await self._execute_step(db, step, context)

    async def _execute_add_tag(
        self,
        db: Session,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Execute add tag action"""
        tag = config.get("tag")
        user_id = context.get("user", {}).get("id")

        logger.info(f"Adding tag '{tag}' to user {user_id}")

        # TODO: Implement actual tag addition to database
        await asyncio.sleep(0.1)

    async def _execute_webhook(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Execute webhook action"""
        url = config.get("url")
        method = config.get("method", "POST")
        payload = config.get("payload", {})

        logger.info(f"Calling webhook: {method} {url}")

        # TODO: Implement actual HTTP request
        await asyncio.sleep(0.1)

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition

        Args:
            condition: Condition configuration
            context: Execution context

        Returns:
            True if condition is met
        """
        field = condition.get("field")
        operator = condition.get("operator")
        expected_value = condition.get("value")

        # Get actual value from context
        actual_value = context.get(field)

        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "greater_than":
            return actual_value > expected_value
        elif operator == "less_than":
            return actual_value < expected_value
        elif operator == "contains":
            return expected_value in str(actual_value)

        return False

    def _render_template(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template with context variables

        Args:
            template: Template string
            context: Context data

        Returns:
            Rendered string
        """
        rendered = template

        # Replace variables
        user = context.get("user", {})
        for key, value in user.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

        # Replace trigger data
        trigger_data = context.get("trigger_data", {})
        for key, value in trigger_data.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

        return rendered


# Singleton instance
workflow_engine = WorkflowEngine()
