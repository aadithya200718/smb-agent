"""
Advanced Razorpay Integration.

Extends the basic payment service with:
  - Payment link creation with callback URLs
  - Webhook signature verification + event dispatching
  - Auto-confirm order on payment success
  - Auto-cancel order on payment timeout
  - Refund automation
"""

import base64
import hashlib
import hmac
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.database import MongoDB
from app.utils.logger import get_logger
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.idempotency import IdempotencyManager

logger = get_logger(__name__)
settings = get_settings()

_razorpay_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


class RazorpayAdvancedService:
    """
    Production-grade Razorpay integration with webhook reconciliation,
    auto-confirmation, timeout handling, and refund automation.
    """

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID or ""
        self.key_secret = settings.RAZORPAY_KEY_SECRET or ""
        self.webhook_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None) or ""
        self.base_url = "https://api.razorpay.com/v1"
        self.mock_mode = not bool(self.key_id)

        if self.mock_mode:
            logger.warning("Razorpay credentials missing — running in MOCK mode.")
        else:
            logger.info("RazorpayAdvancedService initialized.")

    def _auth_header(self) -> str:
        auth_string = f"{self.key_id}:{self.key_secret}"
        return f"Basic {base64.b64encode(auth_string.encode()).decode()}"

    # ── Payment Link Creation ─────────────────────────────────────────

    @_razorpay_breaker
    async def create_payment_link(
        self,
        order_id: str,
        amount: float,
        customer_phone: str,
        customer_name: str = "Customer",
        description: str = "",
        expire_by_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay payment link with callback URL and expiry.
        
        Returns:
            {
                "payment_link_id": str,
                "short_url": str,
                "amount": float,
                "expire_by": int (unix timestamp),
                "status": str,
            }
        """
        # Idempotency check
        idem_key = IdempotencyManager.generate_key("payment_link", order_id)
        is_new = await IdempotencyManager.check_and_lock(idem_key, f"create_payment_link:{order_id}")
        if not is_new:
            logger.info("Duplicate payment link request for %s — skipping", order_id)
            # Look up existing link
            db = MongoDB.get_database()
            existing = await db.payment_links.find_one({"order_id": order_id})
            if existing:
                return {
                    "payment_link_id": existing.get("payment_link_id", ""),
                    "short_url": existing.get("short_url", ""),
                    "amount": amount,
                    "status": "existing",
                }

        if self.mock_mode:
            mock_link_id = f"plink_mock_{order_id}"
            mock_url = f"https://rzp.io/mock/{order_id}"
            
            # Store in DB
            db = MongoDB.get_database()
            await db.payment_links.insert_one({
                "payment_link_id": mock_link_id,
                "order_id": order_id,
                "short_url": mock_url,
                "amount": amount,
                "status": "created",
                "created_at": datetime.now(timezone.utc),
            })
            
            logger.info("Razorpay MOCK: payment link created — %s", mock_url)
            return {
                "payment_link_id": mock_link_id,
                "short_url": mock_url,
                "amount": amount,
                "status": "created",
            }

        import time
        expire_by = int(time.time()) + (expire_by_minutes * 60)
        callback_url = f"{settings.WEBHOOK_BASE_URL or 'https://localhost:8000'}/webhooks/razorpay"

        payload = {
            "amount": int(amount * 100),  # paise
            "currency": "INR",
            "description": description or f"Order #{order_id}",
            "customer": {
                "name": customer_name,
                "contact": customer_phone,
            },
            "notify": {"sms": True, "whatsapp": True},
            "reminder_enable": True,
            "expire_by": expire_by,
            "callback_url": callback_url,
            "callback_method": "get",
            "notes": {
                "order_id": order_id,
            },
        }

        try:
            headers = {
                "Authorization": self._auth_header(),
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/payment_links",
                    headers=headers,
                    json=payload,
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()

            result = {
                "payment_link_id": data.get("id", ""),
                "short_url": data.get("short_url", ""),
                "amount": amount,
                "expire_by": expire_by,
                "status": data.get("status", "created"),
            }

            # Store in DB
            db = MongoDB.get_database()
            await db.payment_links.insert_one({
                **result,
                "order_id": order_id,
                "created_at": datetime.now(timezone.utc),
            })

            logger.info("Razorpay: payment link created — %s", result["short_url"])
            return result

        except Exception as e:
            logger.error("Razorpay payment link creation failed: %s", e)
            raise

    # ── Webhook Signature Verification ────────────────────────────────

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify the Razorpay webhook signature using HMAC-SHA256.
        """
        if not self.webhook_secret:
            logger.warning("Razorpay webhook secret not configured — skipping verification.")
            return True  # Allow in dev

        expected = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(expected, signature)
        if not is_valid:
            logger.warning("Razorpay webhook signature mismatch!")
        return is_valid

    # ── Webhook Event Handler ─────────────────────────────────────────

    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, str]:
        """
        Process Razorpay webhook events.
        
        Supported events:
          - payment.captured → auto-confirm order
          - payment_link.expired → auto-cancel order
          - refund.processed → mark refund complete
        """
        event_type = event.get("event", "")
        payload = event.get("payload", {})

        logger.info("Razorpay webhook event: %s", event_type)

        if event_type == "payment.captured":
            return await self._handle_payment_captured(payload)
        elif event_type == "payment_link.expired":
            return await self._handle_payment_expired(payload)
        elif event_type == "refund.processed":
            return await self._handle_refund_processed(payload)
        else:
            logger.info("Unhandled Razorpay event: %s", event_type)
            return {"status": "ignored", "event": event_type}

    async def _handle_payment_captured(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Auto-confirm order on successful payment."""
        payment = payload.get("payment", {}).get("entity", {})
        notes = payment.get("notes", {})
        order_id = notes.get("order_id", "")

        if not order_id:
            logger.warning("Payment captured but no order_id in notes")
            return {"status": "error", "reason": "missing_order_id"}

        db = MongoDB.get_database()

        # Update order status to confirmed
        result = await db.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "confirmed",
                    "payment_status": "paid",
                    "payment_id": payment.get("id", ""),
                    "paid_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        if result.modified_count > 0:
            logger.info("Order %s auto-confirmed on payment capture", order_id)
            return {"status": "confirmed", "order_id": order_id}
        else:
            logger.warning("Order %s not found for payment capture", order_id)
            return {"status": "order_not_found", "order_id": order_id}

    async def _handle_payment_expired(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Auto-cancel order when payment link expires."""
        payment_link = payload.get("payment_link", {}).get("entity", {})
        notes = payment_link.get("notes", {})
        order_id = notes.get("order_id", "")

        if not order_id:
            return {"status": "error", "reason": "missing_order_id"}

        db = MongoDB.get_database()

        result = await db.orders.update_one(
            {"order_id": order_id, "status": "pending"},
            {
                "$set": {
                    "status": "cancelled",
                    "cancellation_reason": "payment_timeout",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        if result.modified_count > 0:
            logger.info("Order %s auto-cancelled on payment timeout", order_id)
            return {"status": "cancelled", "order_id": order_id}
        else:
            logger.info("Order %s already processed or not found", order_id)
            return {"status": "already_processed", "order_id": order_id}

    async def _handle_refund_processed(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Mark refund as complete."""
        refund = payload.get("refund", {}).get("entity", {})
        payment_id = refund.get("payment_id", "")

        db = MongoDB.get_database()
        await db.orders.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "refund_status": "processed",
                    "refund_id": refund.get("id", ""),
                    "refunded_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        logger.info("Refund processed for payment %s", payment_id)
        return {"status": "refund_processed", "payment_id": payment_id}

    # ── Refund Automation ─────────────────────────────────────────────

    @_razorpay_breaker
    async def initiate_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "customer_request",
    ) -> Dict[str, Any]:
        """
        Initiate a refund for a payment. If amount is None, full refund.
        """
        if self.mock_mode:
            logger.info("Razorpay MOCK: refund initiated for %s", payment_id)
            return {
                "refund_id": f"rfnd_mock_{payment_id}",
                "status": "processed",
                "amount": amount or 0,
            }

        try:
            payload: Dict[str, Any] = {"speed": "normal"}
            if amount is not None:
                payload["amount"] = int(amount * 100)

            headers = {
                "Authorization": self._auth_header(),
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/payments/{payment_id}/refund",
                    headers=headers,
                    json=payload,
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()

            logger.info("Razorpay: refund initiated — %s", data.get("id"))
            return {
                "refund_id": data.get("id", ""),
                "status": data.get("status", ""),
                "amount": data.get("amount", 0) / 100,
            }
        except Exception as e:
            logger.error("Razorpay refund failed: %s", e)
            raise


# Singleton instance
razorpay_service = RazorpayAdvancedService()
