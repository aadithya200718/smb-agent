"""
Scheduler Service (Rewritten for QSR Policy Engine).

Runs background jobs for autonomous order lifecycle management:
  - Payment timeout checks every minute
  - Order ready notifications every 5 minutes
  - Pickup reminders every 10 minutes
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone

from app.utils.logger import get_logger

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def _check_pending_payments():
    """
    Scan all pending orders and apply payment timeout policies.
    Runs every 60 seconds.
    """
    try:
        from app.core.database import MongoDB
        from app.services.autonomous_policies import AutonomousPolicies
        from app.services.whatsapp import whatsapp_service

        db = MongoDB.get_database()
        cursor = db.orders.find({"status": "pending"})
        pending_orders = await cursor.to_list(length=100)

        for order in pending_orders:
            order_id = order.get("order_id", "")
            result = await AutonomousPolicies.check_payment_timeout(order_id)

            action = result.get("action", "none")
            if action in ("payment_reminder", "final_reminder", "auto_cancel"):
                phone = order.get("customer_phone", "")
                message = result.get("message", "")
                if phone and message:
                    await whatsapp_service.send_message(to=phone, body=message)
                    logger.info("Scheduler: sent %s for order %s", action, order_id)

    except Exception as exc:
        logger.error("Scheduler _check_pending_payments failed: %s", exc)


async def _check_order_ready():
    """
    Scan confirmed orders and send ready notifications.
    Runs every 5 minutes.
    """
    try:
        from app.core.database import MongoDB
        from app.services.autonomous_policies import AutonomousPolicies
        from app.services.whatsapp import whatsapp_service

        db = MongoDB.get_database()
        cursor = db.orders.find({"status": "confirmed", "ready_notified": {"$ne": True}})
        confirmed_orders = await cursor.to_list(length=100)

        for order in confirmed_orders:
            order_id = order.get("order_id", "")
            result = await AutonomousPolicies.check_order_ready_notification(order_id)

            if result.get("action") == "order_ready":
                phone = order.get("customer_phone", "")
                message = result.get("message", "")
                if phone and message:
                    await whatsapp_service.send_message(to=phone, body=message)
                    logger.info("Scheduler: sent order_ready for %s", order_id)

    except Exception as exc:
        logger.error("Scheduler _check_order_ready failed: %s", exc)


async def _check_pickup_reminders():
    """
    Scan ready orders and send pickup reminders.
    Runs every 10 minutes.
    """
    try:
        from app.core.database import MongoDB
        from app.services.autonomous_policies import AutonomousPolicies
        from app.services.whatsapp import whatsapp_service

        db = MongoDB.get_database()
        cursor = db.orders.find({"status": "ready", "pickup_reminded": {"$ne": True}})
        ready_orders = await cursor.to_list(length=100)

        for order in ready_orders:
            order_id = order.get("order_id", "")
            result = await AutonomousPolicies.check_pickup_reminder(order_id)

            if result.get("action") == "pickup_reminder":
                phone = order.get("customer_phone", "")
                message = result.get("message", "")
                if phone and message:
                    await whatsapp_service.send_message(to=phone, body=message)
                    logger.info("Scheduler: sent pickup_reminder for %s", order_id)

    except Exception as exc:
        logger.error("Scheduler _check_pickup_reminders failed: %s", exc)


def setup_scheduler():
    """Configure all background jobs for the QSR policy engine."""

    # Check payment timeouts every 60 seconds
    scheduler.add_job(
        _check_pending_payments,
        IntervalTrigger(seconds=60),
        id="check_pending_payments",
        replace_existing=True,
    )

    # Check order ready notifications every 5 minutes
    scheduler.add_job(
        _check_order_ready,
        IntervalTrigger(minutes=5),
        id="check_order_ready",
        replace_existing=True,
    )

    # Check pickup reminders every 10 minutes
    scheduler.add_job(
        _check_pickup_reminders,
        IntervalTrigger(minutes=10),
        id="check_pickup_reminders",
        replace_existing=True,
    )

    logger.info("QSR Scheduler configured with 3 background policy jobs")
