"""
Menu data models.

Defines the schema for menu items offered by businesses.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MenuItem(BaseModel):
    """
    Represents a single item on a business's menu.
    """

    model_config = ConfigDict(populate_by_name=True)

    item_id: str = Field(..., description="Unique identifier for the item")
    business_id: str = Field(..., description="Identifier for the business offering this item")
    name: str = Field(..., min_length=1, description="Name of the dish or product")
    hindi_name: Optional[str] = Field(None, description="Hindi translation of the item name")
    price: float = Field(..., ge=0, description="Price of the item in INR")
    category: str = Field(..., description="E.g., Starters, Mains, Desserts, Services")
    available: bool = Field(default=True, description="Whether the item is currently in stock")
    description: Optional[str] = Field(None, description="Detailed description of the item")
