"""
Agent Tools.

Functions that the AI agent can execute during the 'ACT' node.
Production-ready implementations using MongoDB and Razorpay.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.database import MongoDB
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.services.payment import payment_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_menu(business_id: str) -> List[MenuItem]:
    """
    Fetch the menu for a given business from MongoDB.

    Args:
        business_id: Identifier of the business.

    Returns:
        A list of MenuItem objects.
    """
    logger.info("get_menu: fetching menu for business=%s", business_id)
    try:
        db = MongoDB.get_database()
        cursor = db.menu_items.find(
            {"business_id": business_id, "available": True}
        )
        docs = await cursor.to_list(length=100)

        if not docs:
            logger.warning("get_menu: no items found in DB for %s, using seed data", business_id)
            # Seed data so the agent can still function for demo / first run
            seed = [
                MenuItem(
                    item_id="M1", business_id=business_id,
                    name="Veg Biryani", price=120.0,
                    category="Mains",
                    description="Aromatic basmati rice cooked with mixed vegetables and spices.",
                ),
                MenuItem(
                    item_id="M2", business_id=business_id,
                    name="Paneer Butter Masala", price=150.0,
                    category="Mains",
                    description="Cottage cheese cubes in a rich tomato gravy.",
                ),
                MenuItem(
                    item_id="M3", business_id=business_id,
                    name="Chicken Biryani", price=180.0,
                    category="Mains",
                    description="Fragrant rice layered with tender chicken and spices.",
                ),
                MenuItem(
                    item_id="M4", business_id=business_id,
                    name="Masala Dosa", price=80.0,
                    category="Starters",
                    description="Crispy crepe filled with spiced potato filling.",
                ),
            ]
            # Persist seed data so subsequent calls hit the DB
            await db.menu_items.insert_many([s.model_dump() for s in seed])
            logger.info("get_menu: seeded %d items for business %s", len(seed), business_id)
            return seed

        items = [MenuItem(**doc) for doc in docs]
        logger.info("get_menu: returned %d items for business %s", len(items), business_id)
        return items
    except Exception as e:
        logger.error("get_menu failed: %s", e)
        raise


async def create_order(order_data: Dict[str, Any]) -> Order:
    """
    Create a new order in MongoDB.

    Args:
        order_data: Dictionary containing customer_phone, business_id, and items.

    Returns:
        The created Order object.
    """
    logger.info("create_order: creating order for phone=%s", order_data.get("customer_phone"))
    try:
        db = MongoDB.get_database()

        items: List[OrderItem] = order_data.get("items", [])
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        order = Order(
            order_id=order_id,
            business_id=order_data.get("business_id", ""),
            customer_phone=order_data.get("customer_phone", ""),
            items=items,
        )

        doc = order.model_dump()
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = datetime.now(timezone.utc)
        await db.orders.insert_one(doc)

        logger.info("create_order: created order %s, total=%.2f", order.order_id, order.total)
        return order
    except Exception as e:
        logger.error("create_order failed: %s", e)
        raise




async def generate_payment_link(order_id: str, amount: float, customer_phone: str = "") -> str:
    """
    Generate a payment link for the order via Razorpay.

    Falls back to a mock URL if Razorpay credentials are not configured.

    Args:
        order_id: The order identifier.
        amount:   The total amount to pay.
        customer_phone: Customer phone for the payment link.

    Returns:
        A URL pointing to the payment gateway.
    """
    logger.info("generate_payment_link: order=%s, amount=%.2f", order_id, amount)
    try:
        link = await payment_service.create_payment_link(
            order_id=order_id,
            amount=amount,
            customer_phone=customer_phone or "+910000000000",
        )
        if link:
            logger.info("generate_payment_link: Razorpay link created: %s", link)
            return link

        # Fallback when Razorpay credentials aren't configured
        fallback = f"https://pay.business.app/order/{order_id}?amount={amount}"
        logger.warning("generate_payment_link: Razorpay unavailable, using fallback URL")
        return fallback
    except Exception as e:
        logger.error("generate_payment_link failed: %s", e)
        fallback = f"https://pay.business.app/order/{order_id}?amount={amount}"
        return fallback
