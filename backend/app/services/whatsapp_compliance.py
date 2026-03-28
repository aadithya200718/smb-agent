"""
WhatsApp Compliance Service.

Implements WhatsApp Business API compliance rules:
  - 24-hour session window tracking
  - Pre-approved template management
  - Rate limiting per phone number
  - Consent tracking
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from app.core.database import MongoDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    Tracks WhatsApp 24-hour messaging sessions.
    
    Rules:
      - After user sends a message, a 24-hour window opens
      - Within the window: free-form messages allowed
      - Outside the window: only pre-approved templates allowed
    """

    @staticmethod
    async def is_session_active(customer_phone: str) -> bool:
        """Check if the 24-hour session window is still open."""
        db = MongoDB.get_database()
        session = await db.whatsapp_sessions.find_one(
            {"customer_phone": customer_phone}
        )

        if not session:
            return False

        last_user_message = session.get("last_user_message_at")
        if not last_user_message:
            return False

        if isinstance(last_user_message, str):
            last_user_message = datetime.fromisoformat(last_user_message)

        elapsed = datetime.now(timezone.utc) - last_user_message
        is_active = elapsed < timedelta(hours=24)

        if not is_active:
            logger.info("Session expired for %s (last msg: %s)", customer_phone, last_user_message)

        return is_active

    @staticmethod
    async def update_session(customer_phone: str) -> None:
        """Mark a new user message received (refreshes the 24-hour window)."""
        db = MongoDB.get_database()
        await db.whatsapp_sessions.update_one(
            {"customer_phone": customer_phone},
            {
                "$set": {
                    "last_user_message_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                    "consent_given": True,
                },
            },
            upsert=True,
        )

    @staticmethod
    async def get_session_info(customer_phone: str) -> Dict[str, Any]:
        """Get session details for a customer."""
        db = MongoDB.get_database()
        session = await db.whatsapp_sessions.find_one({"customer_phone": customer_phone})
        if not session:
            return {"active": False, "remaining_seconds": 0}

        last_msg = session.get("last_user_message_at", datetime.now(timezone.utc))
        if isinstance(last_msg, str):
            last_msg = datetime.fromisoformat(last_msg)

        elapsed = datetime.now(timezone.utc) - last_msg
        remaining = timedelta(hours=24) - elapsed
        remaining_seconds = max(0, remaining.total_seconds())

        return {
            "active": remaining_seconds > 0,
            "remaining_seconds": int(remaining_seconds),
            "last_message_at": last_msg.isoformat(),
        }


class TemplateManager:
    """
    Manages pre-approved WhatsApp message templates.
    
    Templates are required for messages sent outside the 24-hour window.
    """

    # Pre-approved templates with placeholders
    TEMPLATES = {
        "order_confirmation": {
            "name": "qsr_order_confirmed",
            "language": "en",
            "body": "✅ Order #{order_id} confirmed! Total: ₹{total}. Estimated time: {eta} minutes. Track your order here: {tracking_link}",
            "category": "UTILITY",
        },
        "payment_reminder": {
            "name": "qsr_payment_reminder",
            "language": "en",
            "body": "⏰ Reminder: Your order #{order_id} (₹{total}) is awaiting payment. Complete payment here: {payment_link}. Order will be cancelled in {minutes_remaining} minutes.",
            "category": "UTILITY",
        },
        "order_ready": {
            "name": "qsr_order_ready",
            "language": "en",
            "body": "🎉 Your order #{order_id} is ready for pickup! Please collect it at the counter. Thank you for ordering with us!",
            "category": "UTILITY",
        },
        "order_cancelled": {
            "name": "qsr_order_cancelled",
            "language": "en",
            "body": "Your order #{order_id} has been cancelled. Reason: {reason}. If you'd like to place a new order, just send us a message!",
            "category": "UTILITY",
        },
        "welcome_back": {
            "name": "qsr_welcome_back",
            "language": "en",
            "body": "👋 Welcome back! We've got some fresh items on the menu today. Reply 'menu' to see what's available!",
            "category": "MARKETING",
        },
    }

    @staticmethod
    def get_template(template_key: str, **params) -> Optional[Dict[str, str]]:
        """
        Get a rendered template with parameters filled in.
        
        Returns None if template not found.
        """
        template = TemplateManager.TEMPLATES.get(template_key)
        if not template:
            logger.warning("Template not found: %s", template_key)
            return None

        try:
            rendered_body = template["body"].format(**params)
            return {
                "name": template["name"],
                "language": template["language"],
                "body": rendered_body,
                "category": template["category"],
            }
        except KeyError as e:
            logger.error("Template %s missing parameter: %s", template_key, e)
            return None

    @staticmethod
    def list_templates() -> Dict[str, Dict[str, str]]:
        """List all available templates."""
        return TemplateManager.TEMPLATES


class WhatsAppCompliance:
    """
    High-level compliance orchestrator.
    
    Determines whether to send a free-form message or use a template
    based on session status.
    """

    @staticmethod
    async def get_send_strategy(
        customer_phone: str,
        message_type: str = "freeform",
        template_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Determine the appropriate sending strategy.
        
        Returns:
            {
                "strategy": "freeform" | "template" | "blocked",
                "template": {...} if applicable,
                "reason": str,
            }
        """
        session_active = await SessionManager.is_session_active(customer_phone)

        if session_active:
            return {
                "strategy": "freeform",
                "reason": "session_active",
            }
        else:
            # Outside session — must use template
            if template_key:
                template = TemplateManager.get_template(template_key)
                if template:
                    return {
                        "strategy": "template",
                        "template": template,
                        "reason": "session_expired_using_template",
                    }

            return {
                "strategy": "blocked",
                "reason": "session_expired_no_template",
            }

    @staticmethod
    async def check_rate_limit(customer_phone: str, limit_per_hour: int = 20) -> bool:
        """
        Check if we've exceeded the rate limit for outbound messages.
        Returns True if sending is allowed.
        """
        db = MongoDB.get_database()
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        count = await db.outbound_messages.count_documents({
            "customer_phone": customer_phone,
            "sent_at": {"$gte": one_hour_ago},
        })

        if count >= limit_per_hour:
            logger.warning("Rate limit reached for %s (%d/%d)", 
                        customer_phone, count, limit_per_hour)
            return False
        return True

    @staticmethod
    async def record_outbound(customer_phone: str, message_type: str) -> None:
        """Record an outbound message for rate limiting."""
        db = MongoDB.get_database()
        await db.outbound_messages.insert_one({
            "customer_phone": customer_phone,
            "message_type": message_type,
            "sent_at": datetime.now(timezone.utc),
        })


# Singletons
session_manager = SessionManager()
template_manager = TemplateManager()
whatsapp_compliance = WhatsAppCompliance()
