"""
Proactive Engagement Event Model (Feature 4).
"""
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class EngagementEvent(BaseModel):
    event_id: str
    user_phone: str
    business_id: str
    event_type: str  # "reengagement", "order_update", "announcement"
    message: str
    metadata: Dict
    sent_at: datetime
    delivered: bool = False
    read: bool = False
    responded: bool = False
    response_text: Optional[str] = None
    response_at: Optional[datetime] = None
