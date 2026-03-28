"""
Policy Engine.

Central rule evaluation engine that processes all policy rules against
the current order/user state. Provides audit logging of all autonomous decisions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.database import MongoDB
from app.services.autonomous_policies import AutonomousPolicies
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolicyEngine:
    """
    Evaluates all applicable policy rules for a given context
    and returns the combined set of actions. Every decision is
    audit-logged to MongoDB.
    """

    @staticmethod
    async def evaluate_order_policies(
        order_id: str,
        customer_phone: str,
        order_value: float = 0.0,
        confidence: float = 1.0,
        retry_count: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Run all relevant policies for an order and return actions.
        
        Checks:
          1. Fraud detection
          2. Payment timeout
          3. Escalation needs
          4. Inventory policies (if items are known)
        """
        actions: List[Dict[str, Any]] = []

        # 1. Fraud detection
        fraud_result = await AutonomousPolicies.check_fraud_signals(
            customer_phone=customer_phone,
            order_value=order_value,
        )
        if fraud_result.get("action") != "none":
            actions.append(fraud_result)
            await PolicyEngine._audit_log("fraud_check", order_id, fraud_result)

        # 2. Payment timeout
        timeout_result = await AutonomousPolicies.check_payment_timeout(order_id)
        if timeout_result.get("action") != "none":
            actions.append(timeout_result)
            await PolicyEngine._audit_log("payment_timeout", order_id, timeout_result)

        # 3. Escalation
        escalation_result = await AutonomousPolicies.check_escalation(
            confidence=confidence,
            retry_count=retry_count,
        )
        if escalation_result.get("action") != "none":
            actions.append(escalation_result)
            await PolicyEngine._audit_log("escalation", order_id, escalation_result)

        # 4. Order ready notification
        ready_result = await AutonomousPolicies.check_order_ready_notification(order_id)
        if ready_result.get("action") != "none":
            actions.append(ready_result)
            await PolicyEngine._audit_log("order_ready", order_id, ready_result)

        # 5. Pickup reminder
        pickup_result = await AutonomousPolicies.check_pickup_reminder(order_id)
        if pickup_result.get("action") != "none":
            actions.append(pickup_result)
            await PolicyEngine._audit_log("pickup_reminder", order_id, pickup_result)

        logger.info("PolicyEngine: %d actions for order %s", len(actions), order_id)
        return actions

    @staticmethod
    async def evaluate_pre_order_policies(
        customer_phone: str,
        item_id: str,
        stock_count: int,
        order_value: float,
    ) -> List[Dict[str, Any]]:
        """
        Run pre-order policies (before order creation).
        
        Checks:
          1. Fraud signals
          2. Inventory / stock levels
        """
        actions: List[Dict[str, Any]] = []

        # Fraud check
        fraud = await AutonomousPolicies.check_fraud_signals(customer_phone, order_value)
        if fraud.get("action") != "none":
            actions.append(fraud)
            await PolicyEngine._audit_log("pre_order_fraud", "", fraud)

        # Inventory
        inv = await AutonomousPolicies.check_inventory_policies(
            item_id=item_id,
            stock_count=stock_count,
            order_value=order_value,
        )
        if inv.get("action") != "none":
            actions.append(inv)
            await PolicyEngine._audit_log("pre_order_inventory", "", inv)

        return actions

    @staticmethod
    async def _audit_log(
        policy_name: str,
        order_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Log every autonomous decision to MongoDB for audit trail."""
        try:
            db = MongoDB.get_database()
            await db.policy_audit_log.insert_one({
                "policy_name": policy_name,
                "order_id": order_id,
                "result": result,
                "timestamp": datetime.now(timezone.utc),
            })
        except Exception as exc:
            logger.warning("Failed to write policy audit log: %s", exc)


# Singleton
policy_engine = PolicyEngine()
