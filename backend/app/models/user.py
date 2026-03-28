from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class User(BaseModel):
    phone: str = Field(..., description="Phone number of the user")
    email: Optional[str] = Field(default=None, description="Email address, primarily for business owners")
    password_hash: Optional[str] = Field(default=None, description="Hashed password")
    role: str = Field(default="customer", description="Role: 'customer' or 'business_owner'")
    order_history: List[str] = Field(default_factory=list, description="List of order IDs")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    language: str = Field(default="en", description="Preferred language (e.g. 'en', 'hi')")
