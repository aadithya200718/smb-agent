"""
Twilio WhatsApp Integration Service.
Handles interacting with the Twilio API to send WhatsApp messages and validates signatures.
"""

from typing import Dict, Any


from twilio.rest import Client
from twilio.request_validator import RequestValidator

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class WhatsAppService:
    def __init__(self):
        auth_token = settings.TWILIO_AUTH_TOKEN
        account_sid = settings.TWILIO_ACCOUNT_SID
        
        if not auth_token or not account_sid:
            logger.warning("Twilio credentials are not set. WhatsApp service will fail.")
            self.client = None
            self.validator = None
        else:
            # Standard instantiation handles connection pooling.
            self.client = Client(account_sid, auth_token)
            
            # Validator for incoming webhook requests
            self.validator = RequestValidator(auth_token)
            logger.info("WhatsAppService initialized.")

    async def send_message(self, to: str, body: str) -> bool:
        """
        Send a WhatsApp message via Twilio API.
        Automatically formats the phone number to start with 'whatsapp:' if not already.
        """
        if not self.client:
            logger.error("Cannot send message: Twilio client not configured.")
            return False

        to_formatted = self.format_phone_number(to)
        from_formatted = self.format_phone_number(settings.TWILIO_WHATSAPP_NUMBER or "")
        
        if not from_formatted:
            logger.error("Cannot send message: TWILIO_WHATSAPP_NUMBER is not set.")
            return False

        try:
            # the python twilio SDK `messages.create` method is synchronous
            # we can run it in an executor in production to make it truly non-blocking asyncio,
            # but keeping it simple as per instructions.
            message = self.client.messages.create(
                body=body,
                from_=from_formatted,
                to=to_formatted
            )
            logger.info("WhatsApp message sent successfully. SID: %s", message.sid)
            return True
        except Exception as e:
            logger.error("Failed to send WhatsApp message: %s", e)
            return False

    def validate_signature(self, request_url: str, params: Dict[str, Any], signature: str) -> bool:
        """
        Validate the Twilio X-Twilio-Signature against the request contents.
        """
        if not self.validator:
            logger.error("Cannot validate signature: Twilio auth token missing.")
            return False
            
        return self.validator.validate(request_url, params, signature)

    def format_phone_number(self, phone: str) -> str:
        """
        Ensure phone number has 'whatsapp:' prefix for Twilio API.
        """
        if not phone:
            return ""
        if phone.startswith("whatsapp:"):
            return phone
        return f"whatsapp:{phone}"

    async def send_voice_message(self, to: str, media_url: str) -> bool:
        """
        Send a voice message via Twilio using a media URL.

        Args:
            to: Recipient phone number.
            media_url: Public URL to the audio file (OGG format).

        Returns:
            True if sent successfully.
        """
        if not self.client:
            logger.error("Cannot send voice: Twilio client not configured.")
            return False

        to_formatted = self.format_phone_number(to)
        from_formatted = self.format_phone_number(settings.TWILIO_WHATSAPP_NUMBER or "")

        if not from_formatted:
            logger.error("Cannot send voice: TWILIO_WHATSAPP_NUMBER is not set.")
            return False

        try:
            message = self.client.messages.create(
                media_url=[media_url],
                from_=from_formatted,
                to=to_formatted,
            )
            logger.info("Voice message sent. SID: %s", message.sid)
            return True
        except Exception as e:
            logger.error("Failed to send voice message: %s", e)
            return False

    async def send_whatsapp_message(self, phone: str, body: str) -> bool:
        """Convenience alias used by the engagement service."""
        return await self.send_message(to=phone, body=body)

# Singleton instance
whatsapp_service = WhatsAppService()
