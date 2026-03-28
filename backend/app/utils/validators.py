import re
from typing import Dict, Any


def validate_phone_number(phone: str) -> bool:
    """
    Validate that a phone number is in E.164 format and optionally contains the 'whatsapp:' prefix.
    """
    if phone.startswith("whatsapp:"):
        phone = phone.replace("whatsapp:", "")
    # Basic E.164 validation: + followed by 10 to 15 digits
    pattern = re.compile(r"^\+[1-9]\d{10,14}$")
    return bool(pattern.match(phone))


def validate_message_text(text: str) -> bool:
    """
    Validate that the message text is not empty and within reasonable bounds.
    """
    if not text or not text.strip():
        return False
    if len(text) > 4096:  # Standard limit for many messaging platforms
        return False
    return True


def sanitize_input(text: str) -> str:
    """
    Sanitize input text to remove potentially harmful content or excessive whitespaces.
    """
    if not text:
        return ""
    # Strip leading/trailing whitespace and normalise internal whitespace
    sanitized = " ".join(text.split())
    # Add more robust sanitization logic here if needed (e.g. escaping HTML)
    return sanitized


def parse_twilio_webhook(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the twilio webhook form_data into a standardized dictionary.
    """
    return {
        "message_sid": form_data.get("MessageSid", ""),
        "from_phone": form_data.get("From", ""),
        "to_phone": form_data.get("To", ""),
        "body": form_data.get("Body", ""),
        "timestamp": form_data.get("Timestamp", "")
    }
