"""
Autonomous Policy Engine.

Concrete time-based automation rules for QSR order lifecycle,
confidence-based escalation, inventory-driven decisions, and fraud detection.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.core.database import MongoDB
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AutonomousPolicies:
    """
    Implements all autonomous decision rules for the QSR bot.
    Each method returns a PolicyAction dict describing what to do.
    """

    # ── Order Lifecycle Policies ──────────────────────────────────────

    @staticmethod
    async def check_payment_timeout(order_id: str) -> Dict[str, Any]:
        """
        Check payment timing and decide on reminder/cancellation.
        
        Timeline:
          T+0:   Order created → Start 15-min payment timer
          T+5:   No payment → Auto-send reminder
          T+10:  No payment → Final reminder
          T+15:  No payment → Auto-cancel + release inventory
        """
        db = MongoDB.get_database()
        order = await db.orders.find_one({"order_id": order_id})

        if not order:
            return {"action": "none", "reason": "order_not_found"}

        if order.get("status") != "pending":
            return {"action": "none", "reason": f"order_status_is_{order.get('status')}"}

        created_at = order.get("created_at", datetime.now(timezone.utc))
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        now = datetime.now(timezone.utc)
        elapsed = now - created_at
        elapsed_minutes = elapsed.total_seconds() / 60

        if elapsed_minutes >= 15:
            # Auto-cancel
            await db.orders.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancellation_reason": "payment_timeout_15min",
                        "updated_at": now,
                    }
                },
            )
            logger.info("POLICY: Auto-cancelled order %s (T+15min)", order_id)
            return {
                "action": "auto_cancel",
                "order_id": order_id,
                "reason": "payment_timeout",
                "elapsed_minutes": round(elapsed_minutes, 1),
                "message": f"Your order #{order_id} has been cancelled due to payment timeout. Please place a new order if you'd like to continue.",
            }

        elif elapsed_minutes >= 10:
            logger.info("POLICY: Final reminder for order %s (T+10min)", order_id)
            return {
                "action": "final_reminder",
                "order_id": order_id,
                "reason": "payment_pending_10min",
                "elapsed_minutes": round(elapsed_minutes, 1),
                "message": f"⚠️ Last chance! Your order #{order_id} will be cancelled in {int(15 - elapsed_minutes)} minutes if payment is not received.",
            }

        elif elapsed_minutes >= 5:
            logger.info("POLICY: Payment reminder for order %s (T+5min)", order_id)
            return {
                "action": "payment_reminder",
                "order_id": order_id,
                "reason": "payment_pending_5min",
                "elapsed_minutes": round(elapsed_minutes, 1),
                "message": f"Reminder: Your order #{order_id} is awaiting payment. Please complete payment within {int(15 - elapsed_minutes)} minutes to avoid cancellation.",
            }

        return {"action": "none", "reason": "within_grace_period"}

    @staticmethod
    async def handle_payment_success(order_id: str) -> Dict[str, Any]:
        """
        Payment received → Auto-confirm + notify customer.
        """
        db = MongoDB.get_database()
        result = await db.orders.update_one(
            {"order_id": order_id, "status": "pending"},
            {
                "$set": {
                    "status": "confirmed",
                    "payment_status": "paid",
                    "confirmed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        if result.modified_count > 0:
            logger.info("POLICY: Order %s auto-confirmed on payment", order_id)
            return {
                "action": "auto_confirm",
                "order_id": order_id,
                "message": f"✅ Payment received! Your order #{order_id} is confirmed and being prepared. Estimated time: 20 minutes.",
            }
        return {"action": "none", "reason": "order_already_processed"}

    @staticmethod
    async def check_order_ready_notification(order_id: str) -> Dict[str, Any]:
        """
        T+30min after confirm → Auto-send "order ready" notification.
        """
        db = MongoDB.get_database()
        order = await db.orders.find_one({"order_id": order_id})

        if not order or order.get("status") != "confirmed":
            return {"action": "none"}

        confirmed_at = order.get("confirmed_at")
        if not confirmed_at:
            return {"action": "none"}

        if isinstance(confirmed_at, str):
            confirmed_at = datetime.fromisoformat(confirmed_at)

        elapsed = (datetime.now(timezone.utc) - confirmed_at).total_seconds() / 60

        if elapsed >= 30 and not order.get("ready_notified"):
            await db.orders.update_one(
                {"order_id": order_id},
                {"$set": {"ready_notified": True, "status": "ready", "updated_at": datetime.now(timezone.utc)}},
            )
            logger.info("POLICY: Order %s marked ready (T+30min)", order_id)
            return {
                "action": "order_ready",
                "order_id": order_id,
                "message": f"🎉 Your order #{order_id} is ready for pickup!",
            }

        return {"action": "none"}

    @staticmethod
    async def check_pickup_reminder(order_id: str) -> Dict[str, Any]:
        """
        T+60min after ready → Send pickup reminder.
        """
        db = MongoDB.get_database()
        order = await db.orders.find_one({"order_id": order_id})

        if not order or order.get("status") != "ready":
            return {"action": "none"}

        confirmed_at = order.get("confirmed_at")
        if not confirmed_at:
            return {"action": "none"}

        if isinstance(confirmed_at, str):
            confirmed_at = datetime.fromisoformat(confirmed_at)

        elapsed = (datetime.now(timezone.utc) - confirmed_at).total_seconds() / 60

        if elapsed >= 60 and not order.get("pickup_reminded"):
            await db.orders.update_one(
                {"order_id": order_id},
                {"$set": {"pickup_reminded": True, "updated_at": datetime.now(timezone.utc)}},
            )
            logger.info("POLICY: Pickup reminder for order %s (T+60min)", order_id)
            return {
                "action": "pickup_reminder",
                "order_id": order_id,
                "message": f"Your order #{order_id} is still waiting for pickup! Please collect it at your earliest convenience.",
            }

        return {"action": "none"}

    # ── Confidence-Based Escalation ───────────────────────────────────

    @staticmethod
    async def check_escalation(
        confidence: float,
        retry_count: int,
        sentiment_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate whether to escalate to a human agent.
        
        Rules:
          - confidence < 0.7 → Escalate
          - retry_count > 2 → Escalate
          - sentiment negative + score < 0.3 → Immediate escalation
        """
        if sentiment_score is not None and sentiment_score < 0.3:
            logger.info("POLICY: Immediate escalation — negative sentiment (%.2f)", sentiment_score)
            return {
                "action": "escalate_immediate",
                "reason": "negative_sentiment",
                "confidence": confidence,
                "message": "I understand you're frustrated. Let me connect you with our team right away. A human agent will assist you shortly.",
            }

        if retry_count > 2:
            logger.info("POLICY: Escalation — too many retries (%d)", retry_count)
            return {
                "action": "escalate",
                "reason": "retry_limit_exceeded",
                "retry_count": retry_count,
                "message": "I'm having trouble processing your request. Let me connect you with our team for assistance.",
            }

        if confidence < 0.7:
            logger.info("POLICY: Escalation — low confidence (%.2f)", confidence)
            return {
                "action": "escalate",
                "reason": "low_confidence",
                "confidence": confidence,
                "message": "I'm not fully sure about that. Let me connect you with our team to help you better.",
            }

        return {"action": "none"}

    # ── Inventory-Driven Decisions ────────────────────────────────────

    @staticmethod
    async def check_inventory_policies(
        item_id: str,
        stock_count: int,
        order_value: float = 0.0,
        avg_order_value: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Make decisions based on inventory levels.
        
        Rules:
          - stock == 0 → Suggest alternatives + update menu
          - stock < 5 → Add "limited stock" warning
          - order_value > 2x avg → Verify with customer
        """
        actions = []

        if stock_count == 0:
            logger.info("POLICY: Item %s out of stock", item_id)
            actions.append({
                "action": "out_of_stock",
                "item_id": item_id,
                "suggest_alternatives": True,
                "message": "Sorry, this item is currently out of stock. Let me suggest some alternatives!",
            })

        elif stock_count < 5:
            logger.info("POLICY: Item %s low stock (%d)", item_id, stock_count)
            actions.append({
                "action": "low_stock_warning",
                "item_id": item_id,
                "remaining": stock_count,
                "message": f"⚡ Only {stock_count} left! Order now to avoid missing out.",
            })

        if avg_order_value > 0 and order_value > (2 * avg_order_value):
            logger.info("POLICY: High-value order ₹%.2f (avg ₹%.2f)", order_value, avg_order_value)
            actions.append({
                "action": "verify_high_value",
                "order_value": order_value,
                "avg_order_value": avg_order_value,
                "message": f"Just to confirm — your order total is ₹{order_value:.0f}, which is higher than usual. Would you like to proceed?",
            })

        if not actions:
            return {"action": "none"}

        return {"actions": actions} if len(actions) > 1 else actions[0]

    # ── Fraud Detection ───────────────────────────────────────────────

    @staticmethod
    async def check_fraud_signals(
        customer_phone: str,
        order_value: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Detect potential fraud patterns.
        
        Rules:
          - orders_in_hour > 5 → Flag for review
          - payment_failures > 3 → Block 1 hour
          - order_value > ₹5000 → Require phone verification
        """
        db = MongoDB.get_database()
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Count recent orders
        recent_orders = await db.orders.count_documents({
            "customer_phone": customer_phone,
            "created_at": {"$gte": one_hour_ago},
        })

        if recent_orders > 5:
            logger.warning("FRAUD: %s placed %d orders in 1 hour", customer_phone, recent_orders)
            return {
                "action": "flag_for_review",
                "reason": "excessive_orders",
                "count": recent_orders,
                "message": "We've noticed unusual activity on your account. Your order is being reviewed.",
            }

        # Check payment failures
        recent_failures = await db.payment_failures.count_documents({
            "customer_phone": customer_phone,
            "created_at": {"$gte": one_hour_ago},
        })

        if recent_failures > 3:
            logger.warning("FRAUD: %s has %d payment failures in 1 hour", customer_phone, recent_failures)
            return {
                "action": "block_temporary",
                "reason": "payment_failures",
                "count": recent_failures,
                "block_duration_minutes": 60,
                "message": "For security reasons, ordering has been temporarily paused on your account. Please try again in 1 hour.",
            }

        # High value check
        if order_value > 5000:
            logger.info("FRAUD: High-value order ₹%.2f from %s", order_value, customer_phone)
            return {
                "action": "require_verification",
                "reason": "high_value_order",
                "order_value": order_value,
                "message": "For orders above ₹5,000, we need to verify your phone number. You'll receive an OTP shortly.",
            }

        return {"action": "none"}
