from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class Business(BaseModel):
    business_id: str = Field(..., description="Unique business identifier")
    name: str = Field(..., min_length=1, description="Business name")
    owner_email: EmailStr = Field(..., description="Email address of the owner")
    owner_password: str = Field(..., description="Hashed owner password", exclude=True)
    phone: str = Field(..., description="WhatsApp phone number")
    address: Optional[str] = Field(default=None, description="Physical address")
    timings: Optional[Dict[str, Any]] = Field(default=None, description="Operating hours")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Business settings")
    voice_enabled: bool = Field(default=False, description="Enable voice messages feature")
    voice_type: str = Field(default="en-IN-Wavenet-A", description="Preferred TTS voice model")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
