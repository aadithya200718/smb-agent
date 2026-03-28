"""
Order data models.

Defines the schema for customer orders and individual order items.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    """Lifecycle stages of an order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """An individual item comprising part of an order."""

    item_id: str = Field(..., description="Unique identifier for the menu item")
    name: str = Field(..., description="Snapshot of the item name at time of order")
    quantity: int = Field(..., gt=0, description="Number of portions requested")
    unit_price: float = Field(..., ge=0, description="Price per unit at time of order")
    notes: Optional[str] = Field(None, description="Special instructions (e.g., 'no onions')")

    @property
    def subtotal(self) -> float:
        """Calculate the total cost for this line item."""
        return self.quantity * self.unit_price


class Order(BaseModel):
    """
    Represents a complete customer order.
    """

    model_config = ConfigDict(populate_by_name=True)

    order_id: str = Field(..., description="Unique identifier for the order")
    business_id: str = Field(..., description="Identifier of the business")
    customer_phone: str = Field(..., description="Customer's WhatsApp number")
    items: List[OrderItem] = Field(default_factory=list, description="List of ordered items")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Current order state")
    payment_link: Optional[str] = Field(None, description="URL for the customer to pay")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the order was created",
    )

    @property
    def total(self) -> float:
        """Calculate the overall total across all items."""
        return sum(item.subtotal for item in self.items)
