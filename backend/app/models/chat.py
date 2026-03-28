from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender: 'user' or 'assistant'")
    content: str = Field(..., description="Text content of the message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_sid: str = Field(..., description="Twilio Message SID to prevent duplicates and track messages")


class Chat(BaseModel):
    chat_id: str = Field(..., description="Unique ID for this chat session")
    business_id: str = Field(..., description="ID of the business")
    customer_phone: str = Field(..., description="Phone number of the customer")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, message: Message) -> None:
        """Add a new message to the chat and update the timestamp."""
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
