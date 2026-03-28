"""
Availability Validators.

Checks stock, timings, and zones.
"""
from typing import Dict, List, Any
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AvailabilityValidator:
    
    @staticmethod
    def is_restaurant_open() -> bool:
        """Verify the restaurant is within business hours (10 AM - 10 PM IST)."""
        # Note: simplistic hour check for demonstration
        h = datetime.utcnow().hour + 5.5 # rough IST
        hour_ist = int(h) % 24
        is_open = 10 <= hour_ist < 22
        if not is_open:
            logger.warning("Availability failure: Restaurant is closed.")
        return is_open
        
    @staticmethod
    async def validate_stock(items: List[Dict[str, Any]]) -> bool:
        """
        Verify that requested items do not exceed current POS stock bounds.
        Opus to connect this with Petpooja real stock.
        """
        # Stub passing everything for now
        return True
