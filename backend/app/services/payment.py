"""
Razorpay Payment Integration Service.
"""

import base64
import httpx
from typing import Optional

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.base_url = "https://api.razorpay.com/v1"
        
        if not self.key_id or not self.key_secret:
            logger.warning("Razorpay credentials missing. Payments will fail.")

    async def create_payment_link(self, order_id: str, amount: float, customer_phone: str) -> Optional[str]:
        """
        Produce a Razorpay payment link.
        Amount should be in INR (we convert it to paise here).
        """
        if not self.key_id or not self.key_secret:
            logger.error("Payment requested but Razorpay credentials are not configured.")
            return None

        amount_in_paise = int(amount * 100)
        auth_string = f"{self.key_id}:{self.key_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
        
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "description": f"Order #{order_id}",
            "customer": {
                "contact": customer_phone
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment_links",
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("short_url")
        except Exception as e:
            logger.error("Failed to generate Razorpay payment link: %s", e)
            return None

payment_service = RazorpayService()
